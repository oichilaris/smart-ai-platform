import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify, redirect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [TIKTOK]: %(message)s")
logger = logging.getLogger("TIKTOK")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "awpvqa0y9p3husgb")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "Qo398VRQwBXgZUWqww4t0i3NY4fCW2Sd")
TIKTOK_REDIRECT_URI = "https://auldihasibuan.pythonanywhere.com/tiktok/callback"

tiktok_bp = Blueprint("tiktok", __name__)

# --- TIKTOK: OAuth Login ---
@tiktok_bp.route("/tiktok/login")
def tiktok_login():
    """Redirect to TikTok OAuth authorization."""
    if not TIKTOK_CLIENT_KEY:
        return jsonify({"error": "TIKTOK_CLIENT_KEY not set"}), 400
    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&scope=user.info.basic,video.publish,video.upload,video.list"
        f"&response_type=code"
        f"&redirect_uri={TIKTOK_REDIRECT_URI}"
        f"&state=tiktok_auth"
    )
    return redirect(auth_url)


# --- TIKTOK: OAuth Callback ---
@tiktok_bp.route("/tiktok/callback")
def tiktok_callback():
    """Handle TikTok OAuth callback."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": TIKTOK_CLIENT_KEY,
                "client_secret": TIKTOK_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": TIKTOK_REDIRECT_URI,
            },
            timeout=30,
        )
        data = resp.json()
        if "access_token" in data:
            # Save token (in production, store in DB)
            os.environ["TIKTOK_ACCESS_TOKEN"] = data["access_token"]
            return jsonify({"status": "connected", "token_preview": data["access_token"][:10] + "..."})
        return jsonify({"error": "Token exchange failed", "details": data}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- TIKTOK: User's Recent Videos ---
@tiktok_bp.route("/tiktok/videos")
def tiktok_videos():
    """Get TikTok user's recent videos."""
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/video/list/",
            params={"fields": "id,title,video_description,duration,cover_image_url,share_url,like_count,comment_count,share_count,view_count,create_time"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"max_count": 20},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- TIKTOK: User Info ---
@tiktok_bp.route("/tiktok/user")
def tiktok_user():
    """Get TikTok user info."""
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    try:
        resp = requests.get(
            "https://open.tiktokapis.com/v2/user/info/",
            params={"fields": "open_id,union_id,avatar_url,display_name"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- TIKTOK: Video Upload Init ---
@tiktok_bp.route("/tiktok/upload/init", methods=["POST"])
def tiktok_upload_init():
    """Initialize video upload to TikTok."""
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    data = request.json or {}
    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "post_info": {
                    "title": data.get("title", "New Video"),
                    "privacy_level": data.get("privacy", "PUBLIC_TO_EVERYONE"),
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": data.get("video_size", 0),
                    "chunk_size": data.get("chunk_size", 10000000),
                    "total_chunk_count": data.get("total_chunks", 1),
                },
            },
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- TIKTOK: Status ---
@tiktok_bp.route("/tiktok/status")
def tiktok_status():
    """Get TikTok connection status."""
    return jsonify({
        "configured": bool(TIKTOK_CLIENT_KEY),
        "connected": bool(os.getenv("TIKTOK_ACCESS_TOKEN", "")),
        "client_key_preview": TIKTOK_CLIENT_KEY[:10] + "..." if TIKTOK_CLIENT_KEY else None,
    })


if __name__ == "__main__":
    print("=== TIKTOK INTEGRATION ===")
    print(f"Client Key configured: {bool(TIKTOK_CLIENT_KEY)}")
    print(f"Connected: {bool(os.getenv('TIKTOK_ACCESS_TOKEN', ''))}")
    print("\n=== ENDPOINTS ===")
    print("  GET  /tiktok/login       - OAuth login")
    print("  GET  /tiktok/callback    - OAuth callback")
    print("  GET  /tiktok/user        - User info")
    print("  POST /tiktok/upload/init - Init video upload")
    print("  GET  /tiktok/status      - Connection status")