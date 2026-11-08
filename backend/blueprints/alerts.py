from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@alerts_bp.route('', methods=['GET'])
def get_alerts():
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    alert_type = request.args.get('type')
    severity = request.args.get('severity')
    source_ip = request.args.get('sourceIp')
    dest_ip = request.args.get('destinationIp')
    page = max(1, int(request.args.get('page', 1)))
    size = max(1, min(100, int(request.args.get('size', 20))))
    sort = request.args.get('sort', '-timestamp')

    query = "SELECT id, timestamp, type, severity, source_ip, destination_ip FROM alerts WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM alerts WHERE 1=1"
    params = []

    if from_time:
        query += " AND timestamp >= %s"
        count_query += " AND timestamp >= %s"
        params.append(from_time)
    if to_time:
        query += " AND timestamp <= %s"
        count_query += " AND timestamp <= %s"
        params.append(to_time)
    if alert_type:
        query += " AND type = %s"
        count_query += " AND type = %s"
        params.append(alert_type)
    if severity:
        query += " AND severity = %s"
        count_query += " AND severity = %s"
        params.append(severity)
    if source_ip:
        query += " AND source_ip = %s"
        count_query += " AND source_ip = %s"
        params.append(source_ip)
    if dest_ip:
        query += " AND destination_ip = %s"
        count_query += " AND destination_ip = %s"
        params.append(dest_ip)

    order_direction = "DESC" if sort.startswith('-') else "ASC"
    sort_column = sort.lstrip('-')
    allowed_sorts = {"timestamp": "timestamp", "severity": "severity", "type": "type"}
    order_by = allowed_sorts.get(sort_column, "timestamp")

    query += f" ORDER BY {order_by} {order_direction} LIMIT %s OFFSET %s"
    offset = (page - 1) * size

    conn = get_db()
    cur = conn.cursor()
    cur.execute(count_query, tuple(params))
    total = cur.fetchone()["count"]

    cur.execute(query, tuple(params + [size, offset]))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "total": total,
        "page": page,
        "size": size,
        "alerts": [{
            "id": r["id"],
            "timestamp": r["timestamp"].isoformat(),
            "type": r["type"],
            "severity": r["severity"],
            "sourceIp": r["source_ip"],
            "destinationIp": r["destination_ip"]
        } for r in rows]
    })

@alerts_bp.route('/latest', methods=['GET'])
def get_latest_alerts():
    since = request.args.get('since')
    conn = get_db()
    cur = conn.cursor()

    if since:
        cur.execute("""
            SELECT id, timestamp, type, severity, source_ip, destination_ip
            FROM alerts WHERE timestamp > %s
            ORDER BY timestamp DESC LIMIT 50;
        """, (since,))
    else:
        cur.execute("""
            SELECT id, timestamp, type, severity, source_ip, destination_ip
            FROM alerts
            ORDER BY timestamp DESC LIMIT 50;
        """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{
        "id": r["id"],
        "timestamp": r["timestamp"].isoformat(),
        "type": r["type"],
        "severity": r["severity"],
        "sourceIp": r["source_ip"],
        "destinationIp": r["destination_ip"]
    } for r in rows])

@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert_detail(alert_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts WHERE id = %s;", (alert_id,))
    alert = cur.fetchone()

    if not alert:
        cur.close()
        conn.close()
        return jsonify({"error": "Alert not found"}), 404

    cur.execute("""
        SELECT id, type, severity, confidence, window_seconds, methods, explanation
        FROM detections WHERE alert_id = %s;
    """, (alert_id,))
    detections = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "id": alert["id"],
        "timestamp": alert["timestamp"].isoformat(),
        "type": alert["type"],
        "severity": alert["severity"],
        "sourceIp": alert["source_ip"],
        "destinationIp": alert["destination_ip"],
        "detections": [{
            "detectionId": d["id"],
            "type": d["type"],
            "severity": d["severity"],
            "confidence": d["confidence"],
            "window": f"{d['window_seconds']}s",
            "methods": d["methods"],
            "explanation": d["explanation"]
        } for d in detections]
    })