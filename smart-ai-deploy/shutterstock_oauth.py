import os
import json
import logging
import requests
from datetime import datetime
from urllib.parse import urlencode
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [SHUTTERSTOCK-OAUTH]: %(message)s")
logger = logging.getLogger("SHUTTERSTOCK-OAUTH")

# ============================================================
# SHUTTERSTOCK OAUTH2 CONFIGURATION
# ============================================================

SHUTTERSTOCK_CONFIG = {
    "name": "Shutterstock",
    "client_id": os.getenv("SHUTTERSTOCK_CLIENT_ID", "xpnUDwCm7Nk33qDWItejOAAaslTZLClz"),
    "client_secret": os.getenv("SHUTTERSTOCK_CLIENT_SECRET", "i5qz2ga6SsXZYLUZ"),
    "auth_url": "https://api.shutterstock.com/v2/oauth/authorize",
    "token_url": "https://api.shutterstock.com/v2/oauth/access_token",
    "api_base": "https://api.shutterstock.com/v2",
    "redirect_uri": "https://auldihasibuan.pythonanywhere.com",
    "scopes": [
        "user.view",
        "licenses.view",
        "licenses.create",
        "collections.view",
        "collections.edit",
        "media.upload",
    ],
}

# In-memory token storage (replace with database in production)
TOKENS = {}

# ============================================================
# OAUTH2 FUNCTIONS
# ============================================================

def get_auth_url() -> Optional[str]:
    """Generate OAuth authorization URL for Shutterstock."""
    config = SHUTTERSTOCK_CONFIG
    if not config["client_id"]:
        return None
    
    params = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "state": "shutterstock",
    }
    return f"{config['auth_url']}?{urlencode(params)}"


def exchange_token(code: str) -> Dict:
    """Exchange authorization code for access token."""
    config = SHUTTERSTOCK_CONFIG
    if not config["client_id"] or not config["client_secret"]:
        return {"error": "Shutterstock credentials not configured"}
    
    data = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config["redirect_uri"],
    }
    
    try:
        import base64
        credentials = base64.b64encode(f"{config['client_id']}:{config['client_secret']}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        resp = requests.post(config["token_url"], data=data, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"Token exchange failed: {resp.status_code} {resp.text}")
            return {"error": resp.text, "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        return {"error": str(e)}


def save_token(token_data: Dict):
    """Save OAuth token."""
    TOKENS["shutterstock"] = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_in": token_data.get("expires_in", 3600),
        "scope": token_data.get("scope", ""),
        "saved_at": datetime.now().isoformat(),
    }
    logger.info("Shutterstock token saved")


def get_token() -> Optional[Dict]:
    """Get stored OAuth token."""
    return TOKENS.get("shutterstock")


def get_status() -> Dict:
    """Get OAuth connection status."""
    config = SHUTTERSTOCK_CONFIG
    token = TOKENS.get("shutterstock")
    return {
        "name": "Shutterstock",
        "connected": token is not None,
        "has_credentials": bool(config["client_id"] and config["client_secret"]),
        "auth_url": get_auth_url() if config["client_id"] else None,
        "scopes": config["scopes"],
        "api_base": config["api_base"],
    }


# ============================================================
# SHUTTERSTOCK API FUNCTIONS
# ============================================================

def _api_request(method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
    """Make authenticated API request to Shutterstock."""
    token = get_token()
    if not token or not token.get("access_token"):
        return {"error": "Not authenticated. Please connect Shutterstock first."}
    
    config = SHUTTERSTOCK_CONFIG
    url = f"{config['api_base']}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json",
    }
    
    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if resp.status_code in (200, 201, 204):
            try:
                return resp.json()
            except:
                return {"status": "success", "status_code": resp.status_code}
        else:
            logger.error(f"API error: {resp.status_code} {resp.text}")
            return {"error": resp.text, "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"API request error: {e}")
        return {"error": str(e)}


def search_images(query: str, per_page: int = 20, page: int = 1, 
                  image_type: str = None, orientation: str = None) -> Dict:
    """Search for images on Shutterstock."""
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
    }
    if image_type:
        params["image_type"] = image_type  # photo, illustration, vector
    if orientation:
        params["orientation"] = orientation  # horizontal, vertical, square
    
    return _api_request("GET", "/images/search", params=params)


def search_videos(query: str, per_page: int = 20, page: int = 1) -> Dict:
    """Search for videos on Shutterstock."""
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
    }
    return _api_request("GET", "/videos/search", params=params)


def get_image_details(image_id: str) -> Dict:
    """Get detailed information about an image."""
    return _api_request("GET", f"/images/{image_id}")


def get_user_info() -> Dict:
    """Get authenticated user's profile info."""
    return _api_request("GET", "/user")


def get_licenses() -> Dict:
    """Get user's license history."""
    return _api_request("GET", "/user/licenses")


