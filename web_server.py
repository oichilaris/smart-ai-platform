import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_file, session
from auth_database import (
    register_user, login_user, login_google, login_campus,
    admin_list_users, admin_toggle_user, admin_get_security_alerts,
    admin_resolve_alert, admin_get_login_logs
)
import hashlib

app = Flask(__name__)
app.secret_key = "smart-ai-secret-key-2026"

# Serve the main HTML
@app.route("/")
def index():
    return send_file("G:/AI AGENTS/HERMES/hermes-autonomous/smart_ai_v2.html")

# ============================================================
# AUTH API ENDPOINTS
# ============================================================
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    result = register_user(
        username=data.get("username", ""),
        email=data.get("email", ""),
        password=data.get("password", ""),
        full_name=data.get("full_name", ""),
        auth_provider="local"
    )
    if result["status"] == "success":
        session["user_id"] = result["user_id"]
    return jsonify(result)

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    result = login_user(
        username_or_email=data.get("username", ""),
        password=data.get("password", ""),
        ip_address=ip,
        user_agent=ua,
        auth_provider="local"
    )
    if result["status"] == "success":
        session["user_id"] = result["user"]["id"]
        session["username"] = result["user"]["username"]
        session["role"] = result["user"]["role"]
    return jsonify(result)

@app.route("/api/login/google", methods=["POST"])
def api_login_google():
    data = request.json
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    result = login_google(
        google_id=data.get("google_id", ""),
        email=data.get("email", ""),
        full_name=data.get("full_name", ""),
        ip_address=ip,
        user_agent=ua
    )
    if result["status"] == "success":
        session["user_id"] = result["user"]["id"]
        session["username"] = result["user"]["username"]
        session["role"] = result["user"]["role"]
    return jsonify(result)

@app.route("/api/login/campus", methods=["POST"])
def api_login_campus():
    data = request.json
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    result = login_campus(
        sso_id=data.get("sso_id", ""),
        email=data.get("email", ""),
        full_name=data.get("full_name", ""),
        campus_name=data.get("campus_name", ""),
        ip_address=ip,
        user_agent=ua
    )
    if result["status"] == "success":
        session["user_id"] = result["user"]["id"]
        session["username"] = result["user"]["username"]
        session["role"] = result["user"]["role"]
    return jsonify(result)

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logout berhasil."})

@app.route("/api/user", methods=["GET"])
def api_user():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Not logged in."}), 401
    return jsonify({"status": "success", "user": {
        "id": session["user_id"],
        "username": session.get("username"),
        "role": session.get("role")
    }})

# ============================================================
# ADMIN API ENDPOINTS
# ============================================================
@app.route("/api/admin/users", methods=["GET"])
def api_admin_users():
    if session.get("role") != "ADMIN":
        return jsonify({"status": "error", "message": "Unauthorized."}), 403
    return jsonify({"status": "success", "users": admin_list_users()})

@app.route("/api/admin/toggle-user", methods=["POST"])
def api_admin_toggle():
    if session.get("role") != "ADMIN":
        return jsonify({"status": "error", "message": "Unauthorized."}), 403
    data = request.json
    result = admin_toggle_user(data.get("user_id"), data.get("active", True))
    return jsonify(result)

@app.route("/api/admin/alerts", methods=["GET"])
def api_admin_alerts():
    if session.get("role") != "ADMIN":
        return jsonify({"status": "error", "message": "Unauthorized."}), 403
    return jsonify({"status": "success", "alerts": admin_get_security_alerts()})

@app.route("/api/admin/resolve-alert", methods=["POST"])
def api_admin_resolve():
    if session.get("role") != "ADMIN":
        return jsonify({"status": "error", "message": "Unauthorized."}), 403
    data = request.json
    result = admin_resolve_alert(data.get("alert_id"))
    return jsonify(result)

@app.route("/api/admin/logs", methods=["GET"])
def api_admin_logs():
    if session.get("role") != "ADMIN":
        return jsonify({"status": "error", "message": "Unauthorized."}), 403
    return jsonify({"status": "success", "logs": admin_get_login_logs(50)})

if __name__ == "__main__":
    print("=== SMART AI WEB SERVER ===")
    print("URL: http://localhost:5000")
    print("Auth DB connected")
    app.run(host="0.0.0.0", port=5000, debug=True)
PYEOF