-- MaroonNet mission store: C-01 DRAFT.
-- Source: AAR Architecture v1.0 section 6. Proposed, not decided. The team votes.
-- Times are UTC ISO-8601 text. Coordinates are WGS84 decimal degrees. Identity is the
-- Meshtastic node number. Written for SQLite; the tables port to PostgreSQL by changing types.

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

-- Timeline events (AAR Architecture v1.0 section 6.3).
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
