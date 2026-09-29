"""Turn a packet dict from the Meshtastic Python library into a RadioRecord.

The library delivers each received packet on the pubsub topic "meshtastic.receive" as a dict built
from the MeshPacket protobuf: camelCase keys ("rxSnr", "hopStart"), with a "decoded" sub-dict when
the gateway could decrypt it. This module is the one place that knows those key names. If the
pinned firmware or library renames a field, this file and its tests change; nothing downstream does.

The key names here follow the protobuf field names (mesh.proto, telemetry.proto). They are checked
against hand-built fixtures, not yet against a real capture. Replace the fixtures with a capture
from the pinned firmware before C-01 is signed (MCM Architecture v1.0 section 11, phase 1).
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

from mcm.contract.record import (
    NodeInfo,
    PacketHeader,
    PositionFix,
    RadioRecord,
    TelemetrySample,
)

_KIND_BY_PORT = {
    "POSITION_APP": "position",
    "TELEMETRY_APP": "telemetry",
    "TEXT_MESSAGE_APP": "text",
    "NODEINFO_APP": "node_info",
    "WAYPOINT_APP": "waypoint",
}

# Decoded keys this module maps into typed fields. Everything else goes to decoded_extra.
_MAPPED_DECODED = {"portnum", "payload", "position", "telemetry", "text", "user", "raw"}


def epoch_to_iso(seconds: int | float | None) -> str | None:
    """Epoch seconds to UTC ISO-8601 with a Z. 0 or None means the radio had no time: None."""
    if not seconds:
        return None
    return datetime.fromtimestamp(float(seconds), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_iso() -> str:
    """The command post clock, UTC, ISO-8601 with a Z."""
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _json_safe(value: Any) -> Any:
    """Make a decoded value JSON-safe: bytes to base64, protobuf objects dropped to their str."""
    if isinstance(value, bytes | bytearray):
        return {"b64": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items() if k != "raw"}
    if isinstance(value, list | tuple):
        return [_json_safe(v) for v in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def _raw_b64(packet: dict[str, Any]) -> str | None:
    raw = packet.get("raw")
    if raw is None:
        return None
    if isinstance(raw, bytes | bytearray):
        return base64.b64encode(bytes(raw)).decode("ascii")
    serialize = getattr(raw, "SerializeToString", None)
    if callable(serialize):
        return base64.b64encode(serialize()).decode("ascii")
    return None


def _position(p: dict[str, Any]) -> PositionFix | None:
    lat = p.get("latitude")
    lon = p.get("longitude")
    if lat is None and "latitudeI" in p:
        lat = p["latitudeI"] * 1e-7
    if lon is None and "longitudeI" in p:
        lon = p["longitudeI"] * 1e-7
    if lat is None or lon is None:
        return None  # a position packet with no coordinates: kept as a record, no fix
    return PositionFix(
        lat=float(lat),
        lon=float(lon),
        alt_m=float(p["altitude"]) if p.get("altitude") is not None else None,
        device_time=epoch_to_iso(p.get("time")),
        precision_bits=p.get("precisionBits"),
        sats_in_view=p.get("satsInView"),
        pdop=(p["PDOP"] / 100.0) if p.get("PDOP") is not None else None,  # firmware sends x100
    )


def _telemetry(t: dict[str, Any]) -> TelemetrySample | None:
    dm = t.get("deviceMetrics")
    if not dm:
        return None  # environment or power telemetry: kept in decoded_extra
    return TelemetrySample(
        battery_pct=dm.get("batteryLevel"),
        voltage=dm.get("voltage"),
        channel_util=dm.get("channelUtilization"),
        air_util_tx=dm.get("airUtilTx"),
        uptime_s=dm.get("uptimeSeconds"),
        device_time=epoch_to_iso(t.get("time")),
    )


def _node_info(u: dict[str, Any]) -> NodeInfo:
    return NodeInfo(
        node_id=u.get("id"),
        long_name=u.get("longName"),
        short_name=u.get("shortName"),
        hw_model=u.get("hwModel"),
    )


def normalize(
    packet: dict[str, Any],
    *,
    seq: int,
    rx_time_host: str | None = None,
    gateway_node: int | None = None,
) -> RadioRecord:
    """Normalize one library packet dict. Never raises on a missing optional field."""
    header = PacketHeader(
        from_node=int(packet["from"]),
        to_node=packet.get("to"),
        mesh_id=packet.get("id"),
        channel=packet.get("channel"),
        hop_start=packet.get("hopStart"),
        hop_limit=packet.get("hopLimit"),
        relay_node=packet.get("relayNode"),
        rx_snr=packet.get("rxSnr"),
        rx_rssi=packet.get("rxRssi"),
        want_ack=packet.get("wantAck"),
        via_mqtt=packet.get("viaMqtt"),
    )
    decoded = packet.get("decoded")
    common = {
        "seq": seq,
        "rx_time_host": rx_time_host or now_iso(),
        "rx_time_radio": epoch_to_iso(packet.get("rxTime")),
        "gateway_node": gateway_node,
        "header": header,
        "raw_b64": _raw_b64(packet),
    }
    if not decoded:
        return RadioRecord(portnum="UNKNOWN", kind="undecoded", **common)

    portnum = str(decoded.get("portnum", "UNKNOWN"))
    kind = _KIND_BY_PORT.get(portnum, "other")
    extra = {k: _json_safe(v) for k, v in decoded.items() if k not in _MAPPED_DECODED}
    if kind == "other" and "payload" in decoded:
        extra["payload"] = _json_safe(decoded["payload"])
    if kind == "waypoint" and "waypoint" in decoded:
        extra["waypoint"] = _json_safe(decoded["waypoint"])

    position = _position(decoded.get("position") or {}) if kind == "position" else None
    telemetry = _telemetry(decoded.get("telemetry") or {}) if kind == "telemetry" else None
    if kind == "telemetry" and telemetry is None and decoded.get("telemetry"):
        extra["telemetry"] = _json_safe(decoded["telemetry"])

    user = decoded.get("user") if kind == "node_info" else None
    return RadioRecord(
        portnum=portnum,
        kind=kind,
        position=position,
        telemetry=telemetry,
        text=decoded.get("text") if kind == "text" else None,
        node_info=_node_info(user) if user else None,
        decoded_extra=extra,
        **common,
    )
