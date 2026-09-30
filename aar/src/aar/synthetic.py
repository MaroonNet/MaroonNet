"""A synthetic mission for tests and demos. No real person is in it.

Searchers walk at about one metre per second on a random heading that drifts. Each report is
delayed by a few seconds (delivery over the mesh). Now and then a radio goes out of range for
five to twenty-five minutes: those reports are dropped, which is what happens on a real mesh
(the node keeps no track memory; MCM v1.1 section 6.8). One report in a hundred arrives with
no device time, to exercise open item A-03. A handful of timeline events are sprinkled in.

Everything is deterministic for a given seed.
"""

from __future__ import annotations

import math
import random
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from aar.store import db

ORIGIN_LAT, ORIGIN_LON = 40.39, -105.60  # near Rocky Mountain National Park, WGS84
EVENT_TYPES = ("assignment", "edit", "override", "message", "clue", "find")


@dataclass
class Summary:
    nodes: int
    positions: int
    positions_without_fix: int
    telemetry: int
    events: int
    started_at: str
    ended_at: str


def iso(dt: datetime) -> str:
    """UTC ISO-8601 with a Z suffix, the store's time format."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(
    con: sqlite3.Connection,
    n_nodes: int = 10,
    hours: float = 6.0,
    interval_s: int = 60,
    seed: int = 7,
    start: datetime | None = None,
) -> Summary:
    """Fill an open mission store with a synthetic mission and return counts."""
    rng = random.Random(seed)
    t0 = start or datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    t_end = t0 + timedelta(hours=hours)
    steps = int(hours * 3600 / interval_s)
    nodes = [0x10000000 + i for i in range(n_nodes)]

    lat = {n: ORIGIN_LAT + rng.uniform(-0.02, 0.02) for n in nodes}
    lon = {n: ORIGIN_LON + rng.uniform(-0.02, 0.02) for n in nodes}
    heading = {n: rng.uniform(0, 2 * math.pi) for n in nodes}
    quiet_until = {n: -1 for n in nodes}  # step index until which a radio is out of range

    for n in nodes:
        db.ensure_node(
            con,
            n,
            iso(t0),
            long_name=f"Searcher {n - 0x10000000 + 1:02d}",
            short_name=f"S{n - 0x10000000 + 1:02d}",
        )

    positions = no_fix = telemetry = 0
    metres_per_deg_lat = 111_000.0
    metres_per_deg_lon = 111_000.0 * math.cos(math.radians(ORIGIN_LAT))

    for k in range(steps):
        t = t0 + timedelta(seconds=k * interval_s)
        for n in nodes:
            # Move first, so the walk continues while a radio is out of range.
            heading[n] += rng.uniform(-0.6, 0.6)
            step_m = 1.0 * interval_s
            lat[n] += step_m * math.cos(heading[n]) / metres_per_deg_lat
            lon[n] += step_m * math.sin(heading[n]) / metres_per_deg_lon

            if k < quiet_until[n]:
                continue  # out of range: nothing delivered, nothing stored
            if rng.random() < 0.004:
                quiet_until[n] = k + rng.randint(300, 1500) // interval_s
                continue

            rx = t + timedelta(seconds=rng.expovariate(1 / 8.0))  # mean 8 s delivery delay
            has_fix = rng.random() > 0.01
            pid = db.insert_packet(
                con,
                rx_time=iso(rx),
                from_node=n,
                to_node=0xFFFFFFFF,
                mesh_id=rng.getrandbits(32),
                portnum="POSITION_APP",
                hop_start=3,
                hop_limit=rng.randint(0, 3),
                relay_node=rng.choice(nodes) if rng.random() < 0.5 else None,
                rx_snr=round(rng.uniform(-12, 10), 2),
                rx_rssi=rng.randint(-125, -60),
                want_ack=False,
                decoded={"latitude": lat[n], "longitude": lon[n], "altitude": 2800},
            )
            db.insert_position(
                con,
                pid,
                n,
                iso(t) if has_fix else None,
                iso(rx),
                lat[n],
                lon[n],
                alt_m=2800 + rng.uniform(-50, 50),
                precision_bits=32,
            )
            positions += 1
            no_fix += 0 if has_fix else 1

            if k % max(1, 1800 // interval_s) == 0:  # telemetry every 30 minutes
                tid = db.insert_packet(
                    con,
                    rx_time=iso(rx + timedelta(seconds=1)),
                    from_node=n,
                    to_node=0xFFFFFFFF,
                    mesh_id=rng.getrandbits(32),
                    portnum="TELEMETRY_APP",
                    hop_start=3,
                    hop_limit=rng.randint(0, 3),
                    rx_snr=round(rng.uniform(-12, 10), 2),
                    rx_rssi=rng.randint(-125, -60),
                    want_ack=False,
                )
                db.insert_telemetry(
                    con,
                    tid,
                    n,
                    iso(rx + timedelta(seconds=1)),
                    battery_pct=round(95 - 60 * k / max(steps, 1), 1),
                    voltage=3.9,
                    channel_util=round(rng.uniform(5, 30), 1),
                    air_util_tx=round(rng.uniform(0.5, 4), 2),
                )
                telemetry += 1

    events = 0
    db.insert_event(con, iso(t0), "mission", payload={"state": "started"})
    events += 1
    for _ in range(max(4, int(hours * 6))):  # about six events an hour
        t = t0 + timedelta(seconds=rng.uniform(0, hours * 3600))
        db.insert_event(
            con,
            iso(t),
            rng.choice(EVENT_TYPES),
            node_num=rng.choice(nodes),
            sector_id=f"S{rng.randint(1, 12)}",
            payload={"note": "synthetic"},
        )
        events += 1
    db.insert_event(con, iso(t_end), "mission", payload={"state": "ended"})
    events += 1

    con.execute("UPDATE mission SET ended_at = ?", (iso(t_end),))
    con.commit()
    return Summary(n_nodes, positions, no_fix, telemetry, events, iso(t0), iso(t_end))
