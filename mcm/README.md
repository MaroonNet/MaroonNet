# MCM — Mesh Connectivity Map (MaroonNet)

MCM is the field: radio-to-radio communication over Meshtastic LoRa, the gateway radio at the
command post, the mesh coverage model (co-owned with (P)MP), and what the field exchanges with the
command post. Every data point in MaroonNet starts here. This folder holds MCM's side of that: the
radio record every packet becomes, the gateway that produces it, the airtime math, the coverage
model interface, the field message set, field warnings, and a synthetic radio feed so the other
segments can build without hardware. See segment document MCM v1.1 and
**[docs/maroonnet-mcm-architecture-v1_0.md](docs/maroonnet-mcm-architecture-v1_0.md)**. The document
lives inside `mcm/` for now; it can move beside the AAR one in `docs/architecture/` later.

> Everything in this package is a **draft**. The radio record is proposed, not decided. The
> firmware is not pinned. Nothing here is in the Decision Log.

## Quick start

```bash
cd mcm
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                                # add ,radio for a real gateway radio

mcm airtime                                            # utilization table, MCM v1.1 section 6.1
mcm synth --nodes 10 --hours 6                         # writes data/synthetic/feed.jsonl
mcm inspect data/synthetic/feed.jsonl                  # what the feed holds, and its gaps
mcm profile                                            # radio profile and firmware pin status
pytest                                                 # 41 tests, no radio needed
```

No runtime dependencies. The `meshtastic` library is the `radio` extra and is imported only when a
gateway radio is opened.

## The hand-off, in one line each

- **Radio layer produces:** one `RadioRecord` per packet the gateway hears, every header field, two
  receive clocks, a sequence number (`src/mcm/contract/record.py`, item M-01).
- **In what format:** a frozen Python dataclass in process; one JSON object per line on disk.
- **Who hands it to whom:** the (P)MP bridge daemon creates a `Gateway` and passes a callback;
  MCM calls it once per packet. The daemon writes the mission store (C-01, AAR) and pushes to the
  screen (C-02). MCM never writes to the store.

## What exists now (build step 0: scaffold)

| Piece | File | What it does |
|---|---|---|
| Radio record | `src/mcm/contract/record.py` | M-01: `RadioRecord`, `PacketHeader`, `PositionFix`, `TelemetrySample`, `NodeInfo`; JSON Lines read and write. Field names match the C-01 draft columns. |
| Normalizer | `src/mcm/radio/normalize.py` | Meshtastic library packet dict to `RadioRecord`. The one place that knows the library's key names. |
| Gateway | `src/mcm/radio/gateway.py` | Opens the USB serial radio, numbers packets, hands records to the daemon, checks the firmware pin, sends text. |
| Radio profile | `configs/radio_profile.toml`, `src/mcm/radio/profile.py` | Firmware pin (C-08, empty until chosen), transport, preset, hop limit, interval, gap threshold. |
| Airtime | `src/mcm/mesh/airtime.py` | LoRa time on air per preset; channel utilization; the node limit under a ceiling. Reproduces the MCM v1.1 section 6.1 table. |
| Gaps | `src/mcm/mesh/gaps.py` | One gap definition used after the fact (`find_gaps`) and live (`QuietNodeWatch`). Never interpolates. |
| Coverage | `src/mcm/coverage/` | The model interface, a free-space baseline (an upper bound only), and the predicted-against-observed harness. |
| Field message set | `src/mcm/messages/catalog.py` | What can go to the field, whether the stock app shows it, size, airtime cost. |
| Field warnings | `src/mcm/field_warnings/rules.py` | The three candidates; buffer-overwrite works now, the other two wait on (P)MP. |
| Simulation | `src/mcm/sim/` | Synthetic library-shaped packets through the real normalizer. meshtasticd and Meshtasticator next. |
| CLI | `src/mcm/cli.py` | `mcm airtime`, `synth`, `inspect`, `profile`. |
| Tests | `tests/` | One file per area; hand-built packet fixtures until a real capture exists. |

## Layout

```
configs/radio_profile.toml    firmware pin, gateway, LoRa preset, position interval, gap threshold
docs/ROADMAP.md               phases and gates for this segment
docs/maroonnet-mcm-architecture-v1_0.md   this segment's architecture, v1.0
data/                         synthetic feeds and captures, local only, never committed
src/mcm/
  contract/record.py          M-01 radio record, JSON Lines
  radio/                      normalize.py, gateway.py, profile.py
  mesh/                       airtime.py, gaps.py
  coverage/                   model.py (interface + baseline), validate.py
  messages/catalog.py         the field message set
  field_warnings/rules.py     outside sector, losing connectivity, buffer overwrite
  sim/                        synthetic.py; README.md for meshtasticd and Meshtasticator
  cli.py                      mcm airtime | synth | inspect | profile
tests/                        fixtures/ + one test file per area
```

Every folder carries `claude/` and `archive/` placeholders per the Team Claude Guide §3.3.

## Roadmap

**[docs/ROADMAP.md](docs/ROADMAP.md)**.

1. ✅ Scaffold: radio record, normalizer, gateway, airtime, gaps, coverage interface, synthetic feed
2. Firmware pinned (C-08); a real capture replaces the hand-built fixtures; M-01 confirmed with the daemon and C-01
3. meshtasticd on a laptop; the daemon runs against it; bench test with the Heltec V3 boards
4. Preset and interval from a field test; the coverage model gains terrain; validation against SPLAT!
5. Vertical slice: radios to daemon to store to live view

## Sources

* MCM v1.1 (segment document) §2, §3, §6, §9; AAR Architecture v1.0 §4, §6, §10 (A-02, A-03)
* Meshtastic documentation: radio settings (modem presets); firmware source (preamble length)
* Semtech SX1261/2 datasheet, LoRa time-on-air formula
