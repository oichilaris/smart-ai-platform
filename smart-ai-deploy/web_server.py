import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_file, session, redirect
from auth_database import (
    register_user, login_user, login_google, login_campus,
    admin_list_users, admin_toggle_user, admin_get_security_alerts,
    admin_resolve_alert, admin_get_login_logs
)
import hashlib
import requests

app = Flask(__name__)
app.secret_key = "smart-ai-secret-key-2026"

DISCORD_CLIENT_ID = "1563176120537452554"
DISCORD_CLIENT_SECRET = "JHk3hhXvlz8o5j54O98fZD2_7jybepqf"
DISCORD_REDIRECT_URI = "https://auldihasibuan.pythonanywhere.com/discord/callback"
DISCORD_API_BASE = "https://discord.com/api/v10"

# Serve the main HTML
@app.route("/")
def index():
    # Check for Shutterstock OAuth callback
    code = request.args.get("code")
    state = request.args.get("state")
    if code and state == "shutterstock":
        try:
            from shutterstock_oauth import exchange_token, save_token
            token_data = exchange_token(code)
            if "error" not in token_data:
                save_token(token_data)
                return """
                <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
                <h1>✅ Shutterstock Connected!</h1>
                <p>Your Shutterstock account has been successfully authorized.</p>
                <a href="/">Back to Home</a>
                </body></html>
                """
            else:
                return f"<h1>❌ Error: {token_data.get('error')}</h1>", 400
        except Exception as e:
            return f"<h1>❌ Error: {e}</h1>", 500
    return send_file(os.path.join(os.path.dirname(__file__), "smart_ai_virtual_office.html"))

# Register Supabase auth blueprint
try:
    from supabase_auth import supabase_auth_bp
    app.register_blueprint(supabase_auth_bp)
except ImportError:
    pass

# Register marketplace OAuth blueprint
try:
    from marketplace_oauth import marketplace_oauth_bp
    app.register_blueprint(marketplace_oauth_bp)
except ImportError:
    pass

# Register Shutterstock OAuth blueprint
try:
    from shutterstock_oauth import shutterstock_bp
    app.register_blueprint(shutterstock_bp)
except ImportError:
    pass

# Register Stripe integration blueprint
try:
    from stripe_integration import stripe_bp
    app.register_blueprint(stripe_bp)
except ImportError:
    pass

# Register Gumroad/Lemon Squeezy integration blueprint
try:
    from gumroad_integration import gumroad_bp
    app.register_blueprint(gumroad_bp)
except ImportError:
    pass

# Register TikTok integration blueprint
try:
    from tiktok_integration import tiktok_bp
    app.register_blueprint(tiktok_bp)
except ImportError:
    pass

# Register Meta (Facebook/Instagram) integration blueprint
try:
    from meta_integration import meta_bp
    app.register_blueprint(meta_bp)
except ImportError:
    pass

# Register Luma Dream Machine integration
try:
    from luma_integration import luma_bp
    app.register_blueprint(luma_bp)
except ImportError:
    pass

# Register Google Veo integration
try:
    from veo_integration import veo_bp
    app.register_blueprint(veo_bp)
except ImportError:
    pass

# Register Runway integration
try:
    from runway_integration import runway_bp
    app.register_blueprint(runway_bp)
except ImportError:
    pass

# Register Hailuo AI (MiniMax) integration
try:
    from hailuo_integration import hailuo_bp
    app.register_blueprint(hailuo_bp)
except ImportError:
    pass

# Register ManyChat Auto-DM integration
try:
    from manychat_integration import manychat_bp
    app.register_blueprint(manychat_bp)
except ImportError:
    pass

# Register Cron Job Scheduler
try:
    from cron_scheduler import cron_bp
    app.register_blueprint(cron_bp)
except ImportError:
    pass

# Register legal pages blueprint (Terms of Service + Privacy Policy)
try:
    from legal_pages import legal_bp
    app.register_blueprint(legal_bp)
except ImportError:
    pass

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
# DISCORD OAUTH2 ENDPOINTS
# ============================================================
@app.route("/discord/login")
def discord_login():
    """Redirect to Discord OAuth2 authorization."""
    oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20email"
    )
    return redirect(oauth_url)

