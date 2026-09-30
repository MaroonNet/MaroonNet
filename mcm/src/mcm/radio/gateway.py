"""The gateway: the radio the command post listens through, and the hand-off to the daemon.

Who calls whom (MCM Architecture v1.0 section 4.1): the (P)MP bridge daemon owns the process and
the mission store. It creates a Gateway, passes a callback, and receives one RadioRecord per packet
the gateway radio hears. MCM never writes to the store.

    gw = Gateway(on_record=daemon.handle_record)
    gw.open()            # USB serial by default; the port comes from the radio profile
    ...
    gw.send_text("Return to CP", channel=0)
    gw.close()

The meshtastic library is imported only inside open(), so the rest of the package (and the tests)
run without it or a radio. Install it with `pip install -e ".[radio]"`.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from mcm.contract.record import RadioRecord
from mcm.messages.catalog import check_text
from mcm.radio.normalize import normalize, now_iso
from mcm.radio.profile import RadioProfile, check_firmware, load

log = logging.getLogger(__name__)

RecordHandler = Callable[[RadioRecord], None]


class Gateway:
    """Owns the connection to one gateway radio and numbers every packet it hears."""

    def __init__(self, on_record: RecordHandler, profile: RadioProfile | None = None) -> None:
        self.on_record = on_record
        self.profile = profile or load()
        self._iface: Any = None
        self._seq = 0
        self._lock = threading.Lock()
        self.gateway_node: int | None = None

    # -- inbound ---------------------------------------------------------------------------

    def handle_packet(self, packet: dict[str, Any], interface: Any = None) -> RadioRecord:
        """Normalize one library packet and hand it on. Also the entry point for replays.

        The record is built and handed on even if the handler raises, so a daemon bug never
        silently drops a packet; the error is logged with the packet's sequence number.
        """
        with self._lock:
            self._seq += 1
            seq = self._seq
        rec = normalize(packet, seq=seq, rx_time_host=now_iso(), gateway_node=self.gateway_node)
        try:
            self.on_record(rec)
        except Exception:  # noqa: BLE001 - the daemon's failure must not stop the radio feed
            log.exception("record handler failed on seq %d", seq)
        return rec

    def open(self) -> None:
        """Connect to the gateway radio over the transport in the profile (serial for now)."""
        if self.profile.transport != "serial":
            raise NotImplementedError(
                f"transport {self.profile.transport!r}: only serial exists (MCM v1.1 section 6.2)"
            )
        try:
            import meshtastic.serial_interface  # noqa: PLC0415 - optional dependency
            from pubsub import pub  # noqa: PLC0415 - installed with meshtastic
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise RuntimeError('install the radio extra: pip install -e ".[radio]"') from exc

        pub.subscribe(self.handle_packet, "meshtastic.receive")
        self._iface = meshtastic.serial_interface.SerialInterface(devPath=self.profile.port or None)
        info = getattr(self._iface, "myInfo", None)
        self.gateway_node = getattr(info, "my_node_num", None)
        meta = getattr(self._iface, "metadata", None)
        problem = check_firmware(self.profile, getattr(meta, "firmware_version", None))
        if problem:
            log.warning(problem)
        log.info("gateway open: node %s", self.gateway_node)

    def close(self) -> None:
        if self._iface is not None:
            self._iface.close()
            self._iface = None

    # -- outbound (from (P)MP, through the daemon) ------------------------------------------

    def send_text(self, text: str, *, channel: int = 0, dest: int | str = "^all") -> None:
        """Send a text on the mesh. Refuses text that does not fit one packet."""
        problem = check_text(text)
        if problem:
            raise ValueError(problem)
        if self._iface is None:
            raise RuntimeError("gateway is not open")
        self._iface.sendText(text, destinationId=dest, channelIndex=channel)
