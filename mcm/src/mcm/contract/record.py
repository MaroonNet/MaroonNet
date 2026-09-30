"""The radio record: what MCM hands to the bridge daemon for every packet the gateway hears.

This is MCM's side of the data contract (MCM Architecture v1.0 section 4, item M-01). It does not
define the mission store (C-01, AAR) or the daemon's screen messages (C-02, (P)MP). Field names
follow the C-01 draft columns where one exists, so the daemon can map a record to a row by name.

Rules the record keeps:

- One record per received packet, including packets the gateway could not decrypt.
- Every header field is carried, even when empty. Nothing is dropped, nothing is filled in.
- Times are UTC ISO-8601 strings ending in "Z". Coordinates are WGS84 decimal degrees.
- A missing value is None, never 0: a radio with no GPS fix reports no device time.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TextIO

# Bumped when the record shape changes. Written into every record so a reader can tell.
RECORD_SCHEMA = "mcm.radio_record/0.1-draft"

KINDS = ("position", "telemetry", "text", "node_info", "waypoint", "other", "undecoded")


@dataclass(frozen=True)
class PacketHeader:
    """MeshPacket header fields, as the gateway radio reports them."""

    from_node: int
    to_node: int | None = None
    mesh_id: int | None = None  # packet id from the header
    channel: int | None = None
    hop_start: int | None = None
    hop_limit: int | None = None
    relay_node: int | None = None  # firmware reports only the low byte of the relaying node
    rx_snr: float | None = None  # of the LAST hop into the gateway, not of the origin
    rx_rssi: int | None = None  # same: last hop only
    want_ack: bool | None = None
    via_mqtt: bool | None = None

    @property
    def hops_taken(self) -> int | None:
        """Hops the packet travelled before the gateway heard it. 0 means heard directly."""
        if self.hop_start is None or self.hop_limit is None:
            return None
        return self.hop_start - self.hop_limit

    @property
    def heard_directly(self) -> bool | None:
        """True when SNR and RSSI describe the origin node's own link to the gateway."""
        hops = self.hops_taken
        return None if hops is None else hops == 0


@dataclass(frozen=True)
class PositionFix:
    """Decoded POSITION_APP payload."""

    lat: float
    lon: float
    alt_m: float | None = None
    device_time: str | None = None  # the radio's GPS time; None when it reports none
    precision_bits: int | None = None
    sats_in_view: int | None = None
    pdop: float | None = None


@dataclass(frozen=True)
class TelemetrySample:
    """Decoded TELEMETRY_APP device metrics."""

    battery_pct: float | None = None
    voltage: float | None = None
    channel_util: float | None = None
    air_util_tx: float | None = None
    uptime_s: int | None = None
    device_time: str | None = None


@dataclass(frozen=True)
class NodeInfo:
    """Decoded NODEINFO_APP user record."""

    node_id: str | None = None  # "!a1b2c3d4"
    long_name: str | None = None
    short_name: str | None = None
    hw_model: str | None = None


@dataclass(frozen=True)
class RadioRecord:
    """One packet heard by the gateway, normalized. The unit MCM hands to the daemon."""

    seq: int  # per-gateway-session counter; total order independent of any clock
    rx_time_host: str  # command post clock at receipt (the laptop)
    header: PacketHeader
    portnum: str  # POSITION_APP, TELEMETRY_APP, TEXT_MESSAGE_APP, ... or "UNKNOWN"
    kind: str  # one of KINDS
    rx_time_radio: str | None = None  # gateway radio's clock at receipt; unreliable without GPS
    gateway_node: int | None = None
    position: PositionFix | None = None
    telemetry: TelemetrySample | None = None
    text: str | None = None
    node_info: NodeInfo | None = None
    decoded_extra: dict[str, Any] = field(default_factory=dict)  # every other decoded field
    raw_b64: str | None = None  # serialized MeshPacket, base64; the untouched original
    schema: str = RECORD_SCHEMA

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown record kind: {self.kind!r}")

    def to_dict(self) -> dict[str, Any]:
        """Plain dict, JSON-safe."""
        return asdict(self)

    def to_json(self) -> str:
        """One line of JSON, keys sorted, no trailing newline."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RadioRecord:
        """Rebuild a record from to_dict() output. Refuses a different schema string."""
        schema = d.get("schema", RECORD_SCHEMA)
        if schema != RECORD_SCHEMA:
            raise ValueError(f"record schema {schema!r} is not {RECORD_SCHEMA!r}")
        return cls(
            seq=d["seq"],
            rx_time_host=d["rx_time_host"],
            header=PacketHeader(**d["header"]),
            portnum=d["portnum"],
            kind=d["kind"],
            rx_time_radio=d.get("rx_time_radio"),
            gateway_node=d.get("gateway_node"),
            position=PositionFix(**d["position"]) if d.get("position") else None,
            telemetry=TelemetrySample(**d["telemetry"]) if d.get("telemetry") else None,
            text=d.get("text"),
            node_info=NodeInfo(**d["node_info"]) if d.get("node_info") else None,
            decoded_extra=d.get("decoded_extra") or {},
            raw_b64=d.get("raw_b64"),
            schema=schema,
        )

    @classmethod
    def from_json(cls, line: str) -> RadioRecord:
        return cls.from_dict(json.loads(line))


def write_jsonl(records: Iterable[RadioRecord], out: TextIO) -> int:
    """Write records as JSON Lines. Returns the count written."""
    n = 0
    for rec in records:
        out.write(rec.to_json())
        out.write("\n")
        n += 1
    return n


def read_jsonl(path: str | Path) -> Iterator[RadioRecord]:
    """Yield records from a JSON Lines capture file, skipping blank lines."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield RadioRecord.from_json(line)
