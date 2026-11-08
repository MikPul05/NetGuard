import os
import socket
import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS
from blueprints.alerts import alerts_bp
from blueprints.detections import detections_bp
from blueprints.traffic import traffic_bp
from blueprints.auth import auth_bp
from blueprints.stats import stats_bp
from blueprints.config import config_bp

app = Flask(__name__)
CORS(app)
DB_URL = os.getenv("DATABASE_URL", "postgresql://netguard_user:netguard_password@db:5432/netguard_db")
KAFKA_HOST = os.getenv("KAFKA_HOST", "kafka")
KAFKA_PORT = int(os.getenv("KAFKA_PORT", 9092))

def check_kafka(host, port, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "healthy"
    except OSError:
        return "unhealthy"

@app.route("/health", methods=["GET"])
def health():
    db_status = "healthy"
    try:
        conn = psycopg2.connect(DB_URL)
        conn.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    kafka_status = check_kafka(KAFKA_HOST, KAFKA_PORT)
    is_ok = db_status == "healthy" and kafka_status == "healthy"

    return jsonify({
        "status": "healthy" if is_ok else "degraded",
        "database": db_status,
        "kafka": kafka_status
    }), (200 if is_ok else 503)

# Register blueprints at module scope
app.register_blueprint(alerts_bp)
app.register_blueprint(detections_bp)
app.register_blueprint(traffic_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(config_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)