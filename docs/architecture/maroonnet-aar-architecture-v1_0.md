# MaroonNet AAR Architecture

**Segment architecture for the After Action Report: what the commander sees in replay, what the mission store must answer, how the store can be shaped, and how the `aar/` package is laid out**

CU Denver Capstone Team: Diego Alas, Corey Greene, Elijah Heimsoth, Joshua 'JJ' Wagner

Segment architecture document, version 1.0 · Prepared by Corey Greene · September 28, 2026 · First version, branched from AAR v1.1 and MaroonNet Architecture v1.0. Shared for iteration.

---

## Contents

1. [Purpose and status](#1-purpose-and-status)
2. [What the commander sees](#2-what-the-commander-sees)
3. [What replay asks of the store](#3-what-replay-asks-of-the-store)
4. [Requirements the store must meet](#4-requirements-the-store-must-meet)
5. [Mission store: shape, stores, engine, lifecycle](#5-mission-store-shape-stores-engine-lifecycle)
6. [Schema draft (C-01 draft)](#6-schema-draft-c-01-draft)
7. [Replay: where the scrubbing happens, and drawing rules](#7-replay-where-the-scrubbing-happens-and-drawing-rules)
8. [Boundary: what the AAR exposes, consumes, and signs](#8-boundary-what-the-aar-exposes-consumes-and-signs)
9. [Package layout: `aar/`](#9-package-layout-aar)
10. [Roadblocks for this segment](#10-roadblocks-for-this-segment)
11. [Build order for this segment](#11-build-order-for-this-segment)
12. [Research the owner will do](#12-research-the-owner-will-do)
13. [Open questions](#13-open-questions)

---

## 1 Purpose and status

This document is the architecture of one segment, the After Action Report. It sits under MaroonNet Architecture v1.0, which covers the whole system. It answers five questions:

- What the commander does with the replay, in the commander's terms.
- What questions the replay asks of the mission store.
- What the mission store must do, and which shapes can do it.
- Where the AAR meets the other three segments, and what it must sign.
- How the `aar/` package is laid out so work can start.

**Status labels.** Every claim carries one label.

| Label | Meaning |
| --- | --- |
| **Verified** | In the Decision Log, with its V-number. |
| **Team answer** | Stated by the owner or the team on September 17, 2026, or later in a meeting. Not yet logged. |
| **Open** | Not decided. |
| **Research** | The owner needs information before the team can decide. |
| **Proposed** | Written by this document as a starting point. Not decided. The team votes. |

Nothing in this document is decided by this document. The owner verifies; the Decision Log records. Segment codes: **SPM** (Sector Probability Mapping, Joshua 'JJ' Wagner), **(P)MP** ((Pre)Mission Planning, Elijah Heimsoth), **AAR** (After Action Report, Corey Greene), **MCM** (Mesh Connectivity Map, Diego Alas). Cross-document references name the document, version, and section: "AAR v1.1 §6.3". Numbered items from Architecture v1.0 keep their numbers here: I-nn integration points, C-nn contracts, R-nn roadblocks. Items new in this document use F-nn (replay features), Q-nn (replay questions), and A-nn (AAR roadblocks).

**Sources.** AAR v1.1; MaroonNet Architecture v1.0; Foundation v3.0 §6; MCM v1.1 §2, §3.2, §6.1, §6.8; (P)MP v1.1 §2, §3.6, §3.8, §4, §6.5; SPM v1.1 §2, §10; Decision Log v1.1; Team Claude Guide v1.0; the `maroonnet/maroonnet` repository as of September 28, 2026, including pull request #4 (`spm/`). Foundation v2.2 was not used.

---

## 2 What the commander sees

The After Action Report is the mission, replayed. It is interactive data, not an exported video. **Verified** V-03. It has no pre-mission role. **Verified** V-13.

The screen, as the owner describes it: a map with a point overlay. Each radio is a point. The point leaves a trail as time moves. A time slider sits along the bottom. A filter panel sits on one side. The commander jogs, scrolls, steps, and moves through time and watches how the searchers moved. **Team answer**

| # | Feature | Version | Status | Where |
| --- | --- | --- | --- | --- |
| F-01 | Scrub, pause, step through the mission | v1 | **Team answer** | AAR v1.1 §3.2 |
| F-02 | Fast-forward by tapping or holding the right arrow | v1, possible | **Team answer** | AAR v1.1 §3.2 |
| F-03 | Each radio's path drawn as a line; lines can be highlighted and clicked | v1 | **Team answer** | AAR v1.1 §3.2 |
| F-04 | Select or deselect searchers to add or remove them from the map; show only their paths | v1 | **Team answer** | AAR v1.1 §3.3 |
| F-05 | Events on the timeline: assignments, edits, overrides, messages, clues, finds | v1 | **Team answer** | AAR v1.1 §3.2; (P)MP v1.1 §6.5 |
| F-06 | Layer toggles: probability surface, coverage, mesh coverage, sectors, quiet-node events | v1; difficulty **Research** | **Team answer** | AAR v1.1 §3.3 |
| F-07 | Out-of-range gaps shown and annotated on the track, never interpolated | v1 | **Team answer** | AAR v1.1 §6.3; MCM v1.1 §6.8 |
| F-08 | Search radius around each position, from the team type's sweep width | Not set | **Open**; sweep widths are a team item (I-14) | AAR v1.1 §3.3; the owner, September 28 |
| F-09 | Distance between selected searchers over time; combined coverage | v2 | **Team answer** | AAR v1.1 §3.3 |
| F-10 | Per-sector coverage at time T; searched against missed | Not set | **Research** | AAR v1.1 §3.3 |
| F-11 | Charts (distance, coverage over time) | After the frontend pick | **Team answer** | AAR v1.1 §3.4, §6.4 |
| F-12 | AAR export | Not needed now | **Team answer**; U-03 | AAR v1.1 §3.4 |

Two things follow from this table. First, every v1 feature is a view of the same data: positions and events, filtered by time and by searcher. Second, F-08, F-09, and F-10 are computed from positions; they add no stored data of their own. So the store's job is small and exact: hold every position and every event, in time order, and give them back fast.

---

## 3 What replay asks of the store

Each v1 feature turns into a question the backend must answer for one mission. The scrub model in §7 decides whether the browser or the backend answers them on each slider move; the questions are the same either way.

| # | Question | Feeds | What the store needs |
| --- | --- | --- | --- |
| Q-01 | Where was every selected searcher at time T? (the last known position at or before T) | F-01, F-04 | Positions indexed by searcher and by time |
| Q-02 | Every position of the selected searchers up to T (the trails) | F-03, F-04 | Same index; ordered output |
| Q-03 | Every position inside a time window [T1, T2) | F-01 chunked loading; F-09 | Index by time |
| Q-04 | Every event at or before T, or inside a window | F-05 | Events with a time and a type |
| Q-05 | Where and when was each searcher out of range? | F-07 | Consecutive device times per searcher, or stored gap events (A-02) |
| Q-06 | Which layer applies at T? (sectors as edited, probability surface, coverage) | F-06 | Sector edits as events; artifact references; coverage per time or recomputed (I-21) |
| Q-07 | Which searcher is which radio, and on which team, at T? | F-04 labels and colors | Assignment as an event, not a column (A-06) |
| Q-08 | The searched area at T (union of sweep-width buffers along the trails) | F-08, F-10 | Positions plus a sweep width per team type; computed, not stored (**Proposed**) |

Q-01 through Q-05 are the v1 set. Q-06 and Q-07 are v1 for the parts the other segments already write. Q-08 waits on the sweep-width item.

---

## 4 Requirements the store must meet

These follow from verified decisions and team answers. They are the fixed points. The shapes that meet them are in §5.

### 4.1 The stream must be replayable

Replay is "everything that happened at or before T". A table that overwrites a radio's last position cannot answer Q-02. So positions, telemetry, and events must be kept as they arrived, never replaced. This is a requirement on the data, not yet a rule on the schema; whether the whole store is insert-only is **Open** (§5.1). **Team answer** that time logs are essential (AAR v1.1 §3.1).

### 4.2 Every packet, every field, from the first day

The daemon must log every packet field from day one; signal data cannot be reconstructed later. **Team answer** (MCM v1.1 §3.2). The fields: position (latitude, longitude, altitude, time, precision bits); packet header (from, to, id, hop start, hop limit, relay node, SNR, RSSI); telemetry (battery, voltage, channel utilization, air utilization). The schema must carry all of them from the first stored packet (I-26).

### 4.3 Two timestamps and an insert order

Each position carries device time (the radio's GPS time) and receive time (when the command post heard the packet). **Team answer** (AAR v1.1 §6.3). Replay draws by device time. Receive time minus device time is the delivery delay. The gap between one radio's consecutive device times is the out-of-range evidence for F-07.

**Proposed** addition: the row's insert order (the packet id in §6) is the third clock. It is a total order that does not depend on any radio's clock. It is the tiebreaker when a radio has no GPS fix and reports no usable time, and it is the order the daemon's push to the screen follows. How firmware reports time without a fix is **Research** (A-03).

### 4.4 Laptop-local, and one self-contained mission

During a search, data is stored locally on the command post computer; no live cloud database. **Verified** V-10. Some AARs happen days later, and the file must survive. **Team answer** (AAR v1.1 §3.1). So a mission must be one thing that can be copied: the store, plus the artifacts it references (§6, `artifact`). Replay also needs the map. The terrain layers belong to (P)MP, so an AAR opened on another machine must be able to find its tiles (A-04).

### 4.5 Retention is explicit before the first real position is stored

Position data of people in the field is sensitive. The repository's rules already say to minimize what is stored and make retention explicit. The retention rule (R-11) must exist before any real person's position is stored; synthetic and simulator data need no rule. **Research** (AAR v1.1 §3.1, §9 Q4).

### 4.6 Mission scale

For sizing, not for decisions. MCM v1.1 §6.1 puts the airtime limit near ten to twenty radios at one-minute intervals on the default preset. A twelve-hour search with twenty radios at sixty seconds is about fourteen thousand positions. A two-day search with forty radios at thirty seconds is about two hundred thousand. Both are small for any engine in §5.3. The raw packet log (payload plus decoded fields) is several times the size of the position rows; that matters for retention, not for replay.

---

## 5 Mission store: shape, stores, engine, lifecycle

### 5.1 Store shape

**Open.** AAR v1.1 §3.1 keeps the insert-only rule as an option to evaluate. Three shapes meet §4.1. None is proposed here; the trade-offs are laid out for the team.

| | (a) Insert-only log, with rebuildable projections | (b) Insert-only everything | (c) Current-state tables plus history tables |
| --- | --- | --- | --- |
| What it is | The packet, position, telemetry, and event tables are append-only. Derived tables (coverage per cell, per-sector numbers, node summaries) and mission metadata may be rebuilt or updated. | Every table is append-only. A change to mission metadata is a new row. Derived data is never stored; it is computed on read. | A `node` row holds the current position and status and is updated in place. A separate history table keeps every position. Replay reads history; the live view reads state. |
| Replay fidelity | Full: the log is the record. | Full. | Full, if the history table is written on every packet. The risk is a code path that updates state and skips history. |
| Live view | Q-01 against the log, or a cached projection. | Q-01 against the log. | A single-row read per node. Fastest, and duplicates what Q-01 already answers. |
| Write path | One insert per packet, plus a typed row. | Same. | One insert plus one update per packet. Two writes to keep consistent. |
| Mission metadata (name, dates, notes) | Updated in place; it is not replayed. | Appended; the latest row wins. More rows, one rule for everything. | Updated in place. |
| Rebuild after a bug | Drop the projection, recompute from the log. | Nothing to rebuild. | State can drift from history; a rebuild recomputes state from history. |
| Size | Log plus small projections. | Log only. | Log plus one state row per node. |
| Fit with the daemon | The daemon inserts; it never updates. | Same. | The daemon updates state; the second sign-off rule on the daemon ((P)MP v1.1 §3.6) then covers state logic too. |

The Bible-era `CLAUDE.md` (pull request #1, now closed) said "append-only history tables; never UPDATE state rows in place." The Bible is retired, so the rule is not in force. It is listed here as shape (a) or (b), for the team to keep, drop, or restate.

### 5.2 One store or several

**Proposed.** One mission file, with a table group per segment, and model artifacts as files beside it. The AAR owns the mission store schema (C-01). The (P)MP bridge daemon writes the packet, position, and telemetry rows. (P)MP writes events and sectors. SPM writes an `artifact` row that points to its raster on disk. This is the middle path from AAR v1.1 §6.2 and Architecture v1.0 §6 R-01. It gives the owner what he asked for (ownership of at least the AAR store) without a second engine or a join across files.

Alternative, listed for the vote: a separate AAR store. The daemon writes to it as well, or the AAR copies from the (P)MP store at mission end. Replay must then align two clocks, and the join contract moves into the daemon. AAR v1.1 §6.2 lists the trade-offs.

Either way, rasters and trained models do not go in a row store; they are files, referenced by a row. **Team answer** (AAR v1.1 §6.2).

### 5.3 Engine

**Research.** AAR v1.1 §6.1 compares SQLite (with SpatiaLite or GeoPackage), PostgreSQL with PostGIS, and a local NoSQL store against seven requirements. That table stands; this document does not restate it or lean. The constraints from §4 that bear on the choice:

- Laptop-local and zero-install for a volunteer (V-10; Foundation v3.0 §6.3).
- One self-contained mission that can be copied for an AAR days later (§4.4).
- One writer during a mission: the daemon. Readers: the live view and, later, replay.
- Spatial work in v1 is small: Q-08 is a buffer and a union over a few thousand points. Shapely (server) or Turf (browser) can do it; a spatial database is not required for it.
- Packaging follows (P)MP: one binary is the lean ((P)MP v1.1 §3.7). An engine that ships inside the binary and one that needs a server process have different install stories.

The schema in §6 is written as SQL so the team can read it. Its tables are engine-neutral; only the index and pragma lines are engine-specific.

### 5.4 Mission file lifecycle

**Proposed.**

1. (P)MP starts a mission. The backend creates one store for it, named by mission id and start time, in a missions folder the user can find.
2. The daemon opens the store once and appends for the whole mission. The live view reads from the same store.
3. (P)MP ends the mission. The backend marks `mission.ended_at`. The store is closed.
4. The AAR opens the store, on the same machine or after a copy. It never writes to it, except a possible `note` event type for review remarks (**Open**).
5. The retention rule (R-11) runs later: strip, scrub, or keep, on a schedule the team sets.

Where the missions folder lives, its naming, and whether the file is zipped with its artifacts for a copy are **Open** (A-04).

---

## 6 Schema draft (C-01 draft)

**Proposed.** This is the owner's starting draft of contract C-01, the mission store schema (Architecture v1.0 §4). It is here to be argued with. It carries every field from MCM v1.1 §3.2, both timestamps, and the event types from (P)MP v1.1 §6.5 and AAR v1.1 §3.2. It is written so that shapes (a) and (b) in §5.1 both fit; shape (c) would add a `node_state` table.

### 6.1 Tables

| Table | One row per | Written by | Read by | Notes |
| --- | --- | --- | --- | --- |
| `mission` | Mission | (P)MP backend | All | Id, name, start, end, schema version, notes. Updated in place under shape (a) or (c). |
| `node` | Radio ever heard | Daemon | All | Meshtastic node number is the key. Names and hardware from the node database. |
| `packet` | Received packet | Daemon | AAR, MCM | The raw log: every header field from MCM §3.2, the raw payload, the decoded fields as JSON. Source of truth. |
| `position` | Position packet | Daemon | (P)MP live, AAR | Typed projection of a `packet` row: device time, receive time, latitude, longitude, altitude, precision bits. |
| `telemetry` | Telemetry packet | Daemon | MCM, AAR | Battery, voltage, channel utilization, air utilization. |
| `message` | Text packet | Daemon; (P)MP for outbound | AAR, (P)MP | Direction, channel, text. Also an event on the timeline (F-05). |
| `event` | Timeline event | (P)MP; daemon for gaps if A-02 says so | AAR, (P)MP | Type, time, optional node, optional sector, JSON payload. Types in §6.3. |
| `sector` | Sector version | (P)MP | AAR, SPM | Geometry as GeoJSON, plus the event that created or edited it. A redraw is a new row, not an update. |
| `artifact` | File beside the store | SPM; (P)MP for terrain package | AAR | Kind (probability surface, coverage raster, terrain package), relative path, format, checksum, produced-at time. |

### 6.2 Time rule, coordinates, identity

- Times are UTC ISO-8601 text. `position.device_time` is the radio's GPS time; `NULL` when the radio reports none (A-03). `rx_time` is the command post clock at receipt. `packet.packet_id` is the insert order (§4.3).
- Coordinates are WGS84 decimal degrees, latitude then longitude, as floats. Altitude in meters. These match the repository's existing conventions.
- Identity is the Meshtastic node number. Who carries a radio, and on which team, is an `assignment` event with a time (Q-07, A-06). No `node` column holds a person.
- Every position row keeps `precision_bits`. A reduced-precision position is stored as reported and flagged in replay; it is not sharpened.

### 6.3 Event types

| Type | From | Payload |
| --- | --- | --- |
| `assignment` | (P)MP | node, team, person label, sector, start or end |
| `edit` | (P)MP | what changed on the plan; the `sector` row it produced |
| `override` | (P)MP | what the system proposed, what the commander did, a reason if given ((P)MP v1.1 §6.5) |
| `message` | Daemon or (P)MP | direction, channel, text; mirrors the `message` row |
| `clue` | (P)MP | position, description |
| `find` | (P)MP | position, description; ends the timeline for most reviews |
| `gap` | Daemon, if A-02 chooses stored gaps | node, last heard, next heard |
| `mission` | (P)MP backend | started, ended, paused |
| `note` | AAR review | free text on the timeline; **Open** whether the AAR writes at all |

### 6.4 Draft DDL

Written for SQLite because that is what runs in the owner's spike; the tables port to PostgreSQL by changing the types. Engine is not decided (§5.3).

```sql
CREATE TABLE mission (
    mission_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    started_at   TEXT NOT NULL,          -- UTC ISO-8601, command post clock
    ended_at     TEXT,
    schema_ver   TEXT NOT NULL,
    notes        TEXT
);

CREATE TABLE node (
    node_num     INTEGER PRIMARY KEY,    -- Meshtastic node number
    long_name    TEXT,
    short_name   TEXT,
    hw_model     TEXT,
    first_seen   TEXT NOT NULL
);

-- Raw per-packet log. Every packet, every header field, raw and decoded. Source of truth.
CREATE TABLE packet (
    packet_id    INTEGER PRIMARY KEY,    -- insert order: the third clock
    rx_time      TEXT NOT NULL,
    from_node    INTEGER NOT NULL,
    to_node      INTEGER,
    mesh_id      INTEGER,                -- packet id from the header
    portnum      TEXT NOT NULL,          -- POSITION_APP, TELEMETRY_APP, TEXT_MESSAGE_APP, ...
    hop_start    INTEGER,
    hop_limit    INTEGER,
    relay_node   INTEGER,
    rx_snr       REAL,
    rx_rssi      INTEGER,
    want_ack     INTEGER,
    raw          BLOB,
    decoded      TEXT                    -- JSON
);

-- Typed projections, one row per packet row of that kind.
CREATE TABLE position (
    packet_id      INTEGER PRIMARY KEY REFERENCES packet(packet_id),
    node_num       INTEGER NOT NULL,
    device_time    TEXT,                 -- GPS time on the radio; NULL when none reported
    rx_time        TEXT NOT NULL,
    lat            REAL NOT NULL,
    lon            REAL NOT NULL,
    alt_m          REAL,
    precision_bits INTEGER
);

CREATE TABLE telemetry (
    packet_id    INTEGER PRIMARY KEY REFERENCES packet(packet_id),
    node_num     INTEGER NOT NULL,
    rx_time      TEXT NOT NULL,
    battery_pct  REAL,
    voltage      REAL,
    channel_util REAL,
    air_util_tx  REAL
);

CREATE TABLE message (
    packet_id    INTEGER PRIMARY KEY REFERENCES packet(packet_id),
    node_num     INTEGER NOT NULL,
    direction    TEXT NOT NULL,          -- in | out
    channel      INTEGER,
    rx_time      TEXT NOT NULL,
    text         TEXT NOT NULL
);

-- Timeline events (section 6.3).
CREATE TABLE event (
    event_id     INTEGER PRIMARY KEY,
    event_time   TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    node_num     INTEGER,
    sector_id    TEXT,
    payload      TEXT                    -- JSON
);

-- Sector versions. A redraw inserts a new row that points at the event that caused it.
CREATE TABLE sector (
    sector_row   INTEGER PRIMARY KEY,
    sector_id    TEXT NOT NULL,
    version      INTEGER NOT NULL,
    event_id     INTEGER REFERENCES event(event_id),
    geometry     TEXT NOT NULL,          -- GeoJSON polygon
    valid_from   TEXT NOT NULL
);

-- Files beside the store: rasters, terrain package, exports.
CREATE TABLE artifact (
    artifact_id  INTEGER PRIMARY KEY,
    kind         TEXT NOT NULL,          -- probability_surface | coverage | terrain_package | export
    rel_path     TEXT NOT NULL,
    format       TEXT NOT NULL,
    sha256       TEXT,
    produced_at  TEXT NOT NULL,
    owner        TEXT NOT NULL           -- SPM | PMP | MCM | AAR
);

CREATE INDEX ix_position_node_time ON position(node_num, device_time);
CREATE INDEX ix_position_time      ON position(device_time);
CREATE INDEX ix_packet_rx          ON packet(rx_time);
CREATE INDEX ix_event_time         ON event(event_time);
```

What is deliberately not in the draft: a `node_state` table (shape (c)), a coverage-per-cell table (I-21 is Open), and any column for a person's name on `node` (A-06).

---

## 7 Replay: where the scrubbing happens, and drawing rules

### 7.1 Where the scrubbing happens

**Open.** This waits on the frontend pick with (P)MP (I-18, R-10). Both shapes are laid out; neither is proposed. The questions in §3 are the same in both.

| | Server time-T queries | Mission bundle to the browser |
| --- | --- | --- |
| What it is | Each slider move sends T to the backend. The backend answers Q-01 and Q-02 for T and returns the rows. The browser draws what it receives. | The backend serves the mission timeline once: positions, events, sectors. The browser holds it and answers Q-01 through Q-05 in memory on every slider move. |
| Round trips | One per slider move. | One per mission, or one per time window if chunked (Q-03). |
| Smoothness | Set by the query time plus the network hop. Fine on a normal mission; a visible hitch on a very large one. | Set by the browser. Instant at normal mission sizes. |
| Memory | Small in the browser. | The whole timeline in the browser: a few megabytes on a normal mission, tens on a very large one. Chunking by window bounds it. |
| Live view | Separate code: the live view polls or subscribes for the current state. | The live view is replay at T = now. The daemon's push appends to the same in-memory timeline. One component for both screens. |
| Filters and layers | Each filter change is a new query, or the client filters the returned rows. | All client-side. |
| Backend surface | Endpoints that take T and filters. | Endpoints that return a mission, a window, or a stream. |
| Fit with the map library | Either works with MapLibre, Leaflet, or OpenLayers. Time-filtered layers are simpler when the data is already in the browser. | Same. |
| Where it is heavier | The backend and the query path. | The frontend and its state handling. |

The chunked bundle is a variant of the second shape: the browser loads the window around the slider and fetches the next window ahead of it. It keeps memory bounded on multi-day searches at the cost of a small amount of client logic.

### 7.2 Drawing rules

These are team answers and hold under either scrub model.

- Draw the track by device time. **Team answer** (AAR v1.1 §6.3).
- Show and annotate out-of-range gaps; never interpolate across them. **Team answer** (AAR v1.1 §6.3; MCM v1.1 §6.8). The annotation shows last heard and next heard.
- A position with no device time is drawn at its receive time and marked as such, or hidden behind a toggle. **Open** (A-03).
- A reduced-precision position is drawn with its precision shown, not sharpened. **Proposed**.
- Events are marks on the timeline and, when they carry a position, marks on the map. **Team answer** (AAR v1.1 §3.2).
- Layers toggle on and off without changing T. The probability surface is one raster per mission in v1 (V-02: static, pre-mission), so it does not change with T. Sectors change with T through their versions (§6.1). Coverage per time is **Open** (I-21).

---

## 8 Boundary: what the AAR exposes, consumes, and signs

### 8.1 Consumes

| From | What | Contract | Status |
| --- | --- | --- | --- |
| MCM | Positions, telemetry, signal data with every packet field, two timestamps (I-08, I-24, I-26) | C-01 fields; C-08 for the pin the daemon decodes against | **Team answer** |
| (P)MP | The daemon that writes the store (I-17) | C-01, C-02 | **Team answer**; daemon is group-shared |
| (P)MP | Events with time: assignments, edits, overrides, messages, clues, finds (I-16) | C-09 | **Team answer** |
| (P)MP | Web stack, map library, and the screen the replay lives on (I-18) | — | **Team answer**; library **Research** R-10 |
| SPM | The probability surface and its inputs, as a file beside the store with an `artifact` row (I-22) | C-04 | **Open** where stored |
| (P)MP and MCM | Coverage overlays per time, or the model to recompute them (I-21) | C-06 | **Open** |

### 8.2 Exposes

**Proposed**, framework-neutral. Whatever framework (P)MP picks (R-03), the AAR backend answers these for one mission: the mission record; the node list; positions by node, by window, or all (Q-01 to Q-03); events by window (Q-04); gaps (Q-05); sector versions and artifacts at T (Q-06); assignments at T (Q-07). The exact endpoints or messages are written into C-02 or a small AAR contract once R-03 and the scrub model (§7.1) are settled. The replay UI itself lives in the shared frontend (§9.2).

Out of the AAR, later: the history layer for the next search (I-19) and outcomes as SPM training data (I-23). Both **Open**; not in v1.

### 8.3 Signs

From Architecture v1.0 §4:

| Contract | AAR role | Status |
| --- | --- | --- |
| C-01 Mission store schema | Writes. (P)MP and SPM sign; MCM confirms the packet fields. §6 is the draft. | Draft in this document |
| C-02 Daemon message contract | Signs. What the daemon pushes to the screen; under the bundle shape, the same push feeds the live timeline. | Waits on R-03 |
| C-04 Probability surface format | Signs. Raster type, resolution, coordinate system, where the file lives (the `artifact` row). | Waits on R-01 |
| C-09 Event record | Signs. Event types and fields; §6.3 is the AAR's proposed list. | Waits on C-01 |

---

## 9 Package layout: `aar/`

### 9.1 The package

**Proposed.** `aar/` follows the shape of `spm/` in pull request #4: a self-contained Python package with its own `pyproject.toml`, a `src/aar/` layout, its own tests, its own `.gitignore`, and `claude/` and `archive/` placeholders in every folder, per the Team Claude Guide. This keeps the two segment packages alike and keeps `aar/` independent of the root project until the team settles the shared layout (Architecture v1.0 §5.1, P-01).

```
aar/
├── README.md
├── pyproject.toml                 package "aar"; no runtime dependencies beyond the standard library
├── .gitignore                     mission files and data are never committed
├── docs/
│   └── ROADMAP.md                 phases and gates for this segment (section 11)
├── data/
│   └── README.md                  missions/ and synthetic/ live here locally; never committed
├── src/aar/
│   ├── store/
│   │   ├── schema.sql             the C-01 draft (section 6.4)
│   │   └── db.py                  open or create a mission store; insert helpers the daemon could call
│   ├── replay/
│   │   └── queries.py             Q-01 to Q-05 as functions over a store
│   ├── synthetic.py               a synthetic mission generator for tests and demos
│   └── cli.py                     aar synth | aar summary
└── tests/                         one test file per module; synthetic data only
```

Not in the package: the replay UI (§9.2), the daemon ((P)MP), any real position data.

### 9.2 Where the replay UI lives

**Open.** Replay and planning share one screen and one map (I-18). Architecture v1.0 §5.1 puts `pmp/web/` and `aar/web/` in the same frontend build, with the build config in `pmp/web/`. Until the frontend is picked, `aar/` holds only the backend side. The choice is between a route group inside the (P)MP frontend, owned by the AAR through CODEOWNERS, and an `aar/web/` folder that the (P)MP build includes. Raised in §13.

### 9.3 What the repository still needs

The root CI runs `uv run pytest` with `testpaths = ["backend/tests"]`, so it runs neither `spm/` nor `aar/` tests. Wiring segment packages into the root project, or giving each its own CI job, is part of the reconciliation pull requests (Architecture v1.0 §9, P-01). This document does not change the root files.

---

## 10 Roadblocks for this segment

From Architecture v1.0 §6, the rows that gate the AAR, plus the roadblocks new in this document.

| # | Decision | Status | Who resolves | Blocks | Can proceed without it |
| --- | --- | --- | --- | --- | --- |
| R-01 | One mission store or several; who owns which | **Proposed** in §5.2; **Open** | Corey with JJ and Elijah | C-01 signed; C-04; the daemon's write path | The schema draft; queries against synthetic data |
| R-02 | Database engine | **Research** | Corey | C-01 signed; packaging | Everything against the draft in SQLite; the draft ports |
| R-04 | Store shape: insert-only, or state plus history | **Open** (§5.1) | Corey with Diego | The daemon's write logic; `node_state` or not | Replay queries, which read the log either way |
| R-10 | Map library | **Research** | Elijah | The replay UI; layer toggles; the scrub model | The backend side of `aar/` |
| R-11 | Retention rule | **Research** | Corey | Storing any real person's position | All synthetic and simulator work |
| R-13 | Python as the backend language | U-02, leaning | Segment owners | Nothing in `aar/` in practice | All current work |
| R-15 | Export: where it lives, whether a format is needed | U-03 | Corey and Elijah | Nothing in the fall slice | Everything |
| A-01 | Scrub model: server time-T queries, mission bundle, or chunked bundle | **Open** (§7.1) | Corey with Elijah, after R-10 | The AAR backend surface; C-02 additions | Q-01 to Q-05 as functions; both shapes call them |
| A-02 | Gap storage: derived from missing device times, or a gap event written by the daemon (I-13) | **Open** | Corey with Diego and Elijah | The `gap` event type; the quiet-node alert source | Derived gaps as a query on the log |
| A-03 | Positions with no device time: how firmware reports them, how they are drawn | **Research** | Corey with Diego | The time rule text in C-01; drawing rule | Store `NULL`, draw by receive time, flagged |
| A-04 | AAR on another machine: how a copied mission finds its tiles and artifacts | **Open** | Corey with Elijah | The mission file lifecycle (§5.4); an AAR days later | Same-machine replay |
| A-05 | Where the replay UI lives in the tree (§9.2) | **Open** | Corey with Elijah | The frontend build layout | The backend side |
| A-06 | Radio to person to team: assignment as an event, and what the label shows | **Proposed** (§6.2) | Corey with Elijah | C-09 `assignment` payload; F-04 labels | Node numbers as labels |

**What the ordering says.** R-01, R-02, and R-04 are the store cluster; Architecture v1.0 §6 already names them the first decision meeting. A-01 and A-05 follow R-10, the frontend. A-02 and A-03 are small and can be settled with Diego in one sitting. R-11 is a rule to write, and it is cheap; write it early.

---

## 11 Build order for this segment

Mapped onto the phases of Architecture v1.0 §7.

### 11.1 What starts now, with no decision

| Work | Where | Needs |
| --- | --- | --- |
| The C-01 draft as `schema.sql`, with a loader | `aar/src/aar/store/` | Nothing; it is the draft in §6 |
| A synthetic mission generator: N radios, H hours, an interval, out-of-range gaps, delivery delay, some positions with no device time | `aar/src/aar/synthetic.py` | Nothing |
| Q-01 to Q-05 as functions, tested against synthetic missions | `aar/src/aar/replay/` and `aar/tests/` | The two items above |
| The retention rule draft (R-11) | `docs/` and C-01 | SAR team practice; the IRB items already on the team's list |
| The C-09 event list as the AAR proposes it (§6.3) | C-01 draft; shared with Elijah | Nothing |

### 11.2 What waits, and on what

| Work | Waits on |
| --- | --- |
| The AAR backend endpoints or messages | R-03 (framework, Elijah); A-01 (scrub model) |
| The replay UI: map, slider, filter panel | R-10 (map library); A-05 (where it lives) |
| The daemon writing to the draft schema | C-01 signed (R-01, R-02, R-04); C-08 (radio pin, Diego) |
| Replay of real radio data | The daemon above; Diego's simulator (I-15) or radios; R-11 before any real person |
| Coverage views (F-08, F-10) | Sweep widths (I-14); C-06 for the mesh coverage layer |
| History layer, export | I-19, R-15; not in the fall slice |

### 11.3 Phases

| Phase | This segment delivers | Gate |
| --- | --- | --- |
| 0 | `aar/` package on `main`; this document under `docs/architecture/` | Pull request review |
| 1 | C-01 signed by (P)MP and SPM; C-09 event list agreed with (P)MP; R-11 written | The store decision meeting (R-01, R-02, R-04) |
| 2 | The daemon writes to the store on the simulator; Q-01 to Q-05 answer against real packet rows; the replay UI draws one track with a slider in the shared frontend | R-10 and A-01 settled; Diego's simulator running |
| 3 | Integration step 3 of Architecture v1.0 §7.1: store to replay, on the vertical slice's region and mission | Steps 1 and 2 of that list |

---

## 12 Research the owner will do

Updated from AAR v1.1 §7.

| Item | What to find out | Where to look | State |
| --- | --- | --- | --- |
| Data-flow chart | Chart the functionality, then model the data flow across all four segments | Architecture v1.0 §3 is that chart; §3 and §8 of this document are the AAR's rows | Done in Architecture v1.0; kept current here |
| Engine | Which engine fits AAR v1.1 §6.1; try a time-T query in two of them | SQLite and SpatiaLite documentation; PostGIS documentation; GeoPackage specification | Owner research |
| One store or several | Settle with the SPM and (P)MP owners | §5.2; AAR v1.1 §6.2 | Proposed here; meeting item |
| Store shape and time rule | Whether insert-only is the rule; what each record holds | §5.1, §6; MCM v1.1 §3.2 | Options laid out; meeting item |
| No-fix time (A-03) | How Meshtastic firmware fills position time without a GPS fix, and whether the daemon can tell | Meshtastic protobuf and firmware documentation, with Diego | New |
| Retention | How long the file lives, who opens it, what can be stripped; whether the raw packet payload is the first thing to strip | SAR team practice; IRB guidance already on the team's list | Owner research |
| Commander needs | What a review must show first | AAR v1.1 §6.5 | Owner research |
| Layer toggles | How hard time-filtered layers are in the chosen map library | Map library documentation, with Elijah | Waits on R-10 |
| Scrub model (A-01) | Which shape the chosen frontend favors; how big a bundle the browser tolerates | Frontend and map library documentation; a prototype against synthetic data | Waits on R-10 |
| Coverage views | Whether per-sector coverage and searched-against-missed are worth building, and what they need | SAR coverage literature; the sweep-width team item | Owner research |
| Tiles for an AAR elsewhere (A-04) | How the (P)MP terrain package is found from a copied mission | With Elijah, after C-05 | New |

---

## 13 Open questions

1. Store shape (§5.1): insert-only log with projections, insert-only everything, or state plus history? Waits on the store decision meeting.
2. Does the team accept one mission file with a table group per segment, and the AAR as the writer of C-01 (§5.2)?
3. Engine (§5.3): which, and does the answer change if (P)MP packages one binary?
4. Scrub model (§7.1): server time-T queries, a whole-mission bundle, or a chunked bundle? Waits on the frontend pick.
5. Gaps (A-02): derived in replay from missing device times, or written by the daemon as `gap` events that also drive the quiet-node alert?
6. Positions with no device time (A-03): what does the firmware report, and how does replay draw them?
7. Where does the replay UI live in the tree (§9.2), and who owns it through CODEOWNERS?
8. Does the AAR ever write to a mission store (a `note` event), or is it read-only?
9. Are the event types in §6.3 the right set for C-09? What does (P)MP add or remove?
10. How does a copied mission find its tiles and artifacts on another machine (A-04)?
11. Is the retention rule written before the first simulator run, or before the first real radio test?

---

*MaroonNet AAR Architecture v1.0 · September 28, 2026 · Branched from AAR v1.1 §2, §3, §6, §7, §9 and MaroonNet Architecture v1.0 §3, §4, §5, §6, §7. Decisions are recorded in the MaroonNet Decision Log. Nothing here is decided until the log says so.*
