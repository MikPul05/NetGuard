from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Basic token store for demo / development
SESSIONS = {
    "token-admin-123": {"username": "admin", "role": "admin"},
    "token-operator-456": {"username": "operator", "role": "operator"}
}

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    # Role separation mock logic
    if username == "admin" and password == "admin":
        return jsonify({
            "token": "token-admin-123",
            "refreshToken": "refresh-admin-123",
            "user": {"username": "admin", "role": "admin"}
        })
    elif username == "operator" and password == "operator":
        return jsonify({
            "token": "token-operator-456",
            "refreshToken": "refresh-operator-456",
            "user": {"username": "operator", "role": "operator"}
        })
    return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    return jsonify({"token": "token-admin-123"})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"status": "logged out"})

@auth_bp.route('/me', methods=['GET'])
def get_me():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    user = SESSIONS.get(token, {"username": "operator", "role": "operator"})
    return jsonify(user)