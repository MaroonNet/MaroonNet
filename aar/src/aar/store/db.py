"""Open, create, and fill a mission store.

The schema is the C-01 draft in schema.sql (AAR Architecture v1.0 section 6). These helpers are
the write path a bridge daemon would call: one packet row per received packet, then one typed
row (position, telemetry) that points back at it. Nothing here updates a row in place; whether
the store is insert-only is still open (section 5.1), but the draft keeps that door open.
"""

from __future__ import annotations

import json
import sqlite3
from importlib import resources
from pathlib import Path

# Bumped when schema.sql changes shape. Stored in mission.schema_ver so a reader can tell.
SCHEMA_VERSION = "0.1-draft"


def schema_sql() -> str:
    """Return the DDL text of the C-01 draft."""
    return resources.files("aar.store").joinpath("schema.sql").read_text(encoding="utf-8")


def connect(path: str | Path) -> sqlite3.Connection:
    """Open an existing mission store. Rows come back as sqlite3.Row (dict-like)."""
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def create(path: str | Path, mission_id: str, name: str, started_at: str) -> sqlite3.Connection:
    """Create a new mission store and its mission row.

    Refuses to touch a file that already exists: a mission store is never overwritten.
    """
    p = Path(path)
    if p.exists():
        raise FileExistsError(f"mission store already exists: {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    con = connect(p)
    con.executescript(schema_sql())
    con.execute(
        "INSERT INTO mission (mission_id, name, started_at, schema_ver) VALUES (?, ?, ?, ?)",
        (mission_id, name, started_at, SCHEMA_VERSION),
    )
    con.commit()
    return con


def ensure_node(
    con: sqlite3.Connection,
    node_num: int,
    first_seen: str,
    long_name: str | None = None,
    short_name: str | None = None,
    hw_model: str | None = None,
) -> None:
    """Insert the node row if this is the first time the radio is heard. Never updates it."""
    con.execute(
        "INSERT OR IGNORE INTO node (node_num, long_name, short_name, hw_model, first_seen)"
        " VALUES (?, ?, ?, ?, ?)",
        (node_num, long_name, short_name, hw_model, first_seen),
    )


def insert_packet(
    con: sqlite3.Connection,
    *,
    rx_time: str,
    from_node: int,
    portnum: str,
    to_node: int | None = None,
    mesh_id: int | None = None,
    hop_start: int | None = None,
    hop_limit: int | None = None,
    relay_node: int | None = None,
    rx_snr: float | None = None,
    rx_rssi: int | None = None,
    want_ack: bool | None = None,
    raw: bytes | None = None,
    decoded: dict | None = None,
) -> int:
    """Append one row to the raw packet log and return its packet_id (the insert order)."""
    cur = con.execute(
        "INSERT INTO packet (rx_time, from_node, to_node, mesh_id, portnum, hop_start, hop_limit,"
        " relay_node, rx_snr, rx_rssi, want_ack, raw, decoded)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            rx_time,
            from_node,
            to_node,
            mesh_id,
            portnum,
            hop_start,
            hop_limit,
            relay_node,
            rx_snr,
            rx_rssi,
            None if want_ack is None else int(want_ack),
            raw,
            None if decoded is None else json.dumps(decoded),
        ),
    )
    return int(cur.lastrowid)


def insert_position(
    con: sqlite3.Connection,
    packet_id: int,
    node_num: int,
    device_time: str | None,
    rx_time: str,
    lat: float,
    lon: float,
    alt_m: float | None = None,
    precision_bits: int | None = None,
) -> None:
    """Append the typed position row for a position packet. device_time is None when the radio
    reported no usable GPS time (open item A-03)."""
    con.execute(
        "INSERT INTO position (packet_id, node_num, device_time, rx_time, lat, lon, alt_m,"
        " precision_bits) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (packet_id, node_num, device_time, rx_time, lat, lon, alt_m, precision_bits),
    )


def insert_telemetry(
    con: sqlite3.Connection,
    packet_id: int,
    node_num: int,
    rx_time: str,
    battery_pct: float | None = None,
    voltage: float | None = None,
    channel_util: float | None = None,
    air_util_tx: float | None = None,
) -> None:
    """Append the typed telemetry row for a telemetry packet."""
    con.execute(
        "INSERT INTO telemetry (packet_id, node_num, rx_time, battery_pct, voltage, channel_util,"
        " air_util_tx) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (packet_id, node_num, rx_time, battery_pct, voltage, channel_util, air_util_tx),
    )


def insert_event(
    con: sqlite3.Connection,
    event_time: str,
    event_type: str,
    node_num: int | None = None,
    sector_id: str | None = None,
    payload: dict | None = None,
) -> int:
    """Append one timeline event (types in AAR Architecture v1.0 section 6.3). Returns event_id."""
    cur = con.execute(
        "INSERT INTO event (event_time, event_type, node_num, sector_id, payload)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            event_time,
            event_type,
            node_num,
            sector_id,
            None if payload is None else json.dumps(payload),
        ),
    )
    return int(cur.lastrowid)
