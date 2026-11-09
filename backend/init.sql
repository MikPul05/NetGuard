DROP TABLE IF EXISTS detection_flows CASCADE;
DROP TABLE IF EXISTS detections CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS flows CASCADE;
DROP TABLE IF EXISTS evaluation_runs CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;

CREATE TABLE flows (
    id SERIAL PRIMARY KEY,
    start_time_unix_us BIGINT NOT NULL,
    duration_us BIGINT,
    source_ip VARCHAR(45) NOT NULL,
    destination_ip VARCHAR(45) NOT NULL,
    source_port INTEGER,
    destination_port INTEGER,
    protocol INTEGER NOT NULL,
    packet_count INTEGER NOT NULL,
    byte_count BIGINT NOT NULL,
    tcp_flags JSONB,
    input_file VARCHAR(255)
);

CREATE INDEX idx_flows_time ON flows (start_time_unix_us);
CREATE INDEX idx_flows_src ON flows (source_ip);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    source_ip VARCHAR(45) NOT NULL,
    destination_ip VARCHAR(45) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE detections (
    id VARCHAR(40) PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence REAL NOT NULL,
    score REAL NOT NULL,
    window_start_unix_us BIGINT NOT NULL,
    window_seconds INTEGER NOT NULL,
    methods JSONB NOT NULL,
    explanation TEXT NOT NULL,
    evidence JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    statistical_evidence JSONB,
    input_source JSONB NOT NULL
);

CREATE TABLE evaluation_runs (
    run_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tp INTEGER NOT NULL,
    fp INTEGER NOT NULL,
    fn INTEGER NOT NULL,
    tn INTEGER NOT NULL,
    precision REAL NOT NULL,
    recall REAL NOT NULL,
    f1 REAL NOT NULL,
    fpr REAL NOT NULL,
    fnr REAL NOT NULL,
    detected_attacks JSONB
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(50) NOT NULL,
    action TEXT NOT NULL
);