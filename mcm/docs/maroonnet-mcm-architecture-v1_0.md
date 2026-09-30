# MaroonNet MCM Architecture

**Segment architecture for the Mesh Connectivity Map: what comes off the radios, in what form, who hands it to whom, and how the `mcm/` package is laid out**

CU Denver Capstone Team: Diego Alas, Corey Greene, Elijah Heimsoth, Joshua 'JJ' Wagner

Segment architecture document, version 1.0 · Segment owner: Diego Alas · September 29, 2026 · First version, branched from MCM v1.1. Draft for the owner's review, then shared for iteration.

---

## Contents

1. [Purpose and status](#1-purpose-and-status)
2. [Where MCM sits](#2-where-mcm-sits)
3. [Data flow in and out](#3-data-flow-in-and-out)
4. [The radio record (M-01): MCM's side of the contract](#4-the-radio-record-m-01-mcms-side-of-the-contract)
5. [Out-of-range gaps (A-02)](#5-out-of-range-gaps-a-02)
6. [Sub-modules](#6-sub-modules)
7. [Package layout: `mcm/`](#7-package-layout-mcm)
8. [Boundary: what MCM consumes, exposes, and signs](#8-boundary-what-mcm-consumes-exposes-and-signs)
9. [Roadblocks for this segment](#9-roadblocks-for-this-segment)
10. [Open questions](#10-open-questions)
11. [Build order for this segment](#11-build-order-for-this-segment)
12. [Research the owner will do](#12-research-the-owner-will-do)

---

## 1 Purpose and status

This document is the architecture of one segment, the Mesh Connectivity Map. It sits beside AAR Architecture v1.0 and under MaroonNet Architecture v1.0. It answers four questions:

- What the radio layer produces for every packet, in what format, and who hands it to whom.
- How out-of-range gaps are defined, and the two ways to keep them.
- What each MCM sub-module does, and what it waits on.
- How the `mcm/` package is laid out so work can start.

It does not define the mission store (C-01, owned by the AAR) or the bridge daemon and its screen messages (C-02, (P)MP). It writes down what MCM hands to them, with field names chosen to line up with the C-01 draft, so the daemon can map a record to a row by name.

**Status labels.** Every claim carries one label.

| Label | Meaning |
| --- | --- |
| **Verified** | In the Decision Log, with its V-number. |
| **Team answer** | Stated by the owner or the team on September 17, 2026, or later in a meeting. Not yet logged. |
| **Open** | Not decided. |
| **Research** | The owner needs information before the team can decide. |
| **Proposed** | Written by this document as a starting point. Not decided. The team votes. |

Nothing in this document is decided by this document. The owner verifies; the Decision Log records. Segment codes: **SPM** (JJ), **(P)MP** (Elijah), **AAR** (Corey), **MCM** (Diego). Numbered items from other documents keep their numbers: C-nn contracts, I-nn integration points, R-nn roadblocks from Architecture v1.0; A-nn from AAR Architecture v1.0. Items new in this document use **M-nn**. If Architecture v1.0 already numbers the radio-to-daemon hand-off, M-01 takes that number.

**Sources.** MCM v1.1; AAR Architecture v1.0 (branch `feat/aar-scaffold`, not yet merged) and its C-01 draft `aar/src/aar/store/schema.sql`; the `MaroonNet/MaroonNet` repository as of September 29, 2026, including `feat/spm-framework`; `CLAUDE.md`; Meshtastic documentation (radio settings, modem presets); the Meshtastic firmware source (preamble length); the Semtech SX1261/2 datasheet (time on air). MaroonNet Architecture v1.0 itself was not available to this draft; its item numbers are used as AAR Architecture v1.0 cites them.

---

## 2 Where MCM sits

MCM is the field: radio to radio over Meshtastic LoRa, the gateway radio at the command post, the coverage model (co-owned with (P)MP), and the searcher's phone. **Team answer** It runs on stock radios with stock firmware and a basic setup; a screen-equipped radio is out. **Verified** V-14. Field members use the stock Meshtastic apps in the fall vertical slice. **Team answer**

Every data point MaroonNet stores starts as a packet on the mesh. The chain from a searcher's radio to the database:

```
 field radio ──LoRa mesh──▶ gateway radio ──USB serial──▶ meshtastic library ──▶ mcm Gateway
 (firmware)     (relays)     (firmware, CP)                (host, Python)          normalize()
                                                                                       │
                                                         RadioRecord, one per packet   │  M-01
                                                                                       ▼
                                                                (P)MP bridge daemon ── owns the process
                                                                   │            │
                                                          C-01 rows │            │ C-02 push
                                                                   ▼            ▼
                                                            mission store    live (P)MP screen
                                                            (AAR schema)     AAR replay later
```

MCM owns everything left of the arrow marked M-01 and the record that crosses it. The daemon owns everything to the right. MCM never writes to the store. **Proposed**

---

## 3 Data flow in and out

From MCM v1.1 §2, with the hand-off named for each row.

| Direction | Data | From / to | Crosses at | Status |
| --- | --- | --- | --- | --- |
| Out | Positions, telemetry, and signal data from every node | Gateway radio → `Gateway` → daemon → store; shown live on (P)MP; replayed by AAR | M-01 (§4) | **Team answer** |
| Out | Out-of-range gaps | Derived from the record stream, or written as events by the daemon; shown and annotated, never interpolated | §5; A-02 | **Team answer**; storage **Open** |
| Out | Live coverage overlay | Coverage model on current positions → (P)MP screen | C-06 | **Open** |
| Out | Quiet-node alerts | `QuietNodeWatch` (§5.4) → daemon → (P)MP screen | C-02 | **Proposed** |
| In | Sectors, assignments, waypoints, text | (P)MP → daemon → `Gateway.send_*` → mesh. Text and waypoints work with stock apps; sector polygons need a custom app | §4.7; §6.4 | **Team answer** |
| In | Radio spacing | (P)MP computes it from team size and radio count; MCM supplies the node limit (§6.2) | — | **Team answer** |
| In | Coverage model on planned positions | Co-owned. (P)MP runs it pre-mission; MCM runs it live. Same code | §6.3 | **Team answer**; split **Open** |
| In | Command post radio configuration | (P)MP screen; first segment stretch goal | §6.1 | **Team answer** |
| Inside | Firmware pin, preset, interval, gateway, message set, warnings, simulation | MCM only | §6 | — |

---

## 4 The radio record (M-01): MCM's side of the contract

### 4.1 Who hands what to whom

**Proposed.**

| Step | Who owns it | What it hands on | Format |
| --- | --- | --- | --- |
| 1. Field radio broadcasts | MCM (firmware config) | MeshPacket over LoRa, encrypted with the channel key | Meshtastic protobuf |
| 2. Mesh relays | Firmware | The same packet, hop limit decremented | Protobuf |
| 3. Gateway radio hears it | MCM (gateway config) | The packet plus receive SNR, RSSI, receive time | Protobuf over USB serial |
| 4. Library decodes it | Meshtastic Python library | A packet dict on pubsub topic `meshtastic.receive` | Python dict, camelCase keys |
| 5. `Gateway.handle_packet` normalizes it | **MCM** | One `RadioRecord`, numbered | Frozen dataclass (in process) |
| 6. Callback into the daemon | **MCM calls, daemon receives** | The same `RadioRecord` | `on_record(record)` |
| 7. Daemon stores and pushes | (P)MP daemon | C-01 rows; C-02 messages | AAR's schema; (P)MP's messages |

Step 6 is the contract line. The daemon creates the `Gateway`, passes its callback, and owns the process, the thread, and the store. MCM owns steps 1 to 5 and guarantees what arrives at step 6 (§4.6).

On disk, the same records are JSON Lines: one record per line, keys sorted, UTF-8. That is the format of capture files and of the synthetic feed (§4.8). It is not a database and does not compete with C-01.

### 4.2 Record shape

**Proposed.** `mcm/src/mcm/contract/record.py`. A directly heard position looks like this:

```json
{
  "schema": "mcm.radio_record/0.1-draft",
  "seq": 1,
  "rx_time_host": "2026-10-03T14:00:05.760313Z",
  "rx_time_radio": "2026-10-03T14:00:05Z",
  "gateway_node": 212852736,
  "portnum": "POSITION_APP",
  "kind": "position",
  "header": {
    "from_node": 167772167, "to_node": 4294967295, "mesh_id": 695425578, "channel": 0,
    "hop_start": 3, "hop_limit": 3, "relay_node": null,
    "rx_snr": 6.09, "rx_rssi": -94, "want_ack": null, "via_mqtt": null
  },
  "position": {
    "lat": 39.9939979, "lon": -105.2810305, "alt_m": 1623.0,
    "device_time": "2026-10-03T14:00:04Z", "precision_bits": 32,
    "sats_in_view": null, "pdop": null
  },
  "telemetry": null, "text": null, "node_info": null,
  "decoded_extra": {},
  "raw_b64": null
}
```

`kind` is one of `position`, `telemetry`, `text`, `node_info`, `waypoint`, `other`, `undecoded`. Exactly one of the typed blocks is filled for the first four kinds. Every other decoded field goes to `decoded_extra`, JSON-safe (bytes as base64). `raw_b64` is the serialized MeshPacket, the untouched original. Synthetic records have no raw bytes.

### 4.3 Field contract

Every field in MCM v1.1 §3.2, where it comes from, where it sits in the record, and the C-01 draft column it lines up with. The last column is the AAR's to decide; it is listed so the mapping can be checked, not to define the schema.

| MCM v1.1 §3.2 field | Library key (from the protobuf) | Record field | Unit, rule | C-01 draft column |
| --- | --- | --- | --- | --- |
| Latitude | `decoded.position.latitude`, or `latitudeI` × 1e-7 | `position.lat` | WGS84 decimal degrees, float | `position.lat` |
| Longitude | `decoded.position.longitude`, or `longitudeI` × 1e-7 | `position.lon` | Same | `position.lon` |
| Altitude | `decoded.position.altitude` | `position.alt_m` | Meters; `null` when not sent | `position.alt_m` |
| Time | `decoded.position.time` | `position.device_time` | UTC ISO-8601; `null` when 0 or absent (no fix) | `position.device_time` |
| Precision bits | `decoded.position.precisionBits` | `position.precision_bits` | As reported; never sharpened | `position.precision_bits` |
| From | `from` | `header.from_node` | Node number | `packet.from_node` |
| To | `to` | `header.to_node` | Node number; 4294967295 is broadcast | `packet.to_node` |
| Id | `id` | `header.mesh_id` | Packet id | `packet.mesh_id` |
| Hop start | `hopStart` | `header.hop_start` | | `packet.hop_start` |
| Hop limit | `hopLimit` | `header.hop_limit` | Remaining when heard | `packet.hop_limit` |
| Relay node | `relayNode` | `header.relay_node` | Low byte of the relayer's node number (§4.5) | `packet.relay_node` |
| SNR | `rxSnr` | `header.rx_snr` | dB, last hop only (§4.5) | `packet.rx_snr` |
| RSSI | `rxRssi` | `header.rx_rssi` | dBm, last hop only | `packet.rx_rssi` |
| Battery | `decoded.telemetry.deviceMetrics.batteryLevel` | `telemetry.battery_pct` | Percent | `telemetry.battery_pct` |
| Voltage | `...deviceMetrics.voltage` | `telemetry.voltage` | Volts | `telemetry.voltage` |
| Channel utilization | `...deviceMetrics.channelUtilization` | `telemetry.channel_util` | Percent, as the node sees the channel | `telemetry.channel_util` |
| Air utilization | `...deviceMetrics.airUtilTx` | `telemetry.air_util_tx` | Percent, the node's own transmissions | `telemetry.air_util_tx` |

Fields MCM carries that the C-01 draft has no column for today. Each can live in `packet.decoded` (JSON) or get a column; the AAR decides (M-02):

| Record field | Why it matters |
| --- | --- |
| `rx_time_radio` | The gateway radio's clock. Unreliable without a GPS fix on the gateway (MCM v1.1 §9 Q3), so the host clock is the proposed `rx_time` (§4.4). |
| `seq` | Per-gateway-session order. A hole in `seq` at the daemon means a record was lost between MCM and the store, not on the mesh. |
| `header.channel`, `header.via_mqtt` | Which channel; whether a packet arrived through MQTT rather than over the air (matters for coverage validation if MQTT ever appears). |
| `telemetry.device_time`, `telemetry.uptime_s` | Telemetry has its own time; uptime shows a radio that rebooted. |
| `position.sats_in_view`, `position.pdop` | Fix quality, for reading a position's reliability in replay. Sent only when the position flags ask for them. |
| `node_info` | Long name, short name, hardware model; the C-01 `node` table's columns. |

Three rules for the daemon, from the C-01 draft's own notes: `portnum` is never empty (an undecodable packet carries `UNKNOWN`); a `null` stays `NULL` and is never written as 0; the record is the only input, so a field MCM does not send is not in the store.

### 4.4 Clocks

Four orderings travel with each record. **Proposed.**

| Clock | Record field | Set by | Use |
| --- | --- | --- | --- |
| Device time | `position.device_time` | The field radio's GPS | Replay draws by it (AAR Architecture v1.0 §7.2). `null` without a fix. |
| Host receive time | `rx_time_host` | The command post laptop, at step 5 | Proposed as C-01 `rx_time`. The laptop clock is the one clock the team controls. |
| Radio receive time | `rx_time_radio` | The gateway radio | Kept for comparison. Without GPS on the gateway it can be unset or wrong. |
| Sequence | `seq` | `Gateway`, per session | Order within a session; loss detection between MCM and the daemon. The C-01 `packet_id` insert order stays the store's third clock. |

Device time minus host receive time is the delivery delay (AAR §4.3). A relayed packet's delay grows with each hop. What the firmware sends as `time` when a radio has no fix is **Research** (A-03, with Corey); the normalizer treats 0 as no time and says so in the record.

### 4.5 Signal data: what it does and does not say

This is the reason the daemon logs every field from the first day (MCM v1.1 §3.2), and it is easy to misread later.

- **SNR and RSSI describe the last hop into the gateway, not the origin.** A packet relayed twice carries the SNR of the relay's transmission. Only a packet with `hop_start == hop_limit` (zero hops taken, `heard_directly`) measures the origin radio's own link. Coverage validation (§6.3) uses only those.
- **`relay_node` is not a full node number.** Current firmware reports only its low byte, to save header space. It narrows the relayer to a few candidates; the node list resolves it when the byte is unique. **Research**: confirm on the pinned version.
- **`hop_start − hop_limit` is the hops taken.** It is derived, not stored separately.
- **A packet that never arrived leaves no row.** Missed reception is visible only as a gap (§5), never as a low RSSI.
- **Encrypted packets the gateway cannot decode still carry signal data.** They become `undecoded` records with a full header. They count as reception for coverage.

### 4.6 What MCM guarantees at the hand-off

**Proposed.** The daemon can rely on these; tests in `mcm/tests/` hold them.

1. One record per packet the library delivers, in the order received, with `seq` rising by one.
2. Every header field present in every record, `null` when the radio did not send it.
3. No value invented: no interpolated position, no filled-in time, no zero for missing.
4. Times UTC ISO-8601 ending in `Z`; coordinates WGS84 decimal degrees as floats; units as in §4.3. These match `CLAUDE.md`.
5. A record is built and handed on even if the daemon's callback raises; the error is logged with its `seq`.
6. The record carries its schema string. A record with a different schema string is refused on read.

### 4.7 The other direction: to the field

**Proposed.** The daemon calls `Gateway.send_text(text, channel, dest)` for commands from (P)MP. The gateway refuses a message that does not fit one packet (§6.4). Waypoints and, later, custom message types follow the same path. Outbound sends are recorded by the daemon as `message` rows with `direction = out`; MCM does not log them itself.

### 4.8 Capture files

**Proposed.** `mcm synth` writes the synthetic feed; a capture command (phase 2) will write real feeds. Both are JSON Lines of `RadioRecord`. They let the other three segments build the daemon's write path, the live view, and replay against a file, with no radio. Files live under `mcm/data/`, are ignored by git, and a capture from radios carried by people waits on the retention rule (R-11).

---

## 5 Out-of-range gaps (A-02)

### 5.1 What a gap is

The node keeps no track memory. A radio out of range for about twenty minutes overwrites its buffer, and those positions are gone (MCM v1.1 §6.8). So a gap is not data; it is the absence of data. Gaps are shown and annotated, never interpolated. **Team answer**

**Proposed** definition, one for everyone, in `mcm/src/mcm/mesh/gaps.py`:

> A gap is two consecutive position reports from one radio whose times are more than the gap threshold apart. The threshold is `gap_factor × broadcast interval` from the radio profile (3 × 60 s = 180 s by default).

Device time is used when both reports have it; otherwise the host receive time, and the gap says which clock it used. The AAR's Q-05 and MCM's live watch must use the same threshold, or the screen and the replay will disagree about the same silence.

### 5.2 Silence is not proof of being out of range

A radio also goes quiet when its battery dies, when it is switched off, or when smart position broadcast is on and it is standing still (the firmware then sends less often). The last one would fill a replay with false gaps. The radio profile proposes smart broadcast off for that reason (**Proposed**; a trade against airtime, §6.2). A gap annotation can carry what was known at the last report: battery, SNR, hops taken.

### 5.3 The two ways to keep gaps

**Open.** Both keep the raw record stream as the source of truth. They differ in whether a gap also becomes a row.

| | (a) Derive: store nothing, find gaps from missing device times | (b) Store: the daemon writes a `gap` event (node, last heard, next heard) |
| --- | --- | --- |
| Where the gap comes from | AAR Q-05 over the position log, at replay time | `QuietNodeWatch.observe()` in the daemon, when a quiet radio is heard again |
| Rows in the store | None | One `event` row per gap (C-09 type `gap`) |
| Can it be rebuilt? | Always; it is a query | Yes, from the log, with `find_gaps`; the event is a convenience, not new information |
| Quiet-node alert on the live screen | Needs its own live check anyway | The same watcher raises the alert while the radio is quiet and closes the event when it returns |
| Threshold changed after the mission | Re-run the query | Stored events reflect the old threshold; re-derive for review |
| Risk | Live and replay code drift apart if they do not share the definition | Two sources for one fact; a daemon bug writes a wrong event that replay trusts |
| Work | AAR side | Daemon side, plus a C-09 event type |

**Owner's lean, non-definitive.** The live alert and the stored gap are separate questions. The alert is needed either way, so `QuietNodeWatch` exists in either case. For storage, (a) keeps one source of truth, and (b) adds nothing that cannot be rebuilt. The lean is (a), with the watcher's alert on the live screen, and (b) only if the replay needs gap annotations that the log cannot produce, such as a commander's note on why a radio was quiet. Settled with Corey and Elijah (AAR A-02). The code supports both.

### 5.4 Live quiet-node watch

**Proposed.** `QuietNodeWatch` keeps the last report per radio. The daemon calls `observe(record)` on every record and `quiet(now)` on a timer. `quiet` lists radios silent past the threshold by the host clock; `observe` returns the closed gap when a quiet radio is heard again. What the daemon does with either (an alert, an event, both) is its call under C-02 and A-02.

---

## 6 Sub-modules

### 6.1 Radio and gateway configuration

**Gateway.** A radio next to the laptop over USB serial. **Team answer** Implemented in `radio/gateway.py`. TCP over Wi-Fi, Bluetooth, and MQTT are laid out in MCM v1.1 §6.2; TCP is the next transport because `meshtasticd` (§6.6) speaks it. Gateway role proposed as `CLIENT_MUTE`, so the command post listens without adding rebroadcasts to the airtime budget. **Research**: confirm the role's behavior and whether the gateway needs its own GPS (MCM v1.1 §9 Q3; the answer also decides whether `rx_time_radio` is trustworthy).

**Firmware pin (C-08).** Pin every node, and the Python library, to one firmware version for the semester; record it in the repository. **Team answer** The place is `mcm/configs/radio_profile.toml`, `[firmware]`: version, library version, date pinned, board. It is empty until the team picks (MCM v1.1 §9 Q4). On connect, the gateway compares the radio's reported version with the pin and warns loudly on a mismatch or an empty pin. The `meshtastic` dependency in `mcm/pyproject.toml` is unpinned until then, on purpose. When picked: two or three latest stable releases, board support for Heltec V3, a matching library version, and no change to the position or telemetry protobufs the normalizer reads (MCM v1.1 §6.3).

**What is never in the repository.** Channel keys (PSKs). They live on the devices and in a teammate's password manager (`CLAUDE.md`).

**Provisioning.** Configuring the command post radio and provisioning field nodes over USB from the web app is the first segment stretch goal, shared with (P)MP. **Team answer** Whose code does it is **Open** (MCM v1.1 §9 Q6). The radio profile is the natural input: provisioning writes the profile's preset, interval, and role to each node.

### 6.2 Mesh behavior and the airtime math

`mesh/airtime.py` implements MCM v1.1 §6.1 and reproduces its table in a test. Time on air comes from the Semtech LoRa formula with each preset's spreading factor, bandwidth, and coding rate, and Meshtastic's 16-symbol preamble:

| Preset | SF | Bandwidth | Coding rate | Time on air, 50-byte packet |
| --- | --- | --- | --- | --- |
| SHORT_FAST | 7 | 250 kHz | 4/5 | 53 ms |
| MEDIUM_FAST | 9 | 250 kHz | 4/5 | 181 ms |
| LONG_TURBO | 11 | 500 kHz | 4/8 | 443 ms |
| LONG_FAST (default) | 11 | 250 kHz | 4/5 | 641 ms |

The node limit under the 25% line (the firmware starts to delay sends there), with three transmissions per packet:

| Interval | LONG_FAST | MEDIUM_FAST |
| --- | --- | --- |
| 60 s | 7 nodes | 27 nodes |
| 120 s | 15 nodes | 55 nodes |
| 180 s | 23 nodes | 82 nodes |
| 300 s | 39 nodes | 138 nodes |

What the table says: on the default preset at one-minute reports, the channel carries about seven radios before the firmware starts delaying. Longer intervals or a faster preset buy node count; the faster preset costs range; the interval sets how fine the AAR tracks are. Only a field test in local terrain settles the range side. **Research** These are estimates: the preset table and preamble are to be checked against the pinned firmware, the three-transmission figure is a simplification of managed flooding, and telemetry and node-info packets add load the table leaves out. `mcm airtime` prints the table for any nodes, intervals, and presets. The node limit feeds (P)MP's spacing rule. **Team answer**

Preset and interval are **Open**; the team wants the math before any decision is verified. **Team answer** The radio profile holds `LONG_FAST` and 60 s as candidates, not choices.

### 6.3 Coverage model

Where radios will and will not reach, from terrain and foliage. Core scope. **Verified** V-06. Co-owned with (P)MP: (P)MP runs it on planned positions pre-mission; MCM runs it live against current positions; same code. **Team answer** Where the pen sits is **Open** (MCM v1.1 §9 Q1).

**Proposed** interface, `coverage/model.py`: a model takes a transmitter `Site` (latitude, longitude, antenna height above ground, ground elevation) and receiver points and returns a `Link` per point: distance, path loss, received power, and a class (`covered`, `marginal`, `shadow`). An elevated node (pole, backpack antenna, drone) is just a larger antenna height. Planned and live positions are both lists of `Site`, which is what makes the same code serve both owners.

The only model today is `FreeSpaceModel`: free-space loss, no terrain, no foliage. It is an upper bound on range and exists so the interface and the validation harness have something to run. Its ranges are not to be quoted. The build order from MCM v1.1 §6.4 adds, behind the same interface: the 3DEP elevation grid (the same file (P)MP uses for contours), line of sight with antenna heights, the Fresnel zone, a per-meter foliage penalty from NLCD canopy or ESA WorldCover, diffraction loss, and a comparison with the preset's receiver sensitivity. The `geo` extra carries its dependencies when that work starts.

**Validation**, `coverage/validate.py`: for every directly heard position (§4.5), predict the link to the gateway and compare with what was heard. The v2.2 target was agreement three times in four; it is not a decision. SPLAT! and the Meshtastic Site Planner are validation targets, not the product; the Site Planner's license is to be confirmed before building on it. **Research**

Output to (P)MP as a live overlay is contract C-06, format **Open**.

### 6.4 The field message set

About 233 bytes per packet on a shared channel of about 1 kbit/s. v1 keeps stock messaging (text, waypoints), with sector assignments and out-of-range warnings if achievable. **Team answer** `messages/catalog.py` lists each message type with its direction, port, whether the stock app shows it, a size, its status, and its airtime cost:

| Message | Direction | Stock app | Size (bytes) | Status |
| --- | --- | --- | --- | --- |
| Text | Both | Yes | UTF-8 length, up to 233 | **Team answer** |
| Waypoint | CP to field | Yes | About 60, estimate | **Team answer** |
| Sector assignment | CP to field | No, custom app | About 120 for a simplified polygon, estimate | **Open** |
| Range warning | CP to field | No; a text is the stock fallback | About 12, estimate | **Open** |

What must reach the field beyond text and waypoints, and when that needs a custom app, is **Open** (MCM v1.1 §9 Q8). The phone application paths are in MCM v1.1 §6.7; battery drain from high-frequency updates drives the choice. **Team answer** Sizes marked estimate are replaced by measured encodings when a format is picked.

### 6.5 Field warnings

The three candidates (MCM v1.1 §3.7), in `field_warnings/rules.py`:

| Warning | Needs | Today |
| --- | --- | --- |
| Outside your sector | Sector polygons from (P)MP | Interface only |
| About to lose connectivity | The co-owned coverage model and the spacing rule | Interface only |
| Buffer about to overwrite | The quiet-node watch (§5.4) and the buffer length | Works: warns five minutes before the twenty-minute estimate |

Anything beyond what the stock app shows needs a custom app (§6.4), so in v1 these rules run at the command post on the live feed and can reach the field only as a text. **Team answer** The buffer length is from MCM v1.1 §6.8 and is **Research** against the pinned firmware.

### 6.6 Simulation

The hardware is stored at one member's house, so the other three depend on simulation for daily work. **Team answer** Three tiers, cheapest first (`mcm/src/mcm/sim/README.md`):

| Tier | What | Gives the others | Status |
| --- | --- | --- | --- |
| 1 | Synthetic feed: library-shaped packets through the real normalizer | JSON Lines of `RadioRecord` with gaps, relays, missing fixes, telemetry. Deterministic per seed. | Built |
| 2 | `meshtasticd`: firmware compiled for Linux as a virtual node | Real protobufs and the gateway code path over TCP | **Research** |
| 3 | Meshtasticator: discrete-event mesh simulator | Collisions, airtime, hops, placement; checks §6.2 and §5 under load | **Research** |

Tier 1 exists so the daemon, the live view, and replay can be built now. Whether tier 3 reproduces enough of the mesh is MCM v1.1 §7's open research item.

---

## 7 Package layout: `mcm/`

**Proposed.** `mcm/` follows the shape of `spm/` (pull request #4) and `aar/` (AAR Architecture v1.0 §9): a self-contained Python package with its own `pyproject.toml`, a `src/mcm/` layout, its own tests and `.gitignore`, and `claude/` and `archive/` placeholders in every folder, per the Team Claude Guide. It depends on nothing at runtime; the radio library is an optional extra.

```
mcm/
├── README.md
├── pyproject.toml                 package "mcm"; extras: dev, radio (meshtastic), geo
├── .gitignore                     captures and data are never committed
├── configs/
│   └── radio_profile.toml         firmware pin (C-08), gateway, preset, interval, gap threshold
├── docs/
│   ├── ROADMAP.md                 phases and gates (section 11)
│   └── maroonnet-mcm-architecture-v1_0.md   this document
├── data/
│   └── README.md                  synthetic/ and captures/ live here locally
├── src/mcm/
│   ├── contract/record.py         M-01: RadioRecord and JSON Lines
│   ├── radio/                     normalize.py, gateway.py, profile.py
│   ├── mesh/                      airtime.py, gaps.py
│   ├── coverage/                  model.py (interface, free-space baseline), validate.py
│   ├── messages/catalog.py        the field message set
│   ├── field_warnings/rules.py    the three warning candidates
│   ├── sim/                       synthetic.py, README.md (tiers 2 and 3)
│   └── cli.py                     mcm airtime | synth | inspect | profile
└── tests/                         fixtures/ + one file per area; no radio needed
```

Not in the package: the bridge daemon ((P)MP), the mission store (AAR), any real position data, any channel key. The package is named `field_warnings`, not `warnings`, to avoid shadowing Python's standard library module.

**What the repository still needs**, not changed by this document: the root CI runs `pytest` with `testpaths = ["backend/tests"]`, so it runs none of the segment packages' tests (AAR Architecture v1.0 §9.3 says the same). `mcm/pyproject.toml` sets its own lint config (inheriting the root rules) so `ruff check .` from the root passes on `mcm/`. Wiring segment tests into CI, the `CLAUDE.md` layout list (which asks for a line per new top-level folder), `CODEOWNERS`, and moving this document to `docs/architecture/` beside the AAR one all touch shared paths; they are listed for the team, not made here.

---

## 8 Boundary: what MCM consumes, exposes, and signs

### 8.1 Consumes

| From | What | Contract | Status |
| --- | --- | --- | --- |
| (P)MP | The daemon process that owns the `Gateway` and receives records | M-01; C-02 | **Team answer**; daemon is group-shared |
| (P)MP | Commands to the field: text, waypoints, later sectors | §4.7; C-02 | **Team answer** |
| (P)MP | Sector polygons, for the outside-sector warning | C-09 or (P)MP's sector format | **Open** |
| (P)MP | Team size and conditions, planned positions, for the coverage model | C-06 | **Open** split |
| AAR | The C-01 column names the record lines up with | C-01 draft | **Proposed** by the AAR |

### 8.2 Exposes

| To | What | Where |
| --- | --- | --- |
| Daemon | `Gateway(on_record=...)`, `open()`, `close()`, `send_text()` | `mcm.radio.gateway` |
| Daemon, AAR, everyone | `RadioRecord` and JSON Lines read and write | `mcm.contract` |
| Daemon, AAR | The gap definition: `find_gaps`, `QuietNodeWatch`, the threshold from the profile | `mcm.mesh.gaps`, `mcm.radio.profile` |
| (P)MP | The node limit for a preset and interval | `mcm.mesh.airtime.max_nodes` |
| (P)MP | The coverage model interface | `mcm.coverage.model` |
| Everyone | A synthetic radio feed | `mcm synth`, `mcm.sim.synthetic` |

### 8.3 Signs

| Contract | MCM role | Status |
| --- | --- | --- |
| M-01 Radio record | Writes. The daemon owner signs; the AAR confirms the C-01 mapping (§4.3). | Draft in this document |
| C-01 Mission store schema | Confirms the packet fields (AAR Architecture v1.0 §8.3). §4.3 is MCM's check. | Waits on the store meeting |
| C-02 Daemon message contract | Signs the parts about quiet-node alerts and outbound commands. | Waits on R-03 |
| C-06 Coverage overlay | Co-writes with (P)MP. | **Open** |
| C-08 Radio pin | Writes. `configs/radio_profile.toml`. | Waits on the firmware pick |
| C-09 Event record | Signs the `gap` type if A-02 chooses stored gaps. | Waits on A-02 |

---

## 9 Roadblocks for this segment

| # | Decision | Status | Who resolves | Blocks | Can proceed without it |
| --- | --- | --- | --- | --- | --- |
| C-08 | Firmware version pinned (MCM v1.1 §9 Q4) | **Research** | Diego with JJ | A real capture; the library pin; confirming key names in the normalizer | Everything on the synthetic feed |
| M-01 | Radio record signed | **Proposed** (§4) | Diego with Elijah; Corey confirms C-01 | The daemon's input code | The daemon can be written against the draft and the synthetic feed |
| M-02 | Fields with no C-01 column today (§4.3): columns or `decoded` JSON | **Open** | Corey with Diego | Nothing; `decoded` holds them either way | Everything |
| M-03 | Gap threshold: `gap_factor` and whether smart broadcast is off | **Proposed** (§5) | Diego with Corey | Q-05 and the live alert agreeing | Default 3 × interval |
| A-02 | Gaps: derived or stored (MCM v1.1 §9 Q5) | **Open** (§5.3) | Corey with Diego and Elijah | The `gap` event type | Derived gaps; the watcher exists either way |
| A-03 | Positions with no device time | **Research** | Corey with Diego | The time rule text in C-01 | `null`, drawn by receive time, flagged |
| M-04 | Preset and position interval | **Open**; needs a field test | Diego, then the team | Node limit; spacing rule; track detail | Candidates in the profile |
| M-05 | Coverage-model split with (P)MP (MCM v1.1 §9 Q1) | **Open** | Diego with Elijah | Who builds terrain steps; C-06 | The interface and the baseline |
| M-06 | Gateway transport beyond serial; gateway GPS (§9 Q2, Q3) | **Research** | Diego | Tier-2 simulation (TCP); trust in `rx_time_radio` | Serial and the host clock |
| M-07 | What reaches the field beyond text and waypoints (§9 Q8) | **Open** | Diego with Elijah | Custom app; sector and warning messages | Stock apps |
| M-08 | Provisioning path and whose code (§9 Q6) | **Open** | Diego with Elijah | Stretch goal 1 | Manual configuration with the CLI or app |
| R-11 | Retention rule | **Research** (AAR) | Corey | Capturing any real person's position | All synthetic and simulator work |

**What the ordering says.** C-08 comes first: a pinned firmware and one real capture turn the normalizer's hand-built fixtures into tested fact and let M-01 be signed. M-02, M-03, A-02, and A-03 are one sitting with Corey. M-04 waits on a field test. M-05 and M-07 are the (P)MP conversations.

---

## 10 Open questions

The eight from MCM v1.1 §9, with where each stands after this document, then the new ones.

| # | MCM v1.1 §9 question | Where it stands |
| --- | --- | --- |
| 1 | Where is the coverage-model split with (P)MP? | **Open** (M-05). The interface in §6.3 serves both; the split decides who builds the terrain steps. |
| 2 | A more elegant gateway transport than USB serial? | **Research** (M-06). TCP is next because simulation tier 2 needs it; MQTT stays in view for multi-gateway. |
| 3 | Does the gateway need its own GPS? | **Research** (M-06). Bears on `rx_time_radio`; the host clock is proposed as the receive time regardless. |
| 4 | Which firmware version is pinned? | **Research** (C-08). The place to record it exists; the gateway checks it on connect. |
| 5 | How are out-of-range gaps stored? | **Open** (A-02). Both options in §5.3; one shared definition; owner's lean is derived, with a live watcher. |
| 6 | What is the provisioning path, and whose code does it? | **Open** (M-08). Elijah and Diego resolve. |
| 7 | Is a ham license necessary, or only helpful? | **Research**. Not necessary for the product under Part 15 (MCM v1.1 §6.9); Part 15 and Part 97 to be confirmed against current FCC text. |
| 8 | What must reach the field beyond text and waypoints? | **Open** (M-07). The message catalog prices each candidate. |

New in this document:

9. Does the daemon accept M-01 as its input, with the `Gateway` owning the radio connection inside the daemon's process (§4.1)?
10. Is the host clock `rx_time` in C-01 (§4.4)?
11. Do the fields in §4.3's second table get columns, or stay in `decoded` (M-02)?
12. Is smart position broadcast off for missions, trading airtime for honest gaps (§5.2)?
13. Is `CLIENT_MUTE` the right gateway role (§6.1)?

---

## 11 Build order for this segment

### 11.1 What starts now, with no decision

| Work | Where | State |
| --- | --- | --- |
| M-01 record, JSON Lines, normalizer | `mcm/src/mcm/contract/`, `radio/normalize.py` | Built, tested on hand-built fixtures |
| Gateway over serial, with the pin check | `radio/gateway.py` | Built; untested against a radio |
| Airtime math reproducing MCM v1.1 §6.1 | `mesh/airtime.py` | Built, tested |
| Gap definition and live watch | `mesh/gaps.py` | Built, tested |
| Coverage interface, baseline, validation harness | `coverage/` | Built, tested |
| Message catalog; buffer-overwrite warning | `messages/`, `field_warnings/` | Built, tested |
| Synthetic feed (simulation tier 1) | `sim/synthetic.py`, `mcm synth` | Built, tested |

### 11.2 What waits, and on what

| Work | Waits on |
| --- | --- |
| Replace the fixtures with a real capture; pin the library | C-08 and one bench session |
| TCP transport and `meshtasticd` | Research; the pin |
| Daemon integration | Elijah's daemon; M-01 signed |
| Coverage terrain steps | M-05 split |
| Outside-sector and losing-connectivity warnings | Sector format from (P)MP; M-05 |
| Custom message types | M-07; the phone application path |

### 11.3 Phases

| Phase | This segment delivers | Gate |
| --- | --- | --- |
| 0 | `mcm/` package; this document at `mcm/docs/` | Pull request review |
| 1 | C-08 pinned; a real capture in the fixtures; M-01 confirmed with the daemon and C-01; A-02 and A-03 settled with Corey | M-01 signed |
| 2 | `meshtasticd` running; the daemon consumes `Gateway` records and writes the C-01 draft; quiet-node alert on the screen | A synthetic mission flows simulator to daemon to store to live view |
| 3 | Preset and interval from a field test; coverage terrain steps; validation; integration step 1 (radios to daemon to store to live view) | The vertical slice (V-11) |

---

## 12 Research the owner will do

From MCM v1.1 §7, with where this document leaves each.

| Item | What to find out | Where to look | State |
| --- | --- | --- | --- |
| Firmware version | Which stable release to pin; library match; protobuf changes | Meshtastic firmware releases and changelog; Python library release notes | Place to record it exists |
| No-fix time (A-03) | What `position.time` holds without a fix | A bench capture, with Corey | New |
| Relay node byte | Confirm `relayNode` is the low byte on the pinned version | Firmware source; a capture | New |
| Preset and interval | The node count the team needs, then the preset and interval that carry it; range in local terrain | `mcm airtime`; field test with the pole | Math built |
| Gateway | Transport; own GPS; `CLIENT_MUTE` behavior | MCM v1.1 §6.2; Meshtastic roles documentation | Serial built |
| Coverage model | The factors in MCM v1.1 §6.4; the split with (P)MP | Propagation texts; SPLAT! documentation; with Elijah | Interface built |
| Validation | Predicted against observed reception | §6.3; SPLAT!; the Site Planner (license to confirm) | Harness built |
| Field message set | What must reach the phone; size; airtime; battery | §6.4; MCM v1.1 §6.7 | Catalog built |
| Buffer length | How long a quiet radio keeps positions before overwriting | Firmware source | New |
| Simulators | Whether Meshtasticator and `meshtasticd` carry the other three's daily work | Their repositories | Tier 1 built |
| Boards and antennas | Heltec V3 against two or three alternatives | Meshtastic supported-hardware list; range reports | Unchanged |
| Ham licensing | Necessary or helpful | FCC Part 15 and Part 97 | Unchanged |
| Sweep widths | Team item; study first | MCM v1.1 §6.6 | Unchanged |

---

*MaroonNet MCM Architecture v1.0 · September 29, 2026 · Branched from MCM v1.1 §2, §3, §6, §7, §9 and AAR Architecture v1.0 §4, §6, §8, §10. Decisions are recorded in the MaroonNet Decision Log. Nothing here is decided until the log says so.*
