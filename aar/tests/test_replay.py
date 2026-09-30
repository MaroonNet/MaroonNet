"""Q-01 to Q-05 against a small hand-built mission with known answers."""

import pytest
from aar.replay import (
    events_until,
    gaps,
    positions_between,
    positions_without_fix,
    state_at,
    trails_until,
)
from aar.store import create, insert_event, insert_packet, insert_position

A, B = 0x10000001, 0x10000002


def t(hhmm: str) -> str:
    return f"2026-10-03T{hhmm}:00Z"


@pytest.fixture
def store(tmp_path):
    """Two searchers. A reports every 10 minutes. B reports, goes quiet for 40 minutes, returns.
    One of A's reports has no device time."""
    con = create(tmp_path / "m.sqlite", "m-001", "test", t("14:00"))

    def pos(node, device, rx, lat):
        pid = insert_packet(con, rx_time=rx, from_node=node, portnum="POSITION_APP")
        insert_position(con, pid, node, device, rx, lat, -105.6)

    pos(A, t("14:00"), t("14:00"), 40.000)
    pos(A, t("14:10"), t("14:10"), 40.010)
    pos(A, None, t("14:15"), 40.015)  # no GPS fix: no device time
    pos(A, t("14:20"), t("14:20"), 40.020)
    pos(A, t("14:30"), t("14:31"), 40.030)  # one minute of delivery delay

    pos(B, t("14:00"), t("14:00"), 41.000)
    pos(B, t("14:10"), t("14:10"), 41.010)
    pos(B, t("14:50"), t("14:50"), 41.050)  # 40-minute gap
    pos(B, t("15:00"), t("15:00"), 41.060)

    insert_event(con, t("14:05"), "assignment", node_num=A, sector_id="S1")
    insert_event(con, t("14:25"), "clue", node_num=B, sector_id="S2")
    insert_event(con, t("14:55"), "find", node_num=B, sector_id="S2")
    con.commit()
    return con


def test_state_at_returns_last_position_per_node(store):
    rows = state_at(store, t("14:22"))
    assert [(r["node_num"], r["device_time"]) for r in rows] == [(A, t("14:20")), (B, t("14:10"))]


def test_state_at_respects_selection(store):
    rows = state_at(store, t("14:22"), nodes=[B])
    assert [r["node_num"] for r in rows] == [B]
    assert state_at(store, t("14:22"), nodes=[]) == []


def test_state_at_before_first_report_is_empty(store):
    assert state_at(store, t("13:59")) == []


def test_trails_until_excludes_later_rows_and_no_fix_rows(store):
    rows = trails_until(store, t("14:20"), nodes=[A])
    assert [r["device_time"] for r in rows] == [t("14:00"), t("14:10"), t("14:20")]


def test_positions_between_is_half_open(store):
    rows = positions_between(store, t("14:10"), t("14:30"))
    assert [(r["node_num"], r["device_time"]) for r in rows] == [
        (A, t("14:10")),
        (B, t("14:10")),
        (A, t("14:20")),
    ]


def test_events_until(store):
    assert [r["event_type"] for r in events_until(store, t("14:30"))] == ["assignment", "clue"]
    assert [r["event_type"] for r in events_until(store, t("15:00"), types=["find"])] == ["find"]


def test_gaps_finds_the_quiet_period_and_nothing_else(store):
    rows = gaps(store, threshold_s=600)  # ten minutes: A's regular interval is not a gap
    assert [(r["node_num"], r["last_heard"], r["next_heard"], round(r["gap_s"])) for r in rows] == [
        (B, t("14:10"), t("14:50"), 2400)
    ]


def test_no_fix_positions_are_kept_and_flagged(store):
    rows = positions_without_fix(store)
    assert [(r["node_num"], r["rx_time"]) for r in rows] == [(A, t("14:15"))]
