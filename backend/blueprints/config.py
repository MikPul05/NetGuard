from flask import Blueprint, request, jsonify
import psycopg2
import tomli_w
import tomllib
import os

config_bp = Blueprint('config', __name__)
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config.toml")

DEFAULT_CONFIG = {
    "rules": {
        "port_scan": {"enabled": True, "window_seconds": 10, "min_unique_dst_ports": 20},
        "brute_force": {"enabled": True, "window_seconds": 60, "ports": [21, 22, 23, 3389], "min_attempts": 10},
        "dos": {"enabled": True, "window_seconds": 10, "min_attempts_to_destination": 100, "max_unique_dst_ports": 5}
    },
    "statistical": {
        "enabled": True,
        "window_seconds": 10,
        "baseline_seconds": 30,
        "z_threshold": 3.0,
        "min_std": 1.0,
        "features": ["connection_attempts", "unique_dst_ports", "unique_dst_ips", "byte_count"]
    },
    "evaluation": {"window_seconds": 10}
}

@config_bp.route('/config/detection', methods=['GET'])
def get_detection_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "rb") as f:
                return jsonify(tomllib.load(f))
        except Exception:
            pass
    return jsonify(DEFAULT_CONFIG)

@config_bp.route('/config/detection', methods=['PUT'])
def update_detection_config():
    new_cfg = request.get_json() or {}
    auth_header = request.headers.get("Authorization", "")
    username = "admin" if "admin" in auth_header else "system"

    # Write config to disk
    try:
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(new_cfg, f)
    except Exception as e:
        return jsonify({"error": f"Failed to save config: {str(e)}"}), 500

    # Write audit log (NFR06)
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_logs (username, action) VALUES (%s, %s);",
            (username, f"Updated detection config sections: {list(new_cfg.keys())}")
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"warning": f"Config saved but audit failed: {str(e)}", "config": new_cfg}), 200

    return jsonify({"status": "success", "config": new_cfg})

@config_bp.route('/sources/', methods=['GET'])
def get_sources():
    # Return available PCAP/flow data sources from the data volume or DB
    data_dir = "/data"
    sources = []
    if os.path.exists(data_dir):
        sources = [f for f in os.listdir(data_dir) if f.endswith(('.pcap', '.pcapng', '.jsonl'))]
    if not sources:
        sources = ["sample_capture.pcap", "normal_traffic.jsonl"]
    return jsonify({"sources": sources})

@config_bp.route('/runs', methods=['GET'])
def get_runs():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT run_id FROM evaluation_runs;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    runs = [r[0] for r in rows] if rows else ["run-001-baseline", "run-002-portscan"]
    return jsonify({"runs": runs})