def create_collection(name: str, description: str = "") -> Dict:
    """Create a new collection (lightbox)."""
    data = {
        "name": name,
        "description": description,
    }
    return _api_request("POST", "/collections", data=data)


def get_collections() -> Dict:
    """Get user's collections."""
    return _api_request("GET", "/collections")


def add_to_collection(collection_id: str, media_ids: List[str]) -> Dict:
    """Add media to a collection."""
    data = {"items": [{"id": mid, "media_type": "image"} for mid in media_ids]}
    return _api_request("POST", f"/collections/{collection_id}/items", data=data)


# ============================================================
# FLASK BLUEPRINT
# ============================================================

from flask import Blueprint, request, jsonify, redirect

shutterstock_bp = Blueprint("shutterstock", __name__)


@shutterstock_bp.route("/shutterstock/oauth")
def oauth_start():
    """Start OAuth flow for Shutterstock."""
    config = SHUTTERSTOCK_CONFIG
    if not config["client_id"]:
        return jsonify({
            "error": "Shutterstock not configured",
            "message": "Set SHUTTERSTOCK_CLIENT_ID and SHUTTERSTOCK_CLIENT_SECRET in environment",
        }), 400
    
    auth_url = get_auth_url()
    if not auth_url:
        return jsonify({"error": "Failed to generate auth URL"}), 500
    
    return redirect(auth_url)


@shutterstock_bp.route("/shutterstock/oauth/callback")
def oauth_callback():
    """Handle OAuth callback from Shutterstock."""
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error:
        return f"""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
        <h1>❌ Authorization Failed</h1>
        <p>Error: {error}</p>
        <p>{request.args.get('error_description', '')}</p>
        <a href="/shutterstock">Back</a>
        </body></html>
        """, 400
    
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    
    token_data = exchange_token(code)
    if "error" in token_data:
        return jsonify({"error": token_data["error"]}), 400
    
    save_token(token_data)
    
    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>✅ Shutterstock Connected!</h1>
    <p>Your Shutterstock account has been successfully authorized.</p>
    <p>Scopes: {token_data.get('scope', 'N/A')}</p>
    <a href="/shutterstock">Back to Shutterstock Dashboard</a>
    </body></html>
    """


@shutterstock_bp.route("/shutterstock/oauth/status")
def oauth_status():
    """Get OAuth connection status."""
    return jsonify(get_status())


@shutterstock_bp.route("/shutterstock/search")
def search():
    """Search images on Shutterstock."""
    query = request.args.get("q", "")
    per_page = int(request.args.get("per_page", 20))
    page = int(request.args.get("page", 1))
    image_type = request.args.get("type")
    orientation = request.args.get("orientation")
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    result = search_images(query, per_page=per_page, page=page, 
                          image_type=image_type, orientation=orientation)
    return jsonify(result)


@shutterstock_bp.route("/shutterstock/user")
def user_info():
    """Get authenticated user info."""
    result = get_user_info()
    return jsonify(result)


@shutterstock_bp.route("/shutterstock/licenses")
def licenses():
    """Get user's license history."""
    result = get_licenses()
    return jsonify(result)


@shutterstock_bp.route("/shutterstock/collections")
def collections():
    """Get user's collections."""
    result = get_collections()
    return jsonify(result)


@shutterstock_bp.route("/shutterstock/collections/create", methods=["POST"])
def create_collection_endpoint():
    """Create a new collection."""
    data = request.get_json() or {}
    name = data.get("name", "")
    description = data.get("description", "")
    
    if not name:
        return jsonify({"error": "Collection name is required"}), 400
    
    result = create_collection(name, description)
    return jsonify(result)


if __name__ == "__main__":
    print("=== SHUTTERSTOCK OAUTH STATUS ===")
    status = get_status()
    print(f"\nName: {status['name']}")
    print(f"Connected: {status['connected']}")
    print(f"Has Credentials: {status['has_credentials']}")
    if status['auth_url']:
        print(f"Auth URL: {status['auth_url'][:80]}...")
    print("\n=== CONFIGURATION NEEDED ===")
    print("Set these environment variables:")
    print("  SHUTTERSTOCK_CLIENT_ID")
    print("  SHUTTERSTOCK_CLIENT_SECRET")
    print("\n=== API ENDPOINTS ===")
    print("  GET  /shutterstock/oauth          - Start OAuth flow")
    print("  GET  /shutterstock/oauth/callback  - OAuth callback")
    print("  GET  /shutterstock/oauth/status    - Connection status")
    print("  GET  /shutterstock/search?q=...    - Search images")
    print("  GET  /shutterstock/user            - User profile")
    print("  GET  /shutterstock/licenses        - License history")
    print("  GET  /shutterstock/collections     - List collections")
    print("  POST /shutterstock/collections/create - Create collection")