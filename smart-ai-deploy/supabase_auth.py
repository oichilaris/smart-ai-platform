import os
import json
import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [SUPABASE-AUTH]: %(message)s")
logger = logging.getLogger("SUPABASE-AUTH")

# ============================================================
# SUPABASE CONFIGURATION
# ============================================================
SUPABASE_URL = "https://oipbdylxpyvwoaalbegn.supabase.co"
SUPABASE_KEY = ""  # Set via environment variable
SUPABASE_SERVICE_KEY = ""  # Set via environment variable

def get_headers():
    """Get headers for Supabase API requests."""
    key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

# ============================================================
# USER MANAGEMENT
# ============================================================
def register_user(username, email, password_hash, full_name="", role="USER", auth_provider="local", provider_id=None):
    """Register a new user in Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users"
    data = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
        "auth_provider": auth_provider,
        "provider_id": provider_id,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    resp = requests.post(url, json=data, headers=get_headers())
    if resp.status_code in (200, 201):
        return {"status": "success", "user": resp.json()[0] if resp.json() else None}
    return {"status": "error", "message": resp.text}

def get_user_by_username(username):
    """Get user by username from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

def get_user_by_email(email):
    """Get user by email from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users?email=eq.{email}&select=*"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

def get_user_by_id(user_id):
    """Get user by ID from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}&select=*"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None

def update_user(user_id, updates):
    """Update user in Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
    updates["updated_at"] = datetime.now().isoformat()
    resp = requests.patch(url, json=updates, headers=get_headers())
    if resp.status_code in (200, 204):
        return {"status": "success"}
    return {"status": "error", "message": resp.text}

def delete_user(user_id):
    """Delete user from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
    resp = requests.delete(url, headers=get_headers())
    if resp.status_code in (200, 204):
        return {"status": "success"}
    return {"status": "error", "message": resp.text}

# ============================================================
# LOGIN/LOGOUT LOGGING
# ============================================================
def log_login(user_id, username, ip_address, user_agent, auth_provider, status, reason=None):
    """Log login attempt to Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/login_logs"
    data = {
        "user_id": user_id,
        "username": username,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "auth_provider": auth_provider,
        "status": status,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    resp = requests.post(url, json=data, headers=get_headers())
    return resp.status_code in (200, 201)

def get_login_logs(user_id=None, limit=50):
    """Get login logs from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/login_logs?select=*&order=timestamp.desc&limit={limit}"
    if user_id:
        url += f"&user_id=eq.{user_id}"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    return []

# ============================================================
# SECURITY ALERTS
# ============================================================
def create_security_alert(alert_type, severity, description, ip_address=None, user_id=None):
    """Create security alert in Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/security_alerts"
    data = {
        "alert_type": alert_type,
        "severity": severity,
        "description": description,
        "ip_address": ip_address,
        "user_id": user_id,
        "resolved": False,
        "timestamp": datetime.now().isoformat()
    }
    resp = requests.post(url, json=data, headers=get_headers())
    return resp.status_code in (200, 201)

def get_security_alerts(resolved=None, limit=50):
    """Get security alerts from Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/security_alerts?select=*&order=timestamp.desc&limit={limit}"
    if resolved is not None:
        url += f"&resolved=eq.{resolved}"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code == 200:
        return resp.json()
    return []

# ============================================================
# AUTHENTICATION HELPERS
# ============================================================
def hash_password(password):
    """Hash password using SHA-256."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash."""
    return hash_password(password) == password_hash

def authenticate_user(username, password):
    """Authenticate user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return {"status": "error", "message": "User not found"}
    if not user.get("is_active"):
        return {"status": "error", "message": "Account disabled"}
    if user.get("locked_until"):
        locked = datetime.fromisoformat(user["locked_until"])
        if locked > datetime.now():
            return {"status": "error", "message": "Account locked"}
    if verify_password(password, user.get("password_hash", "")):
        # Update last login
        update_user(user["id"], {"last_login": datetime.now().isoformat()})
        return {"status": "success", "user": user}
    return {"status": "error", "message": "Invalid password"}

# ============================================================
# FLASK BLUEPRINT
# ============================================================
from flask import Blueprint, request, jsonify, session

supabase_auth_bp = Blueprint("supabase_auth", __name__)

@supabase_auth_bp.route("/api/supabase/register", methods=["POST"])
def api_supabase_register():
    """Register new user via Supabase."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    
    if not username or not email or not password:
        return jsonify({"status": "error", "message": "Username, email, and password required"}), 400
    
    # Check if user exists
    existing = get_user_by_username(username)
    if existing:
        return jsonify({"status": "error", "message": "Username already exists"}), 409
    
    existing_email = get_user_by_email(email)
    if existing_email:
        return jsonify({"status": "error", "message": "Email already registered"}), 409
    
    # Register
    password_hash = hash_password(password)
    result = register_user(username, email, password_hash, full_name)
    
    if result["status"] == "success":
        user = result["user"]
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return jsonify({"status": "success", "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})
    
    return jsonify(result), 500

@supabase_auth_bp.route("/api/supabase/login", methods=["POST"])
def api_supabase_login():
    """Login user via Supabase."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "")
    
    result = authenticate_user(username, password)
    
    if result["status"] == "success":
        user = result["user"]
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        log_login(user["id"], username, ip, ua, "supabase", "success")
        return jsonify({"status": "success", "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})
    
    log_login(None, username, ip, ua, "supabase", "failed", result["message"])
    return jsonify(result), 401

@supabase_auth_bp.route("/api/supabase/logout", methods=["POST"])
def api_supabase_logout():
    """Logout user from Supabase session."""
    user_id = session.get("user_id")
    username = session.get("username")
    if user_id:
        log_login(user_id, username, request.remote_addr, request.headers.get("User-Agent", ""), "supabase", "logout")
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

@supabase_auth_bp.route("/api/supabase/status", methods=["GET"])
def api_supabase_status():
    """Check if user is logged in via Supabase."""
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
        if user:
            return jsonify({"status": "logged_in", "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})
    return jsonify({"status": "not_logged_in"})

if __name__ == "__main__":
    print("=== SUPABASE AUTH MODULE ===")
    print(f"Supabase URL: {SUPABASE_URL}")
    print("Endpoints: /api/supabase/register, /api/supabase/login, /api/supabase/logout, /api/supabase/status")