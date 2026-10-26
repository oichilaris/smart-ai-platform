import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify, redirect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [THREADS]: %(message)s")
logger = logging.getLogger("THREADS")

THREADS_APP_ID = os.getenv("THREADS_APP_ID", "2042331199817645")
THREADS_APP_SECRET = os.getenv("THREADS_APP_SECRET", "b02eb0f915af3e85d7b4cf86f90810aa")
THREADS_REDIRECT_URI = "https://auldihasibuan.pythonanywhere.com/threads/callback"

threads_bp = Blueprint("threads", __name__)

# --- THREADS: OAuth Login ---
@threads_bp.route("/threads/login")
def threads_login():
    """Redirect to Threads OAuth authorization."""
    if not THREADS_APP_ID:
        return jsonify({"error": "THREADS_APP_ID not set"}), 400
    auth_url = (
        f"https://threads.net/oauth/authorize"
        f"?client_id={THREADS_APP_ID}"
        f"&redirect_uri={THREADS_REDIRECT_URI}"
        f"&scope=threads_basic,threads_content_publish"
        f"&response_type=code"
    )
    return redirect(auth_url)


# --- THREADS: OAuth Callback ---
@threads_bp.route("/threads/callback")
def threads_callback():
    """Handle Threads OAuth callback."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    try:
        resp = requests.post(
            "https://graph.threads.net/oauth/access_token",
            data={
                "client_id": THREADS_APP_ID,
                "client_secret": THREADS_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": THREADS_REDIRECT_URI,
                "code": code,
            },
            timeout=30,
        )
        data = resp.json()
        if "access_token" in data:
            os.environ["THREADS_ACCESS_TOKEN"] = data["access_token"]
            return jsonify({"status": "connected", "token_preview": data["access_token"][:10] + "..."})
        return jsonify({"error": "Token exchange failed", "details": data}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- THREADS: User Profile ---
@threads_bp.route("/threads/user")
def threads_user():
    """Get Threads user profile."""
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    try:
        resp = requests.get(
            "https://graph.threads.net/v1.0/me",
            params={"fields": "id,username,name,threads_profile_picture_url,threads_biography", "access_token": token},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- THREADS: User's Threads ---
@threads_bp.route("/threads/posts")
def threads_posts():
    """Get user's Threads posts."""
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    try:
        resp = requests.get(
            "https://graph.threads.net/v1.0/me/threads",
            params={"fields": "id,text,media_type,media_url,permalink,timestamp,username", "access_token": token},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- THREADS: Create Text Post ---
@threads_bp.route("/threads/post/text", methods=["POST"])
def threads_post_text():
    """Create a text post on Threads."""
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "text required"}), 400
    try:
        # Step 1: Create media container
        resp = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            data={"media_type": "TEXT", "text": text, "access_token": token},
            timeout=30,
        )
        container = resp.json()
        if "id" not in container:
            return jsonify({"error": "Failed to create container", "details": container}), 400
        
        # Step 2: Publish
        resp2 = requests.post(
            "https://graph.threads.net/v1.0/me/threads_publish",
            data={"creation_id": container["id"], "access_token": token},
            timeout=30,
        )
        return jsonify(resp2.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- THREADS: Create Image Post ---
@threads_bp.route("/threads/post/image", methods=["POST"])
def threads_post_image():
    """Create an image post on Threads."""
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    data = request.json or {}
    image_url = data.get("image_url", "")
    text = data.get("text", "")
    if not image_url:
        return jsonify({"error": "image_url required"}), 400
    try:
        resp = requests.post(
            "https://graph.threads.net/v1.0/me/threads",
            data={"media_type": "IMAGE", "image_url": image_url, "text": text, "access_token": token},
            timeout=30,
        )
        container = resp.json()
        if "id" not in container:
            return jsonify({"error": "Failed to create container", "details": container}), 400
        
        resp2 = requests.post(
            "https://graph.threads.net/v1.0/me/threads_publish",
            data={"creation_id": container["id"], "access_token": token},
            timeout=30,
        )
        return jsonify(resp2.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- THREADS: Status ---
@threads_bp.route("/threads/status")
def threads_status():
    """Get Threads connection status."""
    return jsonify({
        "configured": bool(THREADS_APP_ID),
        "connected": bool(os.getenv("THREADS_ACCESS_TOKEN", "")),
        "app_id_preview": THREADS_APP_ID[:10] + "..." if THREADS_APP_ID else None,
    })


if __name__ == "__main__":
    print("=== THREADS INTEGRATION ===")
    print(f"App ID configured: {bool(THREADS_APP_ID)}")
    print(f"Connected: {bool(os.getenv('THREADS_ACCESS_TOKEN', ''))}")
    print("\n=== ENDPOINTS ===")
    print("  GET  /threads/login        - OAuth login")
    print("  GET  /threads/callback     - OAuth callback")
    print("  GET  /threads/user         - User profile")
    print("  GET  /threads/posts        - User's posts")
    print("  POST /threads/post/text    - Create text post")
    print("  POST /threads/post/image   - Create image post")
    print("  GET  /threads/status       - Connection status")