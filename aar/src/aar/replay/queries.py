"""The questions replay asks of the store, as plain functions over an open connection.

Numbering follows AAR Architecture v1.0 section 3. Every function takes times as UTC ISO-8601
strings, the same text the store holds, so comparisons are plain string order. All position
queries go by device time (the drawing rule in section 7.2); rows with no device time are
returned only by positions_without_fix, so the UI can draw them by receive time and flag them.

Whether these run on the server for every slider move or once to build a browser bundle is open
(section 7.1). The questions are the same either way.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable


def _node_filter(nodes: Iterable[int] | None, column: str = "node_num") -> tuple[str, list[int]]:
    """Build an optional 'AND column IN (?, ?, ...)' clause for a searcher selection (F-04)."""
    if nodes is None:
        return "", []
    ids = list(nodes)
    if not ids:
        return " AND 0", []
    return f" AND {column} IN ({','.join('?' * len(ids))})", ids


def state_at(
    con: sqlite3.Connection, t: str, nodes: Iterable[int] | None = None
) -> list[sqlite3.Row]:
    """Q-01: each selected searcher's last known position at or before t."""
    clause, params = _node_filter(nodes, "p.node_num")
    return con.execute(
        "SELECT p.packet_id, p.node_num, p.device_time, p.rx_time, p.lat, p.lon, p.alt_m,"
        " p.precision_bits"
        " FROM position p"
        " JOIN (SELECT node_num, max(device_time) AS last_time FROM position"
        "       WHERE device_time <= ? GROUP BY node_num) m"
        "   ON p.node_num = m.node_num AND p.device_time = m.last_time"
        f" WHERE 1{clause}"
        " ORDER BY p.node_num",
        [t, *params],
    ).fetchall()


def trails_until(
    con: sqlite3.Connection, t: str, nodes: Iterable[int] | None = None
) -> list[sqlite3.Row]:
    """Q-02: every position of the selected searchers at or before t, ordered for drawing."""
    clause, params = _node_filter(nodes)
    return con.execute(
        "SELECT packet_id, node_num, device_time, rx_time, lat, lon, alt_m, precision_bits"
        " FROM position"
        f" WHERE device_time <= ?{clause}"
        " ORDER BY node_num, device_time, packet_id",
        [t, *params],
    ).fetchall()


def positions_between(
    con: sqlite3.Connection, t1: str, t2: str, nodes: Iterable[int] | None = None
) -> list[sqlite3.Row]:
    """Q-03: every position inside the window [t1, t2), ordered by time.

    Used for chunked loading.
    """
    clause, params = _node_filter(nodes)
    return con.execute(
        "SELECT packet_id, node_num, device_time, rx_time, lat, lon, alt_m, precision_bits"
        " FROM position"
        f" WHERE device_time >= ? AND device_time < ?{clause}"
        " ORDER BY device_time, packet_id",
        [t1, t2, *params],
    ).fetchall()


def events_until(
    con: sqlite3.Connection, t: str, types: Iterable[str] | None = None
) -> list[sqlite3.Row]:
    """Q-04: every timeline event at or before t, oldest first, optionally limited to some types."""
    clause, params = "", []
    if types is not None:
        kinds = list(types)
        clause = f" AND event_type IN ({','.join('?' * len(kinds))})" if kinds else " AND 0"
        params = kinds
    return con.execute(
        "SELECT event_id, event_time, event_type, node_num, sector_id, payload"
        " FROM event"
        f" WHERE event_time <= ?{clause}"
        " ORDER BY event_time, event_id",
        [t, *params],
    ).fetchall()


def gaps(
    con: sqlite3.Connection, threshold_s: float = 300.0, nodes: Iterable[int] | None = None
) -> list[sqlite3.Row]:
    """Q-05: out-of-range gaps, derived from each searcher's consecutive device times.

    A gap is a jump between two consecutive device times of one radio longer than threshold_s.
    Nothing is interpolated across it; the UI annotates it as last heard / next heard.
    This is the 'derive' side of open item A-02; the 'store' side would read gap events instead.
    """
    clause, params = _node_filter(nodes)
    # strftime('%s') gives whole seconds since the epoch, so the subtraction is exact. julianday()
    # would give a float and a 600 s interval could come out as 600.0000001 s.
    return con.execute(
        "WITH s AS ("
        "  SELECT node_num, device_time,"
        "         lag(device_time) OVER (PARTITION BY node_num ORDER BY device_time, packet_id)"
        "           AS prev"
        f"  FROM position WHERE device_time IS NOT NULL{clause}),"
        " g AS ("
        "  SELECT node_num, prev AS last_heard, device_time AS next_heard,"
        "         CAST(strftime('%s', device_time) AS INTEGER)"
        "         - CAST(strftime('%s', prev) AS INTEGER) AS gap_s"
        "  FROM s WHERE prev IS NOT NULL)"
        " SELECT node_num, last_heard, next_heard, gap_s FROM g"
        " WHERE gap_s > ?"
        " ORDER BY node_num, last_heard",
        [*params, threshold_s],
    ).fetchall()


def positions_without_fix(
    con: sqlite3.Connection, nodes: Iterable[int] | None = None
) -> list[sqlite3.Row]:
    """Positions that arrived with no device time (open item A-03), ordered by receive time."""
    clause, params = _node_filter(nodes)
    return con.execute(
        "SELECT packet_id, node_num, rx_time, lat, lon, alt_m, precision_bits"
        " FROM position"
        f" WHERE device_time IS NULL{clause}"
        " ORDER BY rx_time, packet_id",
        params,
    ).fetchall()
