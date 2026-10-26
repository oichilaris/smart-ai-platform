import os
import json
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [DISCORD]: %(message)s")
logger = logging.getLogger("DISCORD")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")

# Admin Discord IDs
ADMINS = {
    "hermes": "1563176120537452554",  # Bot itself
    "auldi": "1422256862794875035",  # User's Discord ID
    "ferdy": "764909284454039563",  # Ferdy's Discord ID
}

HEADERS = {
    "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
    "Content-Type": "application/json"
}

def discord_request(method, endpoint, data=None):
    """Make a request to Discord API."""
    url = f"{DISCORD_API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, json=data, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=HEADERS, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=HEADERS, timeout=10)
        else:
            return None
        return resp.json() if resp.status_code < 400 else {"error": resp.status_code, "message": resp.text}
    except Exception as e:
        logger.error(f"Discord API error: {e}")
        return {"error": str(e)}

def get_bot_info():
    """Get bot information."""
    return discord_request("GET", "/users/@me")

def get_guilds():
    """Get list of guilds (servers) the bot is in."""
    return discord_request("GET", "/users/@me/guilds")

def send_message(channel_id, content, embed=None):
    """Send a message to a Discord channel."""
    data = {"content": content}
    if embed:
        data["embeds"] = [embed]
    return discord_request("POST", f"/channels/{channel_id}/messages", data)

def create_embed(title, description, color=0x00d4ff, fields=None):
    """Create a Discord embed."""
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "SMART AI Platform"}
    }
    if fields:
        embed["fields"] = fields
    return embed

def notify_smart_ai(channel_id, message_type, data):
    """Send SMART AI notifications to Discord."""
    if message_type == "login":
        embed = create_embed(
            "🔐 Login Baru",
            f"User **{data.get('username')}** login via {data.get('provider', 'local')}",
            color=0x22c55e,
            fields=[
                {"name": "IP", "value": data.get('ip', 'N/A'), "inline": True},
                {"name": "Waktu", "value": datetime.now().strftime("%d/%m/%Y %H:%M"), "inline": True}
            ]
        )
    elif message_type == "register":
        embed = create_embed(
            "📝 Registrasi Baru",
            f"User baru: **{data.get('username')}** ({data.get('email')})",
            color=0xa855f7
        )
    elif message_type == "security_alert":
        embed = create_embed(
            "⚠️ Security Alert",
            data.get('description', 'Suspicious activity detected'),
            color=0xef4444,
            fields=[
                {"name": "Severity", "value": data.get('severity', 'WARNING'), "inline": True},
                {"name": "IP", "value": data.get('ip', 'N/A'), "inline": True}
            ]
        )
    elif message_type == "system":
        embed = create_embed(
            "📊 System Status",
            data.get('message', 'System online'),
            color=0x00d4ff
        )
    else:
        embed = create_embed("📢 Notifikasi", str(data), color=0x00d4ff)
    
    return send_message(channel_id, "", embed)

def is_admin(discord_user_id):
    """Check if a Discord user is an admin."""
    return discord_user_id in ADMINS.values() or discord_user_id == ADMINS["hermes"]

def set_admin(name, discord_id):
    """Set an admin's Discord ID."""
    ADMINS[name] = discord_id
    logger.info(f"Admin set: {name} = {discord_id}")

# Flask blueprint for Discord webhook
from flask import Blueprint, request, jsonify

discord_bp = Blueprint("discord", __name__)

@discord_bp.route("/discord/webhook", methods=["POST"])
def discord_webhook():
    """Handle Discord interactions."""
    data = request.json
    interaction_type = data.get("type")
    
    if interaction_type == 1:  # PING
        return jsonify({"type": 1})
    
    if interaction_type == 2:  # APPLICATION_COMMAND
        command_name = data.get("data", {}).get("name")
        user_id = data.get("member", {}).get("user", {}).get("id")
        
        if command_name == "status":
            return jsonify({
                "type": 4,
                "data": {"content": "✅ SMART AI System Online | Discord Bot Connected"}
            })
        elif command_name == "users":
            if not is_admin(user_id):
                return jsonify({"type": 4, "data": {"content": "❌ Unauthorized"}})
            from auth_database import admin_list_users
            users = admin_list_users()
            user_list = "\n".join([f"- {u['username']} ({u['role']})" for u in users[:10]])
            return jsonify({"type": 4, "data": {"content": f"📋 Users:\n{user_list}"}})
        elif command_name == "alerts":
            if not is_admin(user_id):
                return jsonify({"type": 4, "data": {"content": "❌ Unauthorized"}})
            from auth_database import admin_get_security_alerts
            alerts = admin_get_security_alerts()
            if not alerts:
                return jsonify({"type": 4, "data": {"content": "✅ No security alerts"}})
            alert_list = "\n".join([f"- {a['type']}: {a['description']}" for a in alerts[:5]])
            return jsonify({"type": 4, "data": {"content": f"⚠️ Alerts:\n{alert_list}"}})
    
    return jsonify({"type": 1})

@discord_bp.route("/discord/notify", methods=["POST"])
def discord_notify():
    """Send notification to Discord from SMART AI."""
    data = request.json
    channel_id = data.get("channel_id")
    message_type = data.get("type", "system")
    payload = data.get("data", {})
    
    if not channel_id:
        return jsonify({"status": "error", "message": "channel_id required"}), 400
    
    result = notify_smart_ai(channel_id, message_type, payload)
    return jsonify({"status": "success", "result": result})

if __name__ == "__main__":
    print("=== DISCORD BOT MODULE ===")
    info = get_bot_info()
    print(f"Bot: {info.get('username')} (ID: {info.get('id')})")
    guilds = get_guilds()
    print(f"Guilds: {len(guilds) if isinstance(guilds, list) else guilds}")
    if isinstance(guilds, list):
        for g in guilds:
            print(f"  - {g['name']} (ID: {g['id']})")
    print("=== ADMINS ===")
    for name, did in ADMINS.items():
        print(f"  {name}: {did}")
    print("=== DONE ===")
