-- ClickHouse DB Models for L1 App Violations

-- 1) Create database
CREATE DATABASE IF NOT EXISTS l1_app_db;

-- 2) Raw violations table
CREATE TABLE IF NOT EXISTS l1_app_db.violations
(
    event_time      DateTime,
    violation_type  Enum8('coupling'=1, 'interference'=2, 's_plane_delay'=3, 'fh_violation'=4),
    source          String,
    details         String,
    violation_count UInt32,
    window_ms       UInt32
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (violation_type, event_time)
SETTINGS index_granularity = 8192;

-- 3) Summary (master) table for aggregated daily counts
CREATE TABLE IF NOT EXISTS l1_app_db.violation_summary
(
    violation_type Enum8('coupling'=1, 'interference'=2, 's_plane_delay'=3, 'fh_violation'=4),
    event_date     Date,
    total_count    UInt64
)
ENGINE = SummingMergeTree()
PARTITION BY event_date
ORDER BY (violation_type, event_date)
SETTINGS index_granularity = 8192;

-- 4) Materialized view to auto-populate summary table
CREATE MATERIALIZED VIEW IF NOT EXISTS l1_app_db.mv_violations_to_summary
TO l1_app_db.violation_summary
AS
SELECT
    violation_type,
    toDate(event_time) AS event_date,
    count()           AS total_count
FROM l1_app_db.violations
GROUP BY
    violation_type,
    event_date;
