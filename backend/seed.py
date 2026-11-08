import psycopg2
import json
import os
from datetime import datetime, timezone

DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")

def seed():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    base_time_us = 1710000000000000  # Unix timestamp in microseconds
    iso_time = datetime.fromtimestamp(base_time_us / 1_000_000, timezone.utc).isoformat()

    print("Inserting sample flows...")
    for port in range(20, 45):
        cur.execute("""
            INSERT INTO flows (start_time_unix_us, duration_us, source_ip, destination_ip, source_port, destination_port, protocol, packet_count, byte_count, input_file)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (base_time_us + (port * 10000), 500, "192.168.1.105", "10.0.0.1", 45000 + port, port, 6, 2, 120, "sample_capture.pcap"))

    print("Inserting sample alerts & detections...")
    # Alert 1: Port Scan
    cur.execute("""
        INSERT INTO alerts (id, timestamp, type, severity, source_ip, destination_ip)
        VALUES (1, %s, 'PORT_SCAN', 'HIGH', '192.168.1.105', '10.0.0.1')
        ON CONFLICT (id) DO NOTHING;
    """, (iso_time,))

    cur.execute("""
        INSERT INTO detections (
            id, alert_id, timestamp, type, severity, confidence, score,
            window_start_unix_us, window_seconds, methods, explanation,
            evidence, thresholds, statistical_evidence, input_source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, (
        "d-00001", 1, iso_time, "PORT_SCAN", "HIGH", 0.88, 1.25,
        base_time_us, 10, json.dumps(["rule"]),
        "Port scan detected via rule: 192.168.1.105 queried 25 unique ports.",
        json.dumps({"uniqueDstPorts": 25, "connectionAttempts": 25}),
        json.dumps({"uniqueDstPorts": 20}),
        None,
        json.dumps({"file": "sample_capture.pcap"})
    ))

    # Alert 2: Combined Detection (Statistical + Rule)
    cur.execute("""
        INSERT INTO alerts (id, timestamp, type, severity, source_ip, destination_ip)
        VALUES (2, %s, 'SUSPICIOUS_CONNECTION_PATTERN', 'CRITICAL', '192.168.1.200', 'multiple')
        ON CONFLICT (id) DO NOTHING;
    """, (iso_time,))

    cur.execute("""
        INSERT INTO detections (
            id, alert_id, timestamp, type, severity, confidence, score,
            window_start_unix_us, window_seconds, methods, explanation,
            evidence, thresholds, statistical_evidence, input_source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, (
        "d-00002", 2, iso_time, "SUSPICIOUS_CONNECTION_PATTERN", "CRITICAL", 0.96, 3.40,
        base_time_us, 10, json.dumps(["rule", "statistical"]),
        "Anomaly detected via rule & statistical methods with score 3.40.",
        json.dumps({"connectionAttempts": 85, "uniqueDstPorts": 40, "uniqueDstIps": 12, "byteCount": 10240}),
        json.dumps({"zScore": 3.0}),
        json.dumps({"zScore": 3.4, "zScoreFeature": "uniqueDstPorts", "baselineMean": 5.2, "baselineStd": 1.1}),
        json.dumps({"file": "sample_capture.pcap"})
    ))
    print("Inserting sample evaluation run...")
    cur.execute("""
        INSERT INTO evaluation_runs (
            run_id, tp, fp, fn, tn, precision, recall, f1, fpr, fnr, detected_attacks
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO NOTHING;
    """, (
        "run-001", 42, 2, 3, 500,
        0.955, 0.933, 0.944, 0.004, 0.067,
        json.dumps(["PORT_SCAN", "DOS_DDOS", "SUSPICIOUS_CONNECTION_PATTERN"])
    ))

    cur.execute("SELECT setval('alerts_id_seq', (SELECT MAX(id) FROM alerts));")

    conn.commit()
    cur.close()
    conn.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed()