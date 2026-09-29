# sim/ — developing without radios

The hardware is stored at one member's house, so the other three depend on simulation for daily
work (MCM v1.1 §3.8). Three tiers, cheapest first. Only tier 1 exists.

| Tier | What | Needs | Gives the others | Status |
|---|---|---|---|---|
| 1 | `synthetic.py`: library-shaped packets from made-up radios, through the real normalizer | Nothing | A JSON Lines feed of `RadioRecord`s with gaps, relays, no-fix reports, telemetry. Enough to build the daemon's write path, the live view, and replay. | Built |
| 2 | `meshtasticd`: the Meshtastic firmware compiled for Linux, run as a virtual node on a laptop | Linux or Docker | A real node the Python library connects to over TCP (port 4403). Tests the gateway code path and real protobufs, not radio propagation. | Research |
| 3 | Meshtasticator: a discrete-event simulator of a Meshtastic mesh, and an interactive mode that drives several `meshtasticd` nodes | Python, its own repository (not on PyPI) | Collisions, airtime, hop behavior, node placement. Tests the section 6.1 airtime numbers and the gap logic under load. | Research |

Open for tier 2 and 3 (MCM v1.1 §7, "Simulators"): whether Meshtasticator reproduces enough of the
mesh for the other three to develop against, and whether `meshtasticd` runs on everyone's laptop
(Windows needs WSL or Docker). The gateway only speaks serial today; tier 2 needs a TCP transport
in `radio/gateway.py`, which also answers part of MCM v1.1 §9 Q2.

No tier puts a real person's position anywhere. Captures from tier 2 or 3 are synthetic and may be
shared; captures from radios carried by people wait on the retention rule (R-11).
