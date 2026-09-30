"""Out-of-range gaps: one definition, used live (quiet-node watch) and after the fact (from a log).

MCM v1.1 section 6.8 and AAR Architecture v1.0 A-02. Whether gaps are stored as events or only
derived is Open. Either way the definition must be the same in both places, so it lives here:

    A gap is two consecutive reports from one radio whose times are more than
    gap_threshold_s apart (radio profile: gap_factor x broadcast interval).

Gaps are shown and annotated, never interpolated. Nothing in this module invents a position.

Which clock: device time when both reports have one, else the command post receive time, and the
gap says which it used. Silence is not proof of being out of range: a radio with smart position
broadcast on, a dead battery, or a switched-off radio also goes quiet. The gap records silence;
the annotation can say what else was known (last battery, last SNR).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from mcm.contract.record import RadioRecord


def _t(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Gap:
    node: int
    last_heard: str
    next_heard: str | None  # None: still quiet (live watch only)
    seconds: float
    clock: str  # "device" or "receive"
    last_seq: int
    next_seq: int | None


def _report_time(rec: RadioRecord) -> tuple[str, str]:
    if rec.position and rec.position.device_time:
        return rec.position.device_time, "device"
    return rec.rx_time_host, "receive"


def find_gaps(records: Iterable[RadioRecord], threshold_s: float) -> list[Gap]:
    """Gaps in position reports, per radio, from a finished log. Records may arrive unordered."""
    by_node: dict[int, list[RadioRecord]] = {}
    for rec in records:
        if rec.kind == "position" and rec.position is not None:
            by_node.setdefault(rec.header.from_node, []).append(rec)
    gaps: list[Gap] = []
    for node, recs in sorted(by_node.items()):
        recs.sort(key=lambda r: (_t(_report_time(r)[0]), r.seq))
        for a, b in zip(recs, recs[1:], strict=False):
            (ta, ca), (tb, cb) = _report_time(a), _report_time(b)
            clock = "device" if ca == cb == "device" else "receive"
            if clock == "receive":
                ta, tb = a.rx_time_host, b.rx_time_host
            dt = (_t(tb) - _t(ta)).total_seconds()
            if dt > threshold_s:
                gaps.append(Gap(node, ta, tb, dt, clock, a.seq, b.seq))
    return gaps


class QuietNodeWatch:
    """Live: which radios have been silent longer than the threshold right now.

    The daemon feeds every record to observe() and calls quiet(now) on a timer. What it does with
    the answer (an alert on the (P)MP screen, a stored gap event) is the daemon's and the team's
    call (A-02). This class keeps no history beyond the last report per radio.
    """

    def __init__(self, threshold_s: float) -> None:
        self.threshold_s = threshold_s
        self._last: dict[int, RadioRecord] = {}

    def observe(self, rec: RadioRecord) -> Gap | None:
        """Record a report. Returns the closed gap if this radio was quiet and is heard again."""
        if rec.kind != "position" or rec.position is None:
            return None
        node = rec.header.from_node
        prev = self._last.get(node)
        self._last[node] = rec
        if prev is None:
            return None
        found = find_gaps([prev, rec], self.threshold_s)
        return found[0] if found else None

    def quiet(self, now_iso: str) -> list[Gap]:
        """Radios whose last report is older than the threshold, by the command post clock."""
        now = _t(now_iso)
        out = []
        for node, rec in sorted(self._last.items()):
            dt = (now - _t(rec.rx_time_host)).total_seconds()
            if dt > self.threshold_s:
                out.append(Gap(node, rec.rx_time_host, None, dt, "receive", rec.seq, None))
        return out
