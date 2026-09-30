"""Synthetic radio feed: library-shaped packets from made-up radios, with no hardware.

This is the zero-install tier of simulation (MCM Architecture v1.0 section 6.6). It produces the
same packet dicts the Meshtastic library delivers, so they go through the real normalize() path and
come out as RadioRecords. The other three segments can build against its JSON Lines output today.

What it models: N radios on a random walk around a command post; one report per interval with
jitter; some reports relayed (hops > 0, SNR and RSSI from the relay); out-of-range stretches where
nothing arrives; a few reports with no GPS time; periodic device telemetry. What it does not model:
terrain, collisions, airtime limits, real routing. Those are the next tiers (meshtasticd and
Meshtasticator), in sim/README.md.

Deterministic per seed. No real person is in it.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

from mcm.contract.record import RadioRecord
from mcm.radio.normalize import normalize

GATEWAY_NODE = 0x0CAFE000
START = datetime(2026, 10, 3, 14, 0, 0, tzinfo=UTC)
CP_LAT, CP_LON = 39.9936, -105.2811  # a placeholder point west of Boulder, not a mission site


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def packets(
    n_nodes: int = 6,
    hours: float = 1.0,
    interval_s: int = 60,
    seed: int = 7,
    gap_rate: float = 0.01,
) -> Iterator[tuple[datetime, dict[str, Any]]]:
    """Yield (receive time, library-shaped packet dict) in receive order."""
    rng = random.Random(seed)
    nodes = [0x0A000001 + i for i in range(n_nodes)]
    state = {n: [CP_LAT, CP_LON, 0.0] for n in nodes}  # lat, lon, heading
    quiet_until: dict[int, datetime] = {}
    events: list[tuple[datetime, dict[str, Any]]] = []
    mesh_id = rng.randrange(1, 2**31)
    steps = int(hours * 3600 // interval_s)

    for step in range(steps):
        for node in nodes:
            t = START + timedelta(seconds=step * interval_s + rng.uniform(0, interval_s * 0.2))
            lat, lon, hdg = state[node]
            hdg += rng.uniform(-0.6, 0.6)
            dist = rng.uniform(20, 70)  # meters per interval, walking pace
            lat += dist * math.cos(hdg) / 111_320
            lon += dist * math.sin(hdg) / (111_320 * math.cos(math.radians(lat)))
            state[node] = [lat, lon, hdg]

            if node in quiet_until and t < quiet_until[node]:
                continue  # out of range: the report is never heard
            if rng.random() < gap_rate:
                quiet_until[node] = t + timedelta(minutes=rng.uniform(5, 25))
                continue

            mesh_id += 1
            hops = 0 if rng.random() < 0.7 else rng.randint(1, 2)
            has_fix = rng.random() > 0.02
            rx = t + timedelta(seconds=rng.uniform(0.5, 3.0) * (hops + 1))
            pkt: dict[str, Any] = {
                "from": node,
                "to": 0xFFFFFFFF,
                "id": mesh_id,
                "channel": 0,
                "hopStart": 3,
                "hopLimit": 3 - hops,
                "relayNode": (nodes[(nodes.index(node) + 1) % n_nodes] & 0xFF) if hops else None,
                "rxSnr": round(rng.uniform(-15, 8), 2),
                "rxRssi": rng.randint(-125, -70),
                "rxTime": int(rx.timestamp()),
                "decoded": {
                    "portnum": "POSITION_APP",
                    "position": {
                        "latitudeI": round(lat * 1e7),
                        "longitudeI": round(lon * 1e7),
                        "altitude": round(1650 + rng.uniform(-40, 120)),
                        "time": int(t.timestamp()) if has_fix else 0,
                        "precisionBits": 32,
                    },
                },
            }
            events.append((rx, pkt))

            if step % 10 == 0:
                mesh_id += 1
                events.append(
                    (
                        rx + timedelta(seconds=5),
                        {
                            "from": node,
                            "to": 0xFFFFFFFF,
                            "id": mesh_id,
                            "hopStart": 3,
                            "hopLimit": 3,
                            "rxSnr": round(rng.uniform(-10, 8), 2),
                            "rxRssi": rng.randint(-120, -70),
                            "decoded": {
                                "portnum": "TELEMETRY_APP",
                                "telemetry": {
                                    "time": int(t.timestamp()),
                                    "deviceMetrics": {
                                        "batteryLevel": max(5, 100 - step // 6),
                                        "voltage": round(4.15 - step * 0.002, 3),
                                        "channelUtilization": round(rng.uniform(5, 30), 2),
                                        "airUtilTx": round(rng.uniform(0.5, 3), 2),
                                    },
                                },
                            },
                        },
                    )
                )

    events.sort(key=lambda e: e[0])
    yield from events


def records(**kwargs: Any) -> Iterator[RadioRecord]:
    """The synthetic feed as RadioRecords, numbered in receive order like a real gateway."""
    for seq, (rx, pkt) in enumerate(packets(**kwargs), start=1):
        yield normalize(pkt, seq=seq, rx_time_host=_iso(rx), gateway_node=GATEWAY_NODE)
