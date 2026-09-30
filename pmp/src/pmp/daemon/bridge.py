"""The bridge: receive one radio record, write its rows, push its message.

(P)MP Architecture v1.0 section 5. The daemon owns step 7 of MCM Architecture v1.0 section 4.1: it
creates the ``Gateway``, passes ``on_record`` as the callback, and owns the process, the thread,
and the store. MCM owns steps 1 to 5 and guarantees what arrives (MCM Architecture v1.0
section 4.6). Whether the daemon accepts this split is Open (MCM Architecture v1.0 section 10
question 9); this stub is written against it so the question can be answered with code.

Rules the bridge keeps:

- It imports nothing from ``mcm`` or ``aar`` at runtime. It takes the record as a mapping
  (``as_mapping``) and reads fields by name, and it writes through store helpers handed to it, so
  the synthetic feed (JSON Lines) and a live ``RadioRecord`` look the same to the write path.
- It inserts; it never updates (AAR Architecture v1.0 section 5.1, shapes a and b).
- It adds nothing to a record: no interpolated position, no filled-in time, no re-stamped clock.
  The host receive time is ``rx_time_host``, set by the ``Gateway`` at step 5 and proposed as
  C-01 ``rx_time`` (MCM Architecture v1.0 section 4.4; open there as section 10 question 10).
- A record whose schema string it does not know is logged and skipped, never written.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from typing import Any

from pmp.contract.messages import DaemonMessage

log = logging.getLogger(__name__)

# The M-01 schema string the bridge knows how to map (mcm/src/mcm/contract/record.py).
ACCEPTED_RECORD_SCHEMAS = ("mcm.radio_record/0.1-draft",)


def as_mapping(record: Any) -> dict[str, Any]:
    """The record as a plain dict: a dataclass through ``asdict``, anything else through ``dict``.

    A live ``RadioRecord`` is a frozen dataclass; a synthetic or captured record is already a dict
    from JSON Lines. Both come out the same shape, so the rest of the bridge reads by name.
    """
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    return dict(record)


def row_from_record(record: Any) -> dict[str, Any]:
    """Map one ``RadioRecord`` to the C-01 draft columns, by name.

    MCM chose its field names to match the C-01 draft (MCM Architecture v1.0 section 4.3), so the
    mapping is mostly a rename of nested fields to flat columns: ``header.from_node`` ->
    ``from_node``, ``position.device_time`` -> ``device_time``, and so on. Fields with no C-01
    column today go to the ``decoded`` JSON column (M-02, Open).
    """
    raise NotImplementedError(
        "C-01 mapping; waits on M-01 signed and the store meeting (R-01, R-04)"
    )


class Bridge:
    """Receives radio records, writes C-01 rows, and pushes C-02 messages.

    ``store`` is an object with the AAR's insert helpers (``ensure_node``, ``insert_packet``,
    ``insert_position``, ``insert_telemetry``, ``insert_event``); ``push`` takes one
    ``DaemonMessage``. Both are handed in so the bridge depends on neither package.
    """

    def __init__(
        self,
        store: Any,
        push: Callable[[DaemonMessage], None],
        *,
        quiet_watch: Any | None = None,
    ) -> None:
        self.store = store
        self.push = push
        self.quiet_watch = quiet_watch  # MCM's QuietNodeWatch, if the team keeps it in the daemon
        self.seq = 0

    def on_record(self, record: Any) -> None:
        """The M-01 callback: one record in, its rows written, its message pushed.

        Called by MCM's ``Gateway`` for every packet, in order. Must not raise into the gateway;
        the gateway logs and carries on either way (MCM Architecture v1.0 section 4.6, rule 5).
        """
        raise NotImplementedError("daemon intake; waits on M-01 acceptance (section 5.2)")

    async def run(self, gateway: Any) -> None:
        """Open the gateway, serve records until stopped, close the gateway.

        Under PM-01 shape (a) this is an asyncio task in the API's event loop. Under shape (b) it is
        the body of ``pmp daemon``. The stub does not choose.
        """
        raise NotImplementedError("daemon loop; waits on PM-01 (section 4)")

    def stop(self) -> None:
        """Ask ``run`` to close the gateway and return."""
        raise NotImplementedError("daemon loop; waits on PM-01 (section 4)")

    def on_quiet(self, node_num: int, last_heard: str, silent_s: float) -> None:
        """A radio passed the quiet threshold by the host clock: push ``quiet_node`` (C-02)."""
        raise NotImplementedError("quiet-node alert; waits on A-02 and C-02")
