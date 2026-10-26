import os
import json
import logging
import requests
from datetime import datetime
from urllib.parse import urlencode
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MKT-OAUTH]: %(message)s")
logger = logging.getLogger("MKT-OAUTH")

# ============================================================
# MARKETPLACE OAUTH2 CONFIGURATION
# ============================================================

# Shopee Open Platform
SHOPEE_CONFIG = {
    "name": "Shopee",
    "client_id": "",  # Shopee Partner ID
    "client_secret": "",  # Shopee Partner Key
    "auth_url": "https://partner.shopeemobile.com/api/v2/shop/auth_partner",
    "token_url": "https://partner.shopeemobile.com/api/v2/auth/token/get",
    "redirect_uri": "https://auldihasibuan.pythonanywhere.com/marketplace/oauth/shopee/callback",
    "scopes": ["shop_info", "item", "order"],
}

# Tokopedia Open API
TOKOPEDIA_CONFIG = {
    "name": "Tokopedia",
    "client_id": "",  # Tokopedia Client ID
    "client_secret": "",  # Tokopedia Client Secret
    "auth_url": "https://accounts.tokopedia.com/authorize",
    "token_url": "https://accounts.tokopedia.com/token",
    "redirect_uri": "https://auldihasibuan.pythonanywhere.com/marketplace/oauth/tokopedia/callback",
    "scopes": ["shop", "product", "order"],
}

# Lazada Open Platform
LAZADA_CONFIG = {
    "name": "Lazada",
    "client_id": "",  # Lazada App Key
    "client_secret": "",  # Lazada App Secret
    "auth_url": "https://auth.lazada.com/oauth/authorize",
    "token_url": "https://auth.lazada.com/rest/auth/token/create",
    "redirect_uri": "https://auldihasibuan.pythonanywhere.com/marketplace/oauth/lazada/callback",
    "scopes": [],
}

PLATFORMS = {
    "shopee": SHOPEE_CONFIG,
    "tokopedia": TOKOPEDIA_CONFIG,
    "lazada": LAZADA_CONFIG,
}

# In-memory token storage (replace with database in production)
TOKENS = {}

def get_auth_url(platform: str) -> str:
    """Generate OAuth authorization URL for a platform."""
    config = PLATFORMS.get(platform)
    if not config:
        return None
    
    if platform == "shopee":
        params = {
            "partner_id": config["client_id"],
            "redirect": config["redirect_uri"],
            "state": platform,
        }
        return f"{config['auth_url']}?{urlencode(params)}"
    
    elif platform == "tokopedia":
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(config["scopes"]),
            "state": platform,
        }
        return f"{config['auth_url']}?{urlencode(params)}"
    
    elif platform == "lazada":
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "state": platform,
        }
        return f"{config['auth_url']}?{urlencode(params)}"
    
    return None

def exchange_token(platform: str, code: str) -> Dict:
    """Exchange authorization code for access token."""
    config = PLATFORMS.get(platform)
    if not config:
        return {"error": "Unknown platform"}
    
    if platform == "shopee":
        data = {
            "partner_id": config["client_id"],
            "partner_key": config["client_secret"],
            "code": code,
            "shop_id": 0,  # Will be filled from callback
        }
        resp = requests.post(config["token_url"], json=data)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    
    elif platform == "tokopedia":
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config["redirect_uri"],
        }
        resp = requests.post(config["token_url"], data=data)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    
    elif platform == "lazada":
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config["redirect_uri"],
        }
        resp = requests.post(config["token_url"], data=data)
        return resp.json() if resp.status_code == 200 else {"error": resp.text}
    
    return {"error": "Unsupported platform"}

def save_token(platform: str, token_data: Dict):
    """Save OAuth token for a platform."""
    TOKENS[platform] = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_at": token_data.get("expires_in", 3600),
        "saved_at": datetime.now().isoformat(),
    }
    logger.info(f"Token saved for {platform}")

def get_token(platform: str) -> Dict:
    """Get stored OAuth token for a platform."""
    return TOKENS.get(platform)

def get_status() -> Dict:
    """Get OAuth connection status for all platforms."""
    status = {}
    for platform, config in PLATFORMS.items():
        token = TOKENS.get(platform)
        status[platform] = {
            "name": config["name"],
            "connected": token is not None,
            "has_credentials": bool(config["client_id"] and config["client_secret"]),
            "auth_url": get_auth_url(platform) if config["client_id"] else None,
        }
    return status

# ============================================================
# FLASK BLUEPRINT
# ============================================================
from flask import Blueprint, request, jsonify, redirect

marketplace_oauth_bp = Blueprint("marketplace_oauth", __name__)

@marketplace_oauth_bp.route("/marketplace/oauth/<platform>")
def oauth_start(platform):
    """Start OAuth flow for a marketplace platform."""
    config = PLATFORMS.get(platform)
    if not config:
        return jsonify({"error": "Unknown platform"}), 404
    
    if not config["client_id"]:
        return jsonify({
            "error": "Platform not configured",
            "message": f"Set {platform.upper()}_CLIENT_ID and {platform.upper()}_CLIENT_SECRET in environment",
            "platform": platform
        }), 400
    
    auth_url = get_auth_url(platform)
    if not auth_url:
        return jsonify({"error": "Failed to generate auth URL"}), 500
    
    return redirect(auth_url)

@marketplace_oauth_bp.route("/marketplace/oauth/<platform>/callback")
def oauth_callback(platform):
    """Handle OAuth callback from marketplace platform."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    
    token_data = exchange_token(platform, code)
    if "error" in token_data:
        return jsonify({"error": token_data["error"]}), 400
    
    save_token(platform, token_data)
    
    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>✅ {platform.title()} Connected!</h1>
    <p>Marketplace account successfully authorized.</p>
    <a href="/marketplace">Back to Marketplace Dashboard</a>
    </body></html>
    """

@marketplace_oauth_bp.route("/marketplace/oauth/status")
def oauth_status():
    """Get OAuth connection status for all platforms."""
    return jsonify(get_status())

if __name__ == "__main__":
    print("=== MARKETPLACE OAUTH STATUS ===")
    status = get_status()
    for platform, info in status.items():
        print(f"\n{info['name']}:")
        print(f"  Connected: {info['connected']}")
        print(f"  Has Credentials: {info['has_credentials']}")
        if info['auth_url']:
            print(f"  Auth URL: {info['auth_url'][:80]}...")
    print("\n=== CONFIGURATION NEEDED ===")
    print("Set these environment variables:")
    print("  SHOPEE_CLIENT_ID, SHOPEE_CLIENT_SECRET")
    print("  TOKOPEDIA_CLIENT_ID, TOKOPEDIA_CLIENT_SECRET")
    print("  LAZADA_CLIENT_ID, LAZADA_CLIENT_SECRET")