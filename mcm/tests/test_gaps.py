from mcm.contract.record import PacketHeader, PositionFix, RadioRecord
from mcm.mesh.gaps import QuietNodeWatch, find_gaps


def pos(seq, node, t, device=True):
    return RadioRecord(
        seq=seq,
        rx_time_host=t,
        header=PacketHeader(from_node=node, hop_start=3, hop_limit=3),
        portnum="POSITION_APP",
        kind="position",
        position=PositionFix(39.9, -105.2, device_time=t if device else None),
    )


def test_gap_found_between_reports_and_never_filled():
    recs = [
        pos(1, 7, "2026-10-03T14:00:00Z"),
        pos(2, 7, "2026-10-03T14:01:00Z"),
        pos(3, 7, "2026-10-03T14:15:00Z"),
        pos(4, 8, "2026-10-03T14:00:30Z"),
    ]
    gaps = find_gaps(recs, threshold_s=180)
    assert len(gaps) == 1
    g = gaps[0]
    assert (g.node, g.last_heard, g.next_heard, g.seconds, g.clock) == (
        7,
        "2026-10-03T14:01:00Z",
        "2026-10-03T14:15:00Z",
        840.0,
        "device",
    )
    assert (g.last_seq, g.next_seq) == (2, 3)


def test_unordered_input():
    recs = [pos(3, 7, "2026-10-03T14:15:00Z"), pos(1, 7, "2026-10-03T14:00:00Z")]
    assert len(find_gaps(recs, 180)) == 1


def test_falls_back_to_receive_clock_without_fix():
    recs = [pos(1, 7, "2026-10-03T14:00:00Z"), pos(2, 7, "2026-10-03T14:10:00Z", device=False)]
    assert find_gaps(recs, 180)[0].clock == "receive"


def test_quiet_node_watch():
    w = QuietNodeWatch(threshold_s=180)
    assert w.observe(pos(1, 7, "2026-10-03T14:00:00Z")) is None
    assert w.quiet("2026-10-03T14:02:00Z") == []
    q = w.quiet("2026-10-03T14:10:00Z")
    assert len(q) == 1 and q[0].next_heard is None and q[0].seconds == 600
    closed = w.observe(pos(2, 7, "2026-10-03T14:12:00Z"))
    assert closed is not None and closed.seconds == 720
