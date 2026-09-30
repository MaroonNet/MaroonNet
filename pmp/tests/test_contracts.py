"""The contract drafts round-trip through dict and JSON, and refuse what they should."""

from __future__ import annotations

import pytest

from pmp.contract.events import EVENT_TYPES, PMP_WRITES, Event, OverridePayload
from pmp.contract.messages import KINDS, MESSAGE_SCHEMA, DaemonMessage
from pmp.contract.mission_input import INPUT_SCHEMA, LatLon, MissionInput
from pmp.maps.package import LAYER_KINDS, TerrainLayer, TerrainPackage

T0 = "2026-10-03T14:00:05Z"


def test_daemon_message_round_trip() -> None:
    m = DaemonMessage("position", T0, 7, {"node_num": 1, "lat": 39.99, "lon": -105.28})
    assert DaemonMessage.from_json(m.to_json()) == m
    assert m.to_dict()["schema"] == MESSAGE_SCHEMA


def test_daemon_message_refuses_unknown_kind_and_schema() -> None:
    with pytest.raises(ValueError):
        DaemonMessage("heartbeat", T0, 1)
    with pytest.raises(ValueError):
        DaemonMessage("position", T0, 1, schema="pmp.daemon_message/9.9")


def test_message_kinds_match_the_architecture_table() -> None:
    assert KINDS == (
        "node_seen",
        "position",
        "telemetry",
        "message",
        "quiet_node",
        "gap",
        "mission",
    )


def test_mission_input_known_position_round_trip() -> None:
    mi = MissionInput(
        mission_id="m1",
        entered_at=T0,
        no_known_position=False,
        elapsed_h=3.5,
        subject_category="hiker",
        team_size=6,
        lkp=LatLon(40.35, -105.68),
        lkp_time="2026-10-03T10:30:00Z",
        lkp_kind="pls",
        subject_identifiers=("group",),
        radio_count=6,
    )
    back = MissionInput.from_json(mi.to_json())
    assert back == mi
    assert back.lkp == LatLon(40.35, -105.68)
    assert back.to_dict()["schema"] == INPUT_SCHEMA


def test_mission_input_no_known_position_case() -> None:
    mi = MissionInput("m2", T0, True, 12.0, None, 4)
    assert MissionInput.from_dict(mi.to_dict()) == mi
    assert mi.lkp is None


def test_mission_input_refuses_inconsistent_position_flags() -> None:
    with pytest.raises(ValueError):
        MissionInput("m3", T0, True, 1.0, None, 4, lkp=LatLon(0.0, 0.0))
    with pytest.raises(ValueError):
        MissionInput("m4", T0, False, 1.0, None, 4)
    with pytest.raises(ValueError):
        MissionInput("m5", T0, True, 1.0, None, 4, subject_identifiers=("alien",))
    with pytest.raises(ValueError):
        MissionInput("m6", T0, True, 1.0, None, 4, lkp_kind="guess")
    with pytest.raises(ValueError):
        MissionInput("m7", T0, True, None, None, 4)  # no position and no elapsed time


def test_event_round_trip_and_types() -> None:
    e = Event(
        "override", T0, sector_id="S1", payload=OverridePayload({"a": 1}, {"a": 2}, "why").to_dict()
    )
    assert Event.from_json(e.to_json()) == e
    assert e.payload["reason"] == "why"
    assert set(PMP_WRITES) <= set(EVENT_TYPES)
    with pytest.raises(ValueError):
        Event("alarm", T0)


def test_terrain_package_round_trip() -> None:
    layer = TerrainLayer("elevation", "dem_10m.tif", "geotiff", "USGS 3DEP", T0, resolution_m=10.0)
    pkg = TerrainPackage(
        "rmnp-test", (-105.9, 40.2, -105.5, 40.5), "EPSG:32613", 25.0, (layer,), T0
    )
    back = TerrainPackage.from_json(pkg.to_json())
    assert back == pkg
    assert back.layers[0].kind in LAYER_KINDS
    with pytest.raises(ValueError):
        TerrainLayer("clouds", "x", "geotiff", "nowhere", T0)
    with pytest.raises(ValueError):
        TerrainPackage("bad", (0.0, 0.0, 1.0), "EPSG:32613", 25.0)  # type: ignore[arg-type]
