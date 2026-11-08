import os
import json
import time
from datetime import datetime, timezone
import psycopg2
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DETECTIONS_TOPIC = os.getenv("DETECTIONS_TOPIC", "detections")
FLOWS_TOPIC = os.getenv("FLOWS_TOPIC", "flows")


def calculate_severity(score, methods):
    is_combined = len(methods) > 1
    if score >= 4.0 or (score >= 2.5 and is_combined):
        return "CRITICAL"
    elif score >= 2.0 or is_combined:
        return "HIGH"
    elif score >= 1.2:
        return "MEDIUM"
    return "LOW"


def calculate_confidence(score, methods):
    base = min(0.85, 0.5 + (score * 0.1))
    if len(methods) > 1:
        base = min(1.0, base + 0.15)
    return round(base, 2)


def generate_explanation(det):
    t = det.get("type", "UNKNOWN")
    ev = det.get("evidence", {})
    methods = det.get("detectionMethods", ["rule"])
    methods_str = " & ".join(methods)

    if t == "PORT_SCAN":
        return f"Port scan detected via {methods_str}: {det.get('sourceIp')} contacted {ev.get('uniqueDstPorts')} unique ports."
    elif t == "BRUTE_FORCE":
        return f"Brute force attempt detected via {methods_str}: {ev.get('connectionAttempts')} attempts against port {ev.get('destinationPort')}."
    elif t == "DOS_DDOS":
        return f"DoS flood targeting {det.get('destinationIp')} with {ev.get('connectionAttempts')} attempts."
    elif t == "SUSPICIOUS_CONNECTION_PATTERN":
        stat = det.get("statisticalEvidence", {})
        return f"Statistical anomaly: {stat.get('zScoreFeature')} reached Z-score of {stat.get('zScore')} (baseline: {stat.get('baselineMean')})."
    return f"Anomaly detected by {methods_str} with score {det.get('score', 1.0)}."


def get_db():
    while True:
        try:
            return psycopg2.connect(DB_URL)
        except psycopg2.OperationalError:
            print("[Worker] Waiting for PostgreSQL database...")
            time.sleep(2)


def create_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                DETECTIONS_TOPIC,
                FLOWS_TOPIC,
                bootstrap_servers=[KAFKA_BOOTSTRAP],
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="netguard-persistence-group"
            )
            print(f"[Worker] Subscribed to Kafka topics: '{DETECTIONS_TOPIC}', '{FLOWS_TOPIC}'")
            return consumer
        except NoBrokersAvailable:
            print("[Worker] Waiting for Kafka broker...")
            time.sleep(3)


def persist_detection(det, cur):
    score = float(det.get("score", 1.0))
    methods = det.get("detectionMethods", ["rule"])
    severity = calculate_severity(score, methods)
    confidence = calculate_confidence(score, methods)
    explanation = generate_explanation(det)

    cur.execute("""
        INSERT INTO alerts (timestamp, type, severity, source_ip, destination_ip)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        det.get("timestamp", datetime.now(timezone.utc).isoformat()),
        det.get("type", "UNKNOWN"),
        severity,
        det.get("sourceIp", "unknown"),
        det.get("destinationIp", "unknown")
    ))
    alert_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO detections (
            id, alert_id, timestamp, type, severity, confidence, score,
            window_start_unix_us, window_seconds, methods, explanation,
            evidence, thresholds, statistical_evidence, input_source
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            severity = EXCLUDED.severity,
            confidence = EXCLUDED.confidence;
    """, (
        det.get("detectionId"),
        alert_id,
        det.get("timestamp", datetime.now(timezone.utc).isoformat()),
        det.get("type", "UNKNOWN"),
        severity,
        confidence,
        score,
        int(det.get("windowStartUnixUs", 0)),
        int(det.get("windowSeconds", 10)),
        json.dumps(methods),
        explanation,
        json.dumps(det.get("evidence", {})),
        json.dumps(det.get("thresholds", {})),
        json.dumps(det.get("statisticalEvidence")),
        json.dumps(det.get("input", {"file": "stream"}))
    ))


def persist_flow(flow, cur):
    cur.execute("""
        INSERT INTO flows (
            start_time_unix_us, duration_us, source_ip, destination_ip,
            source_port, destination_port, protocol, packet_count, byte_count,
            tcp_flags, input_file
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        int(flow.get("startTimeUnixUs", flow.get("start_time_unix_us", 0))),
        int(flow.get("durationUs", flow.get("duration_us", 0))),
        flow.get("sourceIp", flow.get("source_ip", "0.0.0.0")),
        flow.get("destinationIp", flow.get("destination_ip", "0.0.0.0")),
        flow.get("sourcePort", flow.get("source_port")),
        flow.get("destinationPort", flow.get("destination_port")),
        int(flow.get("protocol", 6)),
        int(flow.get("packetCount", flow.get("packet_count", 1))),
        int(flow.get("byteCount", flow.get("byte_count", 64))),
        json.dumps(flow.get("tcpFlags", flow.get("tcp_flags", {}))),
        flow.get("inputFile", flow.get("input_file", "stream"))
    ))


def main():
    print("[Worker] Starting NetGuard Ingestion Consumer...")
    db_conn = get_db()
    consumer = create_consumer()

    for message in consumer:
        try:
            raw_text = message.value.decode("utf-8")
            data = json.loads(raw_text)
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            print(f"[Worker] Skipped malformed payload: {err}")
            continue

        try:
            with db_conn.cursor() as cur:
                if message.topic == DETECTIONS_TOPIC:
                    persist_detection(data, cur)
                    print(f"[Worker] Persisted detection {data.get('detectionId')} ({data.get('type')})")
                elif message.topic == FLOWS_TOPIC:
                    persist_flow(data, cur)
            db_conn.commit()
        except Exception as e:
            db_conn.rollback()
            print(f"[Worker] Database error: {e}")


if __name__ == "__main__":
    main()