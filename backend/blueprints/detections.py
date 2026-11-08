from flask import Blueprint, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

detections_bp = Blueprint('detections', __name__, url_prefix='/detections')
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@detections_bp.route('/<det_id>', methods=['GET'])
def get_detection(det_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, type, severity, confidence, window_seconds, methods, explanation
        FROM detections WHERE id = %s;
    """, (det_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Detection not found"}), 404

    return jsonify({
        "detectionId": row["id"],
        "type": row["type"],
        "severity": row["severity"],
        "confidence": row["confidence"],
        "window": f"{row['window_seconds']}s",
        "methods": row["methods"],
        "explanation": row["explanation"]
    })

@detections_bp.route('/<det_id>/evidence', methods=['GET'])
def get_detection_evidence(det_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT evidence, thresholds, statistical_evidence
        FROM detections WHERE id = %s;
    """, (det_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Detection not found"}), 404

    return jsonify({
        "evidence": row["evidence"],
        "thresholds": row["thresholds"],
        "statisticalEvidence": row["statistical_evidence"]
    })

@detections_bp.route('/<det_id>/trace', methods=['GET'])
def get_detection_trace(det_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT window_start_unix_us, window_seconds, input_source, source_ip, destination_ip
        FROM detections d
        JOIN alerts a ON d.alert_id = a.id
        WHERE d.id = %s;
    """, (det_id,))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return jsonify({"error": "Detection not found"}), 404

    start_us = row["window_start_unix_us"]
    end_us = start_us + (row["window_seconds"] * 1_000_000)

    cur.execute("""
        SELECT id, start_time_unix_us, source_ip, destination_ip, destination_port, protocol, packet_count, byte_count
        FROM flows
        WHERE start_time_unix_us >= %s AND start_time_unix_us <= %s
          AND (source_ip = %s OR destination_ip = %s)
        LIMIT 100;
    """, (start_us, end_us, row["source_ip"], row["destination_ip"]))
    flow_rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "detectionId": det_id,
        "inputSource": row["input_source"],
        "windowStartUnixUs": start_us,
        "contributingFlowCount": len(flow_rows),
        "flows": [{
            "flowId": f["id"],
            "startTimeUnixUs": f["start_time_unix_us"],
            "sourceIp": f["source_ip"],
            "destinationIp": f["destination_ip"],
            "destinationPort": f["destination_port"],
            "protocol": f["protocol"],
            "packets": f["packet_count"],
            "bytes": f["byte_count"]
        } for f in flow_rows]
    })