from flask import Blueprint, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

@stats_bp.route('/summary', methods=['GET'])
def get_stats_summary():
    from_time = request.args.get('from')
    to_time = request.args.get('to')

    conn = get_db()
    cur = conn.cursor()

    query_filter = ""
    params = []
    if from_time and to_time:
        query_filter = " WHERE timestamp >= %s AND timestamp <= %s"
        params = [from_time, to_time]

    # Counts by alert type
    cur.execute(f"SELECT type, COUNT(*) as count FROM alerts{query_filter} GROUP BY type;", tuple(params))
    by_type = {r['type']: r['count'] for r in cur.fetchall()}

    # Counts by alert severity
    cur.execute(f"SELECT severity, COUNT(*) as count FROM alerts{query_filter} GROUP BY severity;", tuple(params))
    by_severity = {r['severity']: r['count'] for r in cur.fetchall()}

    cur.close()
    conn.close()

    return jsonify({
        "byType": by_type,
        "bySeverity": by_severity
    })

@stats_bp.route('/methods', methods=['GET'])
def get_stats_methods():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT methods FROM detections;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    counts = {"rule": 0, "statistical": 0, "combined": 0}
    for r in rows:
        m = r["methods"]
        if isinstance(m, list):
            if len(m) > 1:
                counts["combined"] += 1
            elif "rule" in m:
                counts["rule"] += 1
            elif "statistical" in m:
                counts["statistical"] += 1

    return jsonify(counts)

@stats_bp.route('/quality', methods=['GET'])
def get_quality_stats():
    run_id = request.args.get('runId')
    conn = get_db()
    cur = conn.cursor()

    if run_id:
        cur.execute("""
            SELECT run_id, tp, fp, fn, tn, precision, recall, f1, fpr, fnr, detected_attacks
            FROM evaluation_runs WHERE run_id = %s;
        """, (run_id,))
    else:
        cur.execute("""
            SELECT run_id, tp, fp, fn, tn, precision, recall, f1, fpr, fnr, detected_attacks
            FROM evaluation_runs ORDER BY timestamp DESC LIMIT 1;
        """)
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({
            "runId": "none",
            "TP": 0, "FP": 0, "FN": 0, "TN": 0,
            "precision": 0.0, "recall": 0.0, "F1": 0.0,
            "FPR": 0.0, "FNR": 0.0,
            "detected_attacks": []
        })

    return jsonify({
        "runId": row["run_id"],
        "TP": row["tp"],
        "FP": row["fp"],
        "FN": row["fn"],
        "TN": row["tn"],
        "precision": row["precision"],
        "recall": row["recall"],
        "F1": row["f1"],
        "FPR": row["fpr"],
        "FNR": row["fnr"],
        "detectedAttacks": row["detected_attacks"]
    })