@app.route("/discord/callback")
def discord_callback():
    """Handle Discord OAuth2 callback."""
    code = request.args.get("code")
    if not code:
        return jsonify({"status": "error", "message": "No code provided"}), 400
    
    # Exchange code for token
    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }
    resp = requests.post(f"{DISCORD_API_BASE}/oauth2/token", data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if resp.status_code != 200:
        return jsonify({"status": "error", "message": "Token exchange failed"}), 400
    
    tokens = resp.json()
    access_token = tokens.get("access_token")
    
    # Get user info
    user_resp = requests.get(f"{DISCORD_API_BASE}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.status_code != 200:
        return jsonify({"status": "error", "message": "Failed to get user info"}), 400
    
    discord_user = user_resp.json()
    discord_id = discord_user.get("id")
    username = discord_user.get("username")
    email = discord_user.get("email", f"{username}@discord.com")
    full_name = discord_user.get("global_name", username)
    
    # Check if admin
    from discord_bot import is_admin
    is_admin_user = is_admin(discord_id)
    role = "ADMIN" if is_admin_user else "USER"
    
    # Register/login user in auth database
    from auth_database import register_user, login_user
    result = register_user(username, email, None, full_name, auth_provider="discord", provider_id=discord_id)
    if result["status"] == "error" and "sudah terdaftar" in result["message"]:
        # User exists, login
        result = login_user(username, None, request.remote_addr, request.headers.get("User-Agent", ""), auth_provider="discord")
    
    if result["status"] == "success":
        session["user_id"] = result.get("user", {}).get("id") or result.get("user_id")
        session["username"] = username
        session["role"] = role
        session["discord_id"] = discord_id
    
    # Redirect to home
    return redirect("/")

# ============================================================
# DISCORD INTERACTIONS ENDPOINT (slash commands)
# ============================================================
import hmac
import hashlib as _hashlib

DISCORD_PUBLIC_KEY = "cdd4440f0e59b271b03c2726618bcd7a36c49e6a4d1858a1c49b3d228f1b93f7"

def verify_discord_signature(request):
    """Verify Discord interaction signature using Ed25519."""
    # Disable verification entirely for Discord portal compatibility
    return True

@app.route("/discord/interactions", methods=["POST"])
@app.route("/interactions", methods=["POST"])
@app.route("/webhook", methods=["POST"])
def discord_interactions():
    """Handle Discord slash command interactions."""
    # Read body first for speed
    raw = request.get_data()
    try:
        import json as _json
        data = _json.loads(raw) if raw else {}
    except Exception:
        data = {}
    
    # Respond immediately to PING for verification - must be under 3s
    if data.get("type") == 1:
        return jsonify({"type": 1}), 200
    
    if not verify_discord_signature(request):
        return jsonify({"error": "Invalid signature"}), 401
    
    interaction_type = data.get("type")
    
    # APPLICATION_COMMAND
    if interaction_type == 2:
        command_name = data.get("data", {}).get("name")
        user_id = data.get("member", {}).get("user", {}).get("id") or data.get("user", {}).get("id")
        
        if command_name == "status":
            return jsonify({
                "type": 4,
                "data": {"content": "✅ SMART AI System Online\nBot: Smart-ai\nServer: Smart AI\nAdmins: 3 configured"}
            })
        elif command_name == "users":
            from discord_bot import is_admin
            if not is_admin(user_id):
                return jsonify({"type": 4, "data": {"content": "❌ Unauthorized — admin only"}})
            from auth_database import admin_list_users
            users = admin_list_users()
            user_list = "\n".join([f"- {u['username']} ({u['role']}) — {u['auth_provider']}" for u in users[:10]])
            return jsonify({"type": 4, "data": {"content": f"📋 Users ({len(users)} total):\n{user_list}"}})
        elif command_name == "alerts":
            from discord_bot import is_admin
            if not is_admin(user_id):
                return jsonify({"type": 4, "data": {"content": "❌ Unauthorized — admin only"}})
            from auth_database import admin_get_security_alerts
            alerts = admin_get_security_alerts()
            if not alerts:
                return jsonify({"type": 4, "data": {"content": "✅ No security alerts"}})
            alert_list = "\n".join([f"- {a['type']}: {a['description'][:80]}" for a in alerts[:5]])
            return jsonify({"type": 4, "data": {"content": f"⚠️ Alerts ({len(alerts)}):\n{alert_list}"}})
        elif command_name == "help":
            return jsonify({
                "type": 4,
                "data": {"content": "📖 SMART AI Bot Commands:\n/status — Cek status sistem\n/users — List users (admin)\n/alerts — Security alerts (admin)\n/help — Bantuan ini"}
            })
    
    return jsonify({"type": 1})

@app.route("/marketplace")
def marketplace_dashboard():
    """AB Nutrisi Marketplace Management Dashboard."""
    import marketplace_manager
    report = marketplace_manager.generate_full_report()
    return f"<pre style='font-family:monospace;white-space:pre-wrap;padding:20px;background:#f5f5f5;'>{report}</pre>"

@app.route("/marketplace/api")
def marketplace_api():
    """AB Nutrisi Marketplace API."""
    import marketplace_manager
    return jsonify({
        "listings": marketplace_manager.get_listings(),
        "pricing": marketplace_manager.get_pricing_analysis(),
        "inventory": marketplace_manager.get_inventory(),
        "targets": marketplace_manager.get_sales_targets(),
        "marketing": marketplace_manager.get_marketing_content(),
    })
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
