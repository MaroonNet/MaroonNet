"""The C-01 draft loads, refuses to overwrite, and round-trips a packet with its typed row."""

import json

import pytest
from aar.store import SCHEMA_VERSION, connect, create, insert_packet, insert_position, schema_sql

TABLES = {
    "mission",
    "node",
    "packet",
    "position",
    "telemetry",
    "message",
    "event",
    "sector",
    "artifact",
}


def test_create_makes_every_table(tmp_path):
    con = create(tmp_path / "m.sqlite", "m-001", "test", "2026-10-03T14:00:00Z")
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert TABLES <= names
    m = con.execute("SELECT * FROM mission").fetchone()
    assert (
        m["mission_id"] == "m-001" and m["schema_ver"] == SCHEMA_VERSION and m["ended_at"] is None
    )


def test_create_never_overwrites(tmp_path):
    path = tmp_path / "m.sqlite"
    create(path, "m-001", "test", "2026-10-03T14:00:00Z").close()
    with pytest.raises(FileExistsError):
        create(path, "m-002", "again", "2026-10-03T15:00:00Z")


def test_schema_carries_every_mcm_packet_field():
    """MCM v1.1 section 3.2 lists the fields the daemon must log from day one."""
    ddl = schema_sql()
    for field in (
        "hop_start",
        "hop_limit",
        "relay_node",
        "rx_snr",
        "rx_rssi",
        "precision_bits",
        "battery_pct",
        "voltage",
        "channel_util",
        "air_util_tx",
        "device_time",
        "rx_time",
    ):
        assert field in ddl


def test_packet_and_position_round_trip(tmp_path):
    con = create(tmp_path / "m.sqlite", "m-001", "test", "2026-10-03T14:00:00Z")
    pid = insert_packet(
        con,
        rx_time="2026-10-03T14:00:09Z",
        from_node=0x10000001,
        portnum="POSITION_APP",
        hop_start=3,
        hop_limit=2,
        relay_node=0x10000002,
        rx_snr=6.5,
        rx_rssi=-90,
        want_ack=False,
        raw=b"\x01\x02",
        decoded={"latitude": 40.39, "longitude": -105.6},
    )
    insert_position(
        con,
        pid,
        0x10000001,
        "2026-10-03T14:00:00Z",
        "2026-10-03T14:00:09Z",
        40.39,
        -105.6,
        2800.0,
        32,
    )
    con.commit()
    con.close()

    con = connect(tmp_path / "m.sqlite")
    p = con.execute("SELECT * FROM packet").fetchone()
    assert p["packet_id"] == pid and p["want_ack"] == 0 and p["raw"] == b"\x01\x02"
    assert json.loads(p["decoded"])["latitude"] == 40.39
    pos = con.execute("SELECT * FROM position WHERE packet_id = ?", (pid,)).fetchone()
    assert (pos["node_num"], pos["device_time"], pos["rx_time"]) == (
        0x10000001,
        "2026-10-03T14:00:00Z",
        "2026-10-03T14:00:09Z",
    )


def test_position_needs_its_packet_row(tmp_path):
    """A typed row without a packet row would be a datapoint with no provenance."""
    import sqlite3

    con = create(tmp_path / "m.sqlite", "m-001", "test", "2026-10-03T14:00:00Z")
    with pytest.raises(sqlite3.IntegrityError):
        insert_position(
            con, 999, 0x10000001, "2026-10-03T14:00:00Z", "2026-10-03T14:00:09Z", 40.39, -105.6
        )
