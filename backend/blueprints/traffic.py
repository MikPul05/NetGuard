from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time

traffic_bp = Blueprint('traffic', __name__)
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")


def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)


@traffic_bp.route('/traffic/current', methods=['GET'])
def get_current_traffic():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT MAX(start_time_unix_us) as latest_us FROM flows;")
    res = cur.fetchone()
    latest_us = res['latest_us'] if res and res['latest_us'] else int(time.time() * 1_000_000)
    window_start_us = latest_us - (10 * 1_000_000)

    cur.execute("""
        SELECT COUNT(*) as flow_count,
               COALESCE(SUM(packet_count), 0) as total_packets,
               COALESCE(SUM(byte_count), 0) as total_bytes
        FROM flows
        WHERE start_time_unix_us >= %s AND start_time_unix_us <= %s;
    """, (window_start_us, latest_us))
    stats = cur.fetchone()
    cur.close()
    conn.close()

    window_sec = 10.0
    return jsonify({
        "windowSeconds": window_sec,
        "flowsPerSec": round(float(stats["flow_count"]) / window_sec, 2),
        "packetsPerSec": round(float(stats["total_packets"]) / window_sec, 2),
        "bytesPerSec": round(float(stats["total_bytes"]) / window_sec, 2)
    })


@traffic_bp.route('/traffic/timeseries', methods=['GET'])
def get_traffic_timeseries():
    window = request.args.get('window', '10s')  # 1s, 10s, 60s
    seconds = 60 if window == '60s' else (1 if window == '1s' else 10)
    window_us = seconds * 1_000_000

    conn = get_db()
    cur = conn.cursor()
    # Group flows into temporal buckets
    cur.execute(f"""
        SELECT (start_time_unix_us / {window_us}) * {window_us} as bucket_us,
               COUNT(*) as flow_count,
               SUM(packet_count) as packet_count,
               SUM(byte_count) as byte_count
        FROM flows
        GROUP BY bucket_us
        ORDER BY bucket_us ASC
        LIMIT 100;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({
        "window": window,
        "points": [{
            "timestampUnixUs": r["bucket_us"],
            "flowCount": r["flow_count"],
            "packetCount": r["packet_count"],
            "byteCount": r["byte_count"]
        } for r in rows]
    })


@traffic_bp.route('/traffic/top-talkers', methods=['GET'])
def get_top_talkers():
    limit = max(1, min(50, int(request.args.get('limit', 5))))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT source_ip, SUM(byte_count) as total_bytes, COUNT(*) as flow_count
        FROM flows
        GROUP BY source_ip
        ORDER BY total_bytes DESC
        LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([{
        "sourceIp": r["source_ip"],
        "totalBytes": r["total_bytes"],
        "flowCount": r["flow_count"]
    } for r in rows])


@traffic_bp.route('/flows', methods=['GET'])
def get_flows():
    page = max(1, int(request.args.get('page', 1)))
    size = max(1, min(100, int(request.args.get('size', 20))))
    src = request.args.get('src')
    dst = request.args.get('dst')
    protocol = request.args.get('protocol')
    port = request.args.get('port')

    query = "SELECT * FROM flows WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM flows WHERE 1=1"
    params = []

    if src:
        query += " AND source_ip = %s"
        count_query += " AND source_ip = %s"
        params.append(src)
    if dst:
        query += " AND destination_ip = %s"
        count_query += " AND destination_ip = %s"
        params.append(dst)
    if protocol:
        query += " AND protocol = %s"
        count_query += " AND protocol = %s"
        params.append(protocol)
    if port:
        query += " AND (source_port = %s OR destination_port = %s)"
        count_query += " AND (source_port = %s OR destination_port = %s)"
        params.extend([port, port])

    query += " ORDER BY start_time_unix_us DESC LIMIT %s OFFSET %s"
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
        "flows": [{
            "id": r["id"],
            "startTimeUnixUs": r["start_time_unix_us"],
            "sourceIp": r["source_ip"],
            "destinationIp": r["destination_ip"],
            "sourcePort": r["source_port"],
            "destinationPort": r["destination_port"],
            "protocol": r["protocol"],
            "packetCount": r["packet_count"],
            "byteCount": r["byte_count"]
        } for r in rows]
    })