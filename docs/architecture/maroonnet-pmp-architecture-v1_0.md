# MaroonNet (P)MP Architecture

**Segment architecture for (Pre)Mission Planning: the command post process, the bridge daemon, the contracts (P)MP writes, the planning and map pieces, and how the `pmp/` package is laid out**

CU Denver Capstone Team: Diego Alas, Corey Greene, Elijah Heimsoth, Joshua 'JJ' Wagner

Segment architecture document, version 1.0 · Prepared by Elijah Heimsoth · September 29, 2026 · First version, branched from (P)MP v1.1 and MaroonNet Architecture v1.0. Shared for iteration.

---

## Contents

1. [Purpose and status](#1-purpose-and-status)
2. [Where (P)MP sits](#2-where-pmp-sits)
3. [Data flow in and out](#3-data-flow-in-and-out)
4. [The command post process (PM-01)](#4-the-command-post-process-pm-01)
5. [The bridge daemon (I-17)](#5-the-bridge-daemon-i-17)
6. [Contracts (P)MP writes or co-writes](#6-contracts-pmp-writes-or-co-writes)
7. [Planning, maps, and the screen](#7-planning-maps-and-the-screen)
8. [Package layout: `pmp/`](#8-package-layout-pmp)
9. [Boundary: what (P)MP consumes, exposes, and signs](#9-boundary-what-pmp-consumes-exposes-and-signs)
10. [Roadblocks for this segment](#10-roadblocks-for-this-segment)
11. [Open questions](#11-open-questions)
12. [Build order for this segment](#12-build-order-for-this-segment)
13. [Research the owner will do](#13-research-the-owner-will-do)

---

## 1 Purpose and status

This document is the architecture of one segment, (Pre)Mission Planning. It sits beside AAR Architecture v1.0 and MCM Architecture v1.0, and under MaroonNet Architecture v1.0. It answers five questions:

- How the command post process is shaped, and what stays open about it.
- What the bridge daemon takes in, writes, and pushes, and who signs off on it.
- Which contracts (P)MP writes or co-writes, and what each one waits on.
- What the planning, map, and screen pieces do, and which choices are still research.
- How the `pmp/` package is laid out so work can start.

It does not define the mission store (C-01, owned by the AAR), the probability model (SPM), or the radio record (M-01, MCM). It writes down what (P)MP does with each of them, with names chosen to line up with their drafts.

**Status labels.** Every claim carries one label.

| Label | Meaning |
| --- | --- |
| **Verified** | In the Decision Log, with its V-number. |
| **Team answer** | Stated by the owner or the team on September 17, 2026, or later in a meeting. Not yet logged. |
| **Open** | Not decided. |
| **Research** | The owner needs information before the team can decide. |
| **Proposed** | Written by this document as a starting point. Not decided. The team votes. |

Nothing in this document is decided by this document. The owner verifies; the Decision Log records. Segment codes: **SPM** (Sector Probability Mapping, Joshua 'JJ' Wagner), **(P)MP** ((Pre)Mission Planning, Elijah Heimsoth), **AAR** (After Action Report, Corey Greene), **MCM** (Mesh Connectivity Map, Diego Alas). Numbered items from other documents keep their numbers. From Architecture v1.0: I-nn integration points, C-nn contracts, R-nn roadblocks, P-nn reconciliation pull requests. From AAR Architecture v1.0: A-nn, F-nn, Q-nn. From MCM Architecture v1.0: M-nn. Items new in this document use **PM-nn**, because P-nn already names the reconciliation pull requests (Architecture v1.0 §9).

**Sources.** (P)MP v1.1; MaroonNet Architecture v1.0; Foundation v3.0 §3; AAR Architecture v1.0 (branch `feat/aar-scaffold`, pull request #5, not yet merged) and its C-01 draft `aar/src/aar/store/schema.sql`; MCM Architecture v1.0 (branch `feat/mcm-scaffold`, pull request #6, not yet merged) and its M-01 record `mcm/src/mcm/contract/record.py`; SPM v1.1 §2, §3.4, §10 and `spm/src/spm/schema.py` (branch `feat/spm-framework`, pull request #4); Decision Log v1.1; Team Claude Guide v1.0; `CLAUDE.md`; the `MaroonNet/MaroonNet` repository as of September 29, 2026. Foundation v2.2 was not used.

---

## 2 Where (P)MP sits

(P)MP is the commander's setup and the command post screen. The commander opens the application on a laptop, loads maps, enters what is known about the missing person, and starts the mission. The screen stays in use through the whole mission. **Team answer** ((P)MP v1.1 §1). This segment is the integration point of the system: the other segments feed it, and it decides how their outputs are integrated. **Team answer** The web application runs on the command post laptop; data stays local during a search. **Verified** V-10. Map and tile loading is (P)MP, not AAR. **Verified** V-13.

(P)MP holds: the web GUI, the web backend and API, the bridge daemon (group-shared, §5.6), the terrain layers and tiles, the plan (sectors, assignment, radio spacing), the call into the co-owned coverage model, and packaging. It does not hold: the mission store schema (AAR, C-01), the probability model (SPM), the radios, the gateway, and the record normalizer (MCM), or the replay views (AAR, drawn on (P)MP's screen).

```
                              COMMAND POST LAPTOP
             ┌─────────────────────────────────────────────────────────────────┐
 MCM Gateway │  bridge daemon  ──── C-01 rows ────▶  mission store             │
 ──M-01────▶ │  (pmp/daemon,           ▲             (AAR schema; engine Open) │
 RadioRecord │   group-shared)         │                     ▲                 │
      ▲      │        │ C-02 push      │ events, sectors     │ reads           │
      │      │        ▼                │ (C-09)              │                 │
 send_text,  │  web API (pmp/api) ─────┴─── planning ──── SPM model call       │
 send_waypoint      │                       (sectors,       (C-03 in,         │
 (I-09)      │      ▼                        assignment,     C-04 surface out) │
             │  browser tab: planning view · live view · AAR replay (I-18)     │
             └─────────────────────────────────────────────────────────────────┘
               terrain package on disk (C-05): tiles, elevation, land cover, trails, watersheds
               read by the map, by SPM, and by the co-owned coverage model (C-06)
```

The daemon is the only writer of packet, position, and telemetry rows during a mission. (P)MP's planning code writes events and sectors. SPM writes an artifact row for its surface. The AAR reads. **Proposed** by AAR Architecture v1.0 §5.2; one store or several is **Open** (R-01).

---

## 3 Data flow in and out

From (P)MP v1.1 §2, with the integration point and the contract named for each row.

| Direction | Data | From / to | Crosses at | Status |
| --- | --- | --- | --- | --- |
| In | Probability surface, summed per sector | SPM → (P)MP. Drawn as the heat map; the system-generated sectors use it | I-02; C-04 | **Verified** V-02 for the output; format **Proposed** by SPM |
| In | Live positions, telemetry, signal data | MCM `Gateway` → daemon → store → screen | I-08; M-01; C-01; C-02 | **Team answer** |
| In | Coverage overlay on planned positions | Co-owned model. (P)MP runs it pre-mission; MCM runs it live; same code | I-11; C-06 | **Team answer**; split **Open** (R-08) |
| In | Commander inputs: last known position and its time, or a no-known-position flag with the time elapsed; subject category; team size; conditions | Entered on the screen | C-03; I-01; I-04 | **Team answer**; category set **Open** (R-07) |
| In | Node limit for the spacing rule | MCM `mcm.mesh.airtime.max_nodes` | I-10 | **Team answer** |
| In | Quiet-node alerts and out-of-range gaps | MCM `QuietNodeWatch`, run inside the daemon → screen | I-13; A-02; C-02 | **Proposed** by MCM; storage **Open** |
| In | History layer from a past search in the area | AAR → (P)MP | I-19 | **Open**; not confirmed by the AAR owner |
| Out | Mission inputs, including the no-known-position case | (P)MP → SPM. The no-known-position case must reach the model; it is the only way to get an answer | I-01; C-03 | **Team answer** |
| Out | Sectors and assignments | To the field: waypoints and text through the stock app; sector polygons need a custom app, not v1. To the store, for AAR | I-09; C-07; C-09 | **Team answer** |
| Out | Radio spacing | Computed here from team size and radio count; sent to MCM | I-10 | **Team answer** |
| Out | Assignments, edits, overrides, messages, clues, finds, with time | The mission store, read by AAR for replay. Event marks are AAR v1 | I-16; C-09 | **Team answer** |
| Out | Terrain layer package | On disk. SPM and the coverage model read the same files | I-03; C-05 | **Open** who downloads and stores it (R-05) |
| Out | Command post radio configuration and field node provisioning | (P)MP screen → MCM radios. First segment stretch goal of both segments | I-12; M-08 | **Team answer**; path **Open** |
| Inside | Web GUI, map layers, mission input form, sector editing, command shell, packaging, measurement | (P)MP only | §7 | — |

---

## 4 The command post process (PM-01)

**Open.** Architecture v1.0 §2.3 proposes one Python process that hosts the web API, the bridge daemon, and the SPM model call, and opens one browser tab. It names this a (P)MP call with AAR input (Architecture v1.0 §10 Q1). The owner has not made the call. Both shapes are laid out here; neither is leaned on.

| | (a) One process | (b) Two processes |
| --- | --- | --- |
| What it is | `pmp serve` starts the API, runs the daemon as an asyncio task in the same event loop, calls the SPM model in-process, and opens the browser. | `pmp daemon` and `pmp api` run separately. Records cross between them on a local queue or socket. |
| What a volunteer starts | One thing. | Two things, or one launcher that starts both. |
| Packaging (PyInstaller, **Team answer**) | One binary. | Two entry points in one binary, or two binaries. |
| Who opens the mission store | One process; one connection rule. The daemon writes; the API reads. | The daemon writes. The API reads the same file, or asks the daemon. Two processes, one writer. |
| Radio side fails | Takes the screen with it unless the task is supervised and restarted. | The screen stays up; the daemon restarts alone. |
| Testing | The daemon runs alone under a test harness with no API; the API runs with a fake feed. Both are library calls. | Same, plus the queue protocol to test. |
| Live push to the screen (C-02) | The daemon appends to the API's push channel directly. | The queue protocol becomes part of C-02. |
| Fit with the framework (R-03) | Needs a framework that hosts asyncio tasks well. | Any framework; the daemon does not depend on it. |
| What it costs | A crash boundary. | Inter-process messaging and a second start path. |

What this document does about it: the daemon is written as a library (§5). Shape (a) hosts it as a task; shape (b) runs it under its own command. The stubs in `pmp/` do not change when the team decides. The owner decides with AAR input; the Decision Log records.

---

## 5 The bridge daemon (I-17)

### 5.1 What it is

The program that connects to the gateway radio, decodes each packet, writes it to the database, and pushes events to the screen. It falls under this segment and is group-shared: anything written to it is disseminated to the team, and a second person signs off before it lands, since solo work here could silently break another segment. **Team answer** ((P)MP v1.1 §3.6). Its value is the schema and the message contract; both must be written before parallel work starts ((P)MP v1.1 §3.6; Architecture v1.0 §4).

Under MCM Architecture v1.0 §4.1, steps 1 to 5 (radio, mesh, gateway, library decode, normalize) are MCM. Step 6, the callback, is the contract line. The daemon owns step 7: it creates the `Gateway`, passes its callback, and owns the process, the thread, and the store. **Proposed** by MCM. Whether the daemon accepts this split is **Open** (MCM Architecture v1.0 §10 Q9); the stub in `pmp/daemon/bridge.py` is written against it so the question can be answered with code.

### 5.2 Input: the radio record (M-01)

The daemon receives one `RadioRecord` per packet through `on_record(record)`. MCM guarantees the record's order, completeness, units, and schema string (MCM Architecture v1.0 §4.6). The daemon relies on those guarantees and adds nothing: no interpolated position, no filled-in time. A record whose `schema` string the daemon does not know is logged and skipped, never written. **Proposed**

The daemon imports nothing from `mcm` at runtime. It takes the record as a mapping and reads fields by name: the synthetic feed (`mcm synth`, JSON Lines) is already that shape, and a live `RadioRecord` becomes one at the callback with `dataclasses.asdict`. Either source looks the same to the write path. **Proposed**

### 5.3 Writes: C-01 rows

The daemon writes through the AAR's store helpers, `aar.store.db`: `ensure_node`, `insert_packet`, `insert_position`, `insert_telemetry`, `insert_event`. **Proposed** by AAR Architecture v1.0 §9.1. The mapping from record to row is by name, because MCM chose its field names to match the C-01 draft (MCM Architecture v1.0 §4.3). The draft has no helper for the `message` table yet, and its `message` row is keyed by packet, so an outbound text (no packet) has no row shape. Both are asks on pull request #5 (§11 Q15).

The daemon inserts; it never updates. This fits store shapes (a) and (b) in AAR Architecture v1.0 §5.1. Shape (c), current-state tables plus history, would put state logic into the daemon and under the second sign-off rule. The store shape is **Open** (R-04); one store or several is **Open** (R-01); the engine is **Research** (R-02).

Three clocks per position, from AAR Architecture v1.0 §4.3 and MCM Architecture v1.0 §4.4: device time (the radio's GPS, `NULL` without a fix), host receive time (`rx_time_host`, stamped by the `Gateway` at step 5 and proposed as C-01 `rx_time`), and insert order (`packet_id`). The daemon maps the second clock from the record; it never re-stamps it. **Proposed** by MCM and AAR. Whether the host clock is C-01 `rx_time` is MCM Architecture v1.0 §10 Q10 (**Open**).

### 5.4 Pushes: the daemon message contract (C-02, PM-02)

C-02 is what the daemon pushes to the screen and when. (P)MP writes it; AAR and MCM sign; it is blocked by R-03 (Architecture v1.0 §4). The transport (WebSocket, server-sent events, or polling) waits on the framework. The message list does not, so it is drafted here. **Proposed**

| Kind | When | Payload | Source |
| --- | --- | --- | --- |
| `node_seen` | A radio is heard for the first time in the mission | node number, names, hardware, first-seen time | daemon |
| `position` | A position row is written | node number, device time, receive time, lat, lon, altitude, precision bits, hops taken | daemon |
| `telemetry` | A telemetry row is written | node number, receive time, battery, voltage, channel and air utilization | daemon |
| `message` | A text packet is written, either direction | node number, direction, channel, text, time | daemon; (P)MP for outbound |
| `quiet_node` | A radio passes the quiet threshold by the host clock | node number, last heard, silent-for seconds | MCM `QuietNodeWatch` in the daemon |
| `gap` | A quiet radio is heard again | node number, last heard, next heard | MCM `QuietNodeWatch` in the daemon; stored or derived per A-02 |
| `mission` | The mission starts, pauses, or ends | mission id, state, time | (P)MP backend |

Every message carries `kind`, `time` (host clock, UTC ISO-8601 ending in `Z`), and `seq` (per daemon session, rising by one), so a screen that reconnects can ask for what it missed. **Proposed** The draft record is `pmp/src/pmp/contract/messages.py`. Whether the same push feeds the live view and replay from one timeline is A-01, with AAR (**Open**).

### 5.5 Outbound: commands to the field

The daemon calls `Gateway.send_text(text, channel, dest)` for commands from (P)MP; waypoints and, later, custom message types follow the same path. The gateway refuses a message that does not fit one packet. Outbound sends are recorded by the daemon as `message` rows with `direction = out`. **Proposed** by MCM Architecture v1.0 §4.7. The C-01 draft keys `message` rows by packet, so the outbound row shape is an ask on pull request #5 (§11 Q15). What v1 sends and what it costs in airtime is C-07 (MCM writes, (P)MP signs). Sector polygons need a custom app and are not v1 (I-09). **Team answer**

### 5.6 Group-shared code

Rule, from (P)MP v1.1 §3.6: a second person signs off before anything lands in the daemon. In git terms, from Architecture v1.0 §5.3: the pull request carries an approval from an owner of another segment, in addition to the ruleset's two approvals. Architecture v1.0 §5.2 proposes CODEOWNERS lines for this. With the `src/` layout the other three packages use, the lines are:

```
/pmp/                     @heimsothe
/pmp/src/pmp/daemon/      @heimsothe @coreybbgreene @alasdiego     # group-shared: second sign-off
```

**Proposed.** `CODEOWNERS` is Corey's file (`/.github/`), so the lines are listed here and in the pull request body for P-05, not changed by this segment.

---

## 6 Contracts (P)MP writes or co-writes

From Architecture v1.0 §4. A contract is a file in the repository that two or more owners sign off on. The proposed home is `shared/contracts/` (P-08, Corey). Until that folder exists, (P)MP's drafts live in `pmp/src/pmp/contract/` and `pmp/src/pmp/maps/package.py`, the way MCM keeps M-01 in `mcm/contract/`. They move when P-08 lands. **Proposed**

| # | Contract | (P)MP role | Others | Blocked by | Draft |
| --- | --- | --- | --- | --- | --- |
| C-02 | Daemon message contract | Writes | AAR and MCM sign | R-03 | §5.4; `contract/messages.py` |
| C-03 | Mission input record and category set | Co-writes with SPM | — | R-07 | §6.1; `contract/mission_input.py` |
| C-05 | Terrain layer package | Writes | SPM and MCM sign | R-05, R-06 | §6.2; `maps/package.py` |
| C-06 | Coverage model interface | Co-writes with MCM | — | R-08 | §6.3; `planning/coverage.py` calls `mcm.coverage.model` |
| C-09 | Event record | Writes | AAR signs | C-01 | §6.4; `contract/events.py` |
| C-01 | Mission store schema | Signs | AAR writes; SPM signs; MCM confirms fields | R-01, R-02, R-04 | AAR's `schema.sql`; §11 Q8, Q15 |
| C-04 | Probability surface format | Signs | SPM writes; AAR signs | R-01 | SPM's `Prediction` |
| C-07 | Field message set | Signs | MCM writes | none | MCM's `messages/catalog.py` |
| C-08 | Radio configuration record | Signs | MCM writes | R-09 | MCM's `configs/radio_profile.toml` |

### 6.1 C-03: the mission input record (PM-03)

What the commander enters, as one typed record that SPM accepts. **Team answer** on the fields ((P)MP v1.1 §3.3); the exact values are **Open** (R-07).

| Field | Meaning | Status |
| --- | --- | --- |
| `mission_id`, `entered_at` | Which mission; when the form was submitted, host clock | **Proposed** |
| `lkp` (lat, lon), `lkp_time`, `lkp_kind` | Last known position and its time; kind is point last seen, last known point, or route, in SPM's `ipp_type` terms | **Team answer** for the position and time; kind **Proposed** |
| `no_known_position`, `elapsed_h` | The no-known-position case, with hours since the person was last known. Required, not optional; it is the only way to get an answer | **Team answer** |
| `subject_category` | One value from the agreed set. More than child and adult; group, disabled, infirm, and dog were raised as identifiers | **Team answer** that more values are needed; the set is **Open** (R-07, I-04) |
| `subject_identifiers` | Extra flags on the subject (group, disabled, infirm, dog) until the set says whether they are categories or flags | **Open** |
| `team_size`, `radio_count` | The searchers and the radios available. Drives radio spacing (§7.4). Whether the model uses team size is for SPM to say | **Team answer** that team size is an input |
| `conditions` | Weather and hazards; stretch with SPM | **Team answer**, stretch |

Mapping to SPM's `Case` (`spm/src/spm/schema.py`): `lkp` → `ipp` (`None` for no known position); `lkp_kind` → `ipp_type`; `subject_category` → `category`; `elapsed_h` → `elapsed_h`; the group identifier may map to `party_size`. **Proposed**; JJ confirms. The category values come from ISRID's definitions (SPM v1.1 §7; (P)MP v1.1 §7). **Research**, Elijah and JJ.

### 6.2 C-05: the terrain layer package (PM-04)

The files a mission region needs on disk, from (P)MP v1.1 §6.4. The map draws them; SPM reads elevation and land cover for its terrain factors; the coverage model reads elevation and land cover for line of sight and foliage. The commander downloads the region before the mission, while connected; maps are not pre-built. **Team answer** ((P)MP v1.1 §3.1). Which layers, and where to source them, is **Research** ((P)MP v1.1 §3.1); the pipeline in §6.4 of that document is a primer, not a decision. Contents and location here are **Proposed**.

| Layer | Source | Form on disk | Made by |
| --- | --- | --- | --- |
| Base map: roads, trails, water, place names | OpenStreetMap extract (Geofabrik) | One vector tile file, PMTiles or MBTiles | Planetiler, one run per region |
| Elevation | USGS 3DEP, 10 m or 30 m | GeoTIFF; contours or hillshade derived | Download; derive |
| Land cover | NLCD (US) or ESA WorldCover | GeoTIFF | Download |
| Trails and roads as features | OpenStreetMap; NPS trails where they exist | GeoJSON or GeoPackage | Extract |
| Watersheds | USGS WBD | GeoJSON or GeoPackage | Download |

The package carries a manifest: region name and bounding box, the coordinate reference system, cell size, one entry per file with format, checksum, source, and produced-at time. SPM's `Window` works in the local UTM zone (EPSG:32613 for Colorado); the manifest records the zone so the map, the model, and the coverage grid line up. **Proposed** A select-a-region step at first run limits the download to what the commander needs; a statewide build takes hours ((P)MP v1.1 §6.4). **Proposed**

Which segment downloads and stores the package is **Open** (R-05, Elijah and JJ). The region for the fall slice follows the reference case SPM picks (R-06, I-05). Where the package lives on disk, and how a copied mission finds it for an AAR on another machine, is A-04 (**Open**, with Corey).

### 6.3 C-06: the coverage model interface

Co-owned. (P)MP runs the model on planned positions pre-mission; MCM runs it live against current positions; same code. **Team answer** (MCM v1.1 §3.3). MCM Architecture v1.0 §6.3 gives the interface a home, `mcm.coverage.model`, with a free-space baseline whose ranges are not to be quoted. (P)MP's side is a caller: `pmp/planning/coverage.py` takes planned radio positions and the terrain package and asks the interface for per-cell classes. **Proposed** Where the pen sits for the terrain steps (elevation grid, line of sight, Fresnel zone, foliage loss) is **Open** (R-08, M-05; Elijah and Diego). The output format to the screen is **Open** (C-06 format, MCM Architecture v1.0 §6.3).

### 6.4 C-09: the event record

(P)MP writes; AAR signs; blocked by C-01. The AAR proposed a list in AAR Architecture v1.0 §6.3: `assignment`, `edit`, `override`, `message`, `clue`, `find`, `gap`, `mission`, `note`. Whether that list is the right set for C-09 is **Open**; the owner answers on pull request #5 (§11 Q7). `pmp/src/pmp/contract/events.py` mirrors the list, marked draft, so the daemon and the planning code have a name for each type while the question is open.

An override stores what the system proposed, what the commander did instead, the time, and a short reason if given. **Team answer** ((P)MP v1.1 §6.5). The measurement the team wants, time from case entry to first team dispatch ((P)MP v1.1 §3.8), is a query over these events: from the `mission` started event to the first `assignment` event. No separate log is needed (PM-05). **Proposed**

---

## 7 Planning, maps, and the screen

### 7.1 Mission inputs and the form

The form collects C-03 (§6.1). It pings SPM; the heat map returns to the screen. **Team answer** Which fields the form needs so SPM gets what it needs is **Research** with the SPM owner ((P)MP v1.1 §7).

### 7.2 Sectors

System-generated sectors, split along ridgelines, drainages, trails, and roads, which the commander can edit. Manual sector creation, and dragging a line to split a sector, are both wanted. **Team answer** ((P)MP v1.1 §3.5). Terrain is a planning input as well as a radio one: dense forest and elevation change cut Meshtastic range. **Team answer** A redraw is a new `sector` row version, never an update, in the C-01 draft (**Proposed** by AAR). Ranking of sectors is stretched with continuous update; the SPM heat map already carries the information (I-06). **Team answer** Sweep widths and coverage rates are a team item (I-14). **Team answer** How to split along terrain breaks, and sector size per operational period, is **Research** (§13).

### 7.3 Assignment

Radio to person to team to sector. The team assumes one radio per person but does not know how SAR teams structure themselves; prepare for both: pair a radio to a named searcher and to a team. **Team answer** ((P)MP v1.1 §3.4). An assignment is a C-09 event with node, team, person label, sector, and start or end. AAR Architecture v1.0 A-06 proposes no person-name column on the `node` table; the label lives in the assignment event payload. **Proposed** by AAR.

### 7.4 Radio spacing

Computed here from team size and radio count; sent to MCM to work in tandem. **Team answer** ((P)MP v1.1 §3.5). The MCM node limit for a preset and interval, `mcm.mesh.airtime.max_nodes`, feeds the rule (I-10). Sweep widths stay parked (I-14). `pmp/planning/spacing.py` is the stub.

### 7.5 The terrain package and the region step

§6.2. A Planetiler run on one small region is work the owner can start with no decision (Architecture v1.0 §7.2). `pmp/maps/region.py` is the stub for the select-a-region step and the build.

### 7.6 The screen

Browser tab, served by the backend, is the lean; Electron stays in the comparison for information; Tauri is out. **Team answer** ((P)MP v1.1 §3.7). Figures for disk and memory are typical, not measured; measure on the team's laptops before deciding ((P)MP v1.1 §6.3). **Research** One screen hosts planning, the live view, and AAR replay (I-18). Architecture v1.0 §5.1 puts `pmp/web/` and `aar/web/` in the same frontend build, with the build config in `pmp/web/`. Where the replay UI lives in the tree is A-05 (**Open**, Corey with Elijah; PM-06 here). Whether replay scrubs against server time-T queries or a bundle in the browser is A-01 (**Open**, after R-10).

### 7.7 Backend framework (R-03)

Flask, Django, or FastAPI. No lean. **Team answer** The owner has dabbled in Flask and Django and has not explored FastAPI; he researches and recommends ((P)MP v1.1 §4). **Research** The bake-off: build the same two endpoints, one REST and one WebSocket, in each framework and compare the code; a day of work settles it ((P)MP v1.1 §6.2). Results land in `docs/research/pmp/` (Architecture v1.0 §7.2). C-02's transport, the API surface, and the daemon's push to the screen wait on it. The daemon's radio intake and decode do not.

### 7.8 Map library (R-10)

React (JavaScript or TypeScript) with MapLibre GL JS is the lean, with full comparisons requested against Leaflet and OpenLayers. **Team answer** ((P)MP v1.1 §4). **Research** What the comparison must cover, from (P)MP v1.1 §7 and AAR Architecture v1.0 §7: offline vector tiles (PMTiles or MBTiles) with no server; a large raster overlay (the heat map); time-filtered layers for replay; drawing and editing polygons for sectors; layer toggles. The GUI, the AAR replay layers, and the charting library wait on it. The backend, the models, and the store do not.

### 7.9 Backend language (R-13)

Python. The owner sees no reason to deviate, since the other segments are built on it, but wants the case for Node laid out. **Team answer** ((P)MP v1.1 §4, §6.1). U-02, leaning. All current segment code is Python. The Python-against-Node note is work the owner can start now; it lands in `docs/research/pmp/`.

### 7.10 Packaging

PyInstaller accepted. **Team answer** ((P)MP v1.1 §3.7). AAR Architecture v1.0 §5.3 reads this as one binary; how many entry points it has is PM-01 (§4).

### 7.11 Measurement (PM-05)

Log the time from case entry to first team dispatch; log as much as feasible. **Team answer** ((P)MP v1.1 §3.8). §6.4: a query over C-09 events. Commander overrides are the second measurement; they show whether the proposals are trusted, and they give AAR an event to show on the timeline.

### 7.12 Export

Not a separate application. Lives in this web app as zipping and packaging, with scrubbing as the stretch goal. **Team answer** ((P)MP v1.1 §4). Whether a separate export file format is needed at all is **Research** (R-15, U-03; Corey and Elijah). Not in the fall slice.

---

## 8 Package layout: `pmp/`

**Proposed.** `pmp/` follows the shape of `spm/` (pull request #4), `aar/` (pull request #5), and `mcm/` (pull request #6): a self-contained Python package with its own `pyproject.toml`, a `src/pmp/` layout, its own tests and `.gitignore`, and `claude/` and `archive/` placeholders in every folder, per the Team Claude Guide §3.3. Its subpackages follow Architecture v1.0 §5.1 (`api`, `daemon`, `planning`, `maps`, `web`), plus `contract/` in the shape of `mcm/contract/`. It depends on nothing at runtime.

Phase 0 is stubs. Every module imports. Each carries a docstring that names its purpose and the item it serves. Functions and classes carry their signatures and raise `NotImplementedError`. The contract records are typed dataclasses with validation and serialization only. One test imports everything; one test round-trips the contract records.

```
pmp/
├── README.md                     what (P)MP is, what exists now, quick start, layout
├── pyproject.toml                package "pmp"; no runtime dependencies; extras: dev, geo
├── .gitignore                    data/ and missions/ are never committed
├── docs/
│   └── ROADMAP.md                phases and gates (section 12)
├── data/
│   └── README.md                 terrain packages and mission stores live here locally
├── web/
│   └── README.md                 frontend placeholder; R-10 and A-05 decide what goes here
├── src/pmp/
│   ├── __init__.py               version, segment code
│   ├── cli.py                    pmp status: prints the stub inventory and the open items
│   ├── contract/
│   │   ├── messages.py           C-02 draft: DaemonMessage and its kinds (section 5.4)
│   │   ├── mission_input.py      C-03 draft: MissionInput (section 6.1)
│   │   └── events.py             C-09 draft: (P)MP's side; mirrors AAR section 6.3, marked Open
│   ├── daemon/
│   │   ├── bridge.py             Bridge: on_record(record); run() as an asyncio coroutine
│   │   └── outbound.py           send_text, send_waypoint through MCM's Gateway
│   ├── api/
│   │   └── surface.py            the endpoints and pushes the screen needs, framework-neutral
│   ├── planning/
│   │   ├── sectors.py            system-generated sectors; edit, split, merge
│   │   ├── assignment.py         radio to person to team to sector
│   │   ├── spacing.py            radio spacing from team size and the MCM node limit
│   │   └── coverage.py           calls the co-owned mcm.coverage interface (C-06)
│   └── maps/
│       ├── package.py            C-05 draft: TerrainPackage manifest (section 6.2)
│       └── region.py             the select-a-region step; the Planetiler run
└── tests/
    ├── test_imports.py           every module imports; every stub raises NotImplementedError
    └── test_contracts.py         the contract records round-trip through dict and JSON
```

Not in the package: the mission store schema (AAR), the probability model (SPM), the radios and the `Gateway` (MCM), any frontend code, any real position data.

**What the repository still needs**, not changed by this document:

- The `pmp/` line in the `CLAUDE.md` layout list (P-03). Pull request #4 already edits that file, so this segment does not.
- The CODEOWNERS lines in §5.6 (P-05).
- Root `pyproject.toml` `testpaths` still points at `backend/tests`, so root CI runs none of the segment tests (P-01). AAR Architecture v1.0 §9.3 and MCM Architecture v1.0 §7 say the same.
- `shared/contracts/` (P-08).

`pmp/pyproject.toml` extends the root ruff rules so `ruff check .` from the root passes on `pmp/`.

---

## 9 Boundary: what (P)MP consumes, exposes, and signs

### 9.1 Consumes

| From | What | Contract | Status |
| --- | --- | --- | --- |
| MCM | `RadioRecord`, one per packet, through `on_record` | M-01 | **Proposed** by MCM; daemon acceptance **Open** |
| MCM | `Gateway(on_record=...)`, `open()`, `close()`, `send_text()` | §5.5; C-07 | **Proposed** by MCM |
| MCM | The node limit for a preset and interval | I-10; `mcm.mesh.airtime.max_nodes` | **Team answer** |
| MCM | The coverage model interface and baseline | C-06; `mcm.coverage.model` | Co-owned; split **Open** |
| MCM | The gap definition and `QuietNodeWatch` | A-02; `mcm.mesh.gaps` | **Proposed** by MCM |
| MCM | Simulators and the synthetic feed | I-15; `mcm synth` | **Team answer** |
| SPM | The probability surface and its per-sector table | I-02; C-04; `spm.schema.Prediction` | **Verified** V-02 output; format **Proposed** by SPM |
| SPM | The reference case and its region | I-05; R-06 | **Team answer**; case not chosen |
| AAR | The store helpers the daemon writes through | C-01; `aar.store.db` | **Proposed** by AAR |
| AAR | The history layer for the next search | I-19 | **Open** |

### 9.2 Exposes

| To | What | Where |
| --- | --- | --- |
| SPM | The mission input record and the category set | C-03; `pmp.contract.mission_input` |
| SPM, MCM | The terrain layer package and its manifest | C-05; `pmp.maps.package` |
| AAR | Events with time: assignments, edits, overrides, messages, clues, finds | C-09; `pmp.contract.events` |
| AAR | The daemon that writes the store | I-17; `pmp.daemon.bridge` |
| AAR | The screen, the map library, and the frontend build | I-18; `pmp/web/` |
| AAR, MCM | The daemon's screen messages | C-02; `pmp.contract.messages` |
| MCM | Sectors, waypoints, text outbound | I-09; `pmp.daemon.outbound` |
| MCM | Radio spacing | I-10; `pmp.planning.spacing` |
| MCM | Planned positions for the coverage model | I-11; `pmp.planning.coverage` |
| Everyone | `pmp status` | `pmp.cli` |

### 9.3 Signs

| Contract | (P)MP role | Status |
| --- | --- | --- |
| C-02 Daemon message contract | Writes. AAR and MCM sign. | Draft in §5.4; transport waits on R-03 |
| C-03 Mission input record | Co-writes with SPM. | Draft in §6.1; values wait on R-07 |
| C-05 Terrain layer package | Writes. SPM and MCM sign. | Draft in §6.2; waits on R-05, R-06 |
| C-06 Coverage model interface | Co-writes with MCM. | Caller stub; split waits on R-08 |
| C-09 Event record | Writes. AAR signs. | AAR's list mirrored; **Open** |
| C-01 Mission store schema | Signs. | Waits on the store meeting (R-01, R-02, R-04) |
| C-04 Probability surface format | Signs. | Waits on R-01 |
| C-07 Field message set | Signs. | MCM's catalog exists |
| C-08 Radio configuration record | Signs. | Waits on the firmware pick (R-09) |
| M-01 Radio record | Signs as the daemon owner. | **Open** (§11 Q9) |

---

## 10 Roadblocks for this segment

| # | Decision | Status | Who resolves | Blocks | Can proceed without it |
| --- | --- | --- | --- | --- | --- |
| R-03 | Backend framework: Flask, Django, or FastAPI | **Research** | Elijah | C-02 transport; the API; the daemon's push; the WebSocket layer | The daemon's intake and writes; planning code; the terrain package |
| R-10 | Map library: MapLibre GL JS, Leaflet, OpenLayers | **Research**; React with MapLibre is the lean | Elijah | The GUI; AAR replay layers (I-18); charting; A-05; A-01 | Everything server-side |
| PM-01 | One process or two on the command post (§4) | **Open** | Elijah with Corey | Packaging entry points; who opens the store; C-02 transport | The daemon as a library; every stub |
| R-07 | Subject category identifier set | **Open** | Elijah and JJ | C-03 values; the input form; the model's category dimension | C-03 with a placeholder set |
| R-05 | Which segment downloads and stores the terrain layers | **Open** | Elijah and JJ | C-05 ownership; SPM terrain factors; coverage elevation input | The manifest; a Planetiler run on one region |
| R-06 | Reference case and its region | **Team answer** that one case sets the region; case not chosen | JJ finds; team agrees | Which region gets tiles built; the slice's map | Everything not tied to a region |
| R-08 | Coverage model split with MCM (M-05) | **Open** | Elijah and Diego | C-06; who builds the terrain steps | The caller stub; MCM's interface and baseline |
| PM-02 | C-02 message list (§5.4) | **Proposed** | Elijah; Corey and Diego sign | The push side of the daemon | The write side of the daemon |
| PM-03 | C-03 field list and the `Case` mapping (§6.1) | **Proposed** | Elijah with JJ | The input form; SPM's intake | Placeholder categories |
| PM-04 | C-05 contents, manifest, and on-disk location (§6.2) | **Proposed** | Elijah; JJ and Diego sign | The map; SPM terrain stacks; coverage inputs | One region built by hand |
| PM-05 | Dispatch-time and override measurement as C-09 queries (§6.4, §7.11) | **Proposed** | Elijah with Corey | Nothing | Everything |
| PM-06 | Where the replay UI lives in the frontend build (A-05) | **Open** | Elijah with Corey | The frontend build layout | The backend side of both segments |
| M-01 | The daemon accepts the radio record at step 6 | **Open** (MCM Architecture v1.0 §10 Q9) | Elijah with Diego | M-01 signed; the daemon's input code | The daemon written against the draft and the synthetic feed |
| M-08 | Provisioning path and whose code | **Open** | Elijah and Diego | Stretch goal 1 | Manual configuration with the CLI or app |
| R-13 | Python as the backend language | U-02, leaning | Segment owners | Nothing in practice | All current work |
| R-15 | Export: where it lives, whether a format is needed | U-03 | Corey and Elijah | Nothing in the fall slice | Everything |
| R-11 | Retention rule | **Research** (AAR) | Corey | Storing any real person's position | All synthetic and simulator work |

**What the ordering says.** R-03 and R-10 are the owner's two research items and gate the most on this segment; the bake-off and the map comparison come first. PM-01 is one conversation with Corey and can close in the same sitting as the store meeting. R-07 and R-05 are one conversation with JJ; R-08 and M-01 are one with Diego. Everything below the line proceeds against drafts.

---

## 11 Open questions

The six from (P)MP v1.1 §9, with where each stands after this document, then the new ones.

| # | (P)MP v1.1 §9 question | Where it stands |
| --- | --- | --- |
| 1 | Where is the split in the coverage model between this segment and MCM? | **Open** (R-08, M-05). MCM's interface serves both; (P)MP is a caller until the split says who builds the terrain steps (§6.3). |
| 2 | Which database does this segment write to, and is it the same store AAR reads? | **Open** (R-01, R-02). The AAR proposes one mission file with a table group per segment (AAR Architecture v1.0 §5.2); the daemon writes through the AAR's helpers either way (§5.3). |
| 3 | What is the provisioning path, and whose code does it? | **Open** (M-08). Elijah and Diego resolve. Stretch goal 1. |
| 4 | Which subject-category identifiers does SPM need? | **Open** (R-07). The C-03 draft carries the raised identifiers as flags until the set is agreed (§6.1). |
| 5 | The slice region follows the historical case SPM picks. Who builds its tiles? | **Open** (R-05). The manifest and the region step are drafted (§6.2). |
| 6 | Is a separate export file format needed at all? | **Research** (R-15, U-03). Not in the fall slice. |

New in this document:

7. Is the AAR's event list in AAR Architecture v1.0 §6.3 the right set for C-09? The owner answers on pull request #5. **Open**
8. Is one mission file, with a table group per segment and the AAR writing C-01 (AAR Architecture v1.0 §5.2), acceptable as the proposal to vote on? The owner answers on pull request #5. **Open**
9. Does the daemon accept M-01 as its input, with the `Gateway` owning the radio connection inside the daemon's process (MCM Architecture v1.0 §4.1, §10 Q9)? **Open**
10. One process or two on the command post (§4)? **Open**; PM-01.
11. Which transport carries C-02 to the screen, once R-03 is settled (§5.4)? **Open**
12. Does the same push feed the live view and replay from one timeline (A-01)? **Open**, with Corey, after R-10.
13. Is `team_size` a model input SPM uses, or only a spacing input (§6.1)? JJ answers. **Open**
14. Where does the terrain package live on disk, and how does a copied mission find it (A-04)? **Open**, with Corey.
15. The C-01 draft has no `insert_message` helper, and its `message` row is keyed by packet. What is the row shape for an outbound text with no packet (§5.3, §5.5)? Ask on pull request #5. **Open**

---

## 12 Build order for this segment

### 12.1 What starts now, with no decision

| Work | Where | State |
| --- | --- | --- |
| The C-02, C-03, and C-09 drafts as typed records | `contract/` | Stubs; records defined |
| The daemon's intake against MCM's synthetic feed, writing the C-01 draft through `aar.store.db` | `daemon/bridge.py` | Stub; signatures only |
| The terrain package manifest and a Planetiler run on one small region | `maps/` | Stub; run not started |
| The framework bake-off (R-03) and the Python-against-Node note (R-13) | `docs/research/pmp/` | Not started |
| The map library comparison (R-10) | `docs/research/pmp/` | Not started |
| The node-limit check for a plan: team size and radio count against MCM's `max_nodes` | `planning/spacing.py` | Stub; the spacing distance waits (§12.2) |

### 12.2 What waits, and on what

| Work | Waits on |
| --- | --- |
| The API surface and the C-02 transport | R-03 |
| The planning view, the live view, and the replay home in the build | R-10; A-05 (PM-06) |
| The input form's category values | R-07 with JJ |
| Sector generation along terrain breaks | The terrain package for the R-06 region; the sector research (§13) |
| The coverage overlay on the map | C-06 split (R-08); C-05 elevation and land cover |
| The daemon on real radios | C-08 pin (Diego); R-11 before any real person |
| Provisioning from the web app | M-08; stretch |

### 12.3 Phases

| Phase | This segment delivers | Gate |
| --- | --- | --- |
| 0 | `pmp/` folders, docs, and stubs; this document at `docs/architecture/` | Pull request review |
| 1 | C-03 with JJ; the C-05 draft and one region built; C-06 caller agreed with Diego; C-02 list agreed; the bake-off and the map comparison written up in `docs/research/pmp/`; PM-01 settled with Corey | R-03 and R-10 decided by the team; C-01 signed |
| 2 | The daemon consumes the synthetic feed and writes the C-01 draft; the API surface in the chosen framework; the planning view in `pmp/web/`; the terrain package for the R-06 region; radio spacing | Integration step 1 of Architecture v1.0 §7.1: daemon to store to live view |
| 3 | Inputs to SPM to heat map (step 2); the coverage overlay on the map (step 4); sectors and assignments on the screen; events to the store for replay | The vertical slice (V-11) |
| Later | Provisioning (I-12, M-08); export (R-15); ranking (I-06); the history layer (I-19); scrubbing of the export | Stretch goals, (P)MP v1.1 §8 |

---

## 13 Research the owner will do

From (P)MP v1.1 §7, with where each result lands.

| Item | What to find out | Where to look | Lands in |
| --- | --- | --- | --- |
| Backend framework (R-03) | The same two endpoints in Flask, Django, FastAPI; WebSocket and asyncio fit; code compared | (P)MP v1.1 §6.2; each framework's documentation | `docs/research/pmp/`; then `pmp/api/` |
| Map library (R-10) | MapLibre GL JS, Leaflet, OpenLayers: offline vector tiles, large overlays, time-filtered layers, polygon editing | Library documentation; (P)MP v1.1 §4 | `docs/research/pmp/`; then `pmp/web/` |
| Command shell | Confirm the browser-tab lean with measured memory and disk on the team's laptops | (P)MP v1.1 §6.3 | `docs/research/pmp/` |
| Map layers and sources (C-05) | Which layers a commander needs; how to package a region; a Planetiler run | (P)MP v1.1 §6.4; Planetiler, PMTiles, USGS, MRLC, Geofabrik documentation | `pmp/maps/`; §6.2 |
| Sector generation | How to split along terrain breaks; sector size per operational period | SAR planning manuals; CalTopo's segment tools as reference | `pmp/planning/sectors.py` |
| Subject category identifiers (R-07) | Which fields the form needs so SPM gets what it needs | With the SPM owner; ISRID category definitions | C-03 |
| Team structure | How SAR teams assign people and radios | SAR team outreach; NASAR field guides | `pmp/planning/assignment.py`; `docs/research/` |
| Commander needs | What is on the screen during a mission | CalTopo and SARTopo walkthroughs; SAR team outreach | `pmp/web/`; `docs/research/` |
| Export (R-15) | Whether a separate export file format is needed at all | SAR team outreach | Decision Log, with Corey |
| Provisioning path (M-08) | The most seamless way to configure the command post radio and provision field nodes from the web app | With the MCM owner; Meshtastic Python library | With Diego; stretch |
| Python against Node (R-13) | The case for Node, laid out for the team | (P)MP v1.1 §6.1 | `docs/research/pmp/` |

Anything about how real teams operate must trace to `docs/research/` or an outreach conversation logged in `docs/outreach/` (`CLAUDE.md`). Nothing in this document invents an operational requirement; where the team assumed one, the row says Research.

---

*MaroonNet (P)MP Architecture v1.0 · September 29, 2026 · Branched from (P)MP v1.1 §2, §3, §4, §6, §7, §9 and MaroonNet Architecture v1.0 §2, §3, §4, §5, §6, §7, with AAR Architecture v1.0 §5, §6, §8 and MCM Architecture v1.0 §4, §6, §8 as sources. Decisions are recorded in the MaroonNet Decision Log. Nothing here is decided until the log says so.*
