import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify, redirect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [META]: %(message)s")
logger = logging.getLogger("META")

META_APP_ID = os.getenv("META_APP_ID", "4323246241300437")
META_APP_SECRET = os.getenv("META_APP_SECRET", "10090e44792ac7915f8b9d363d083afe")
META_REDIRECT_URI = "https://auldihasibuan.pythonanywhere.com/meta/callback"

meta_bp = Blueprint("meta", __name__)

# --- META: OAuth Login ---
@meta_bp.route("/meta/login")
def meta_login():
    """Redirect to Meta OAuth authorization."""
    if not META_APP_ID:
        return jsonify({"error": "META_APP_ID not set"}), 400
    auth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&scope=pages_manage_posts,pages_read_engagement,instagram_basic,instagram_content_publish"
        f"&state=meta_auth"
    )
    return redirect(auth_url)


# --- META: OAuth Callback ---
@meta_bp.route("/meta/callback")
def meta_callback():
    """Handle Meta OAuth callback."""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No authorization code"}), 400
    try:
        resp = requests.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "redirect_uri": META_REDIRECT_URI,
                "code": code,
            },
            timeout=30,
        )
        data = resp.json()
        if "access_token" in data:
            os.environ["META_ACCESS_TOKEN"] = data["access_token"]
            return jsonify({"status": "connected", "token_preview": data["access_token"][:10] + "..."})
        return jsonify({"error": "Token exchange failed", "details": data}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- META: Get Pages ---
@meta_bp.route("/meta/pages")
def meta_pages():
    """Get Facebook pages managed by user."""
    token = os.getenv("META_ACCESS_TOKEN", "EAA9bZBDR9P9UBS4TBpGcE2x2nxgFYT1IuQVIK3hNZBW8ao7o5s3uc4fsPYR8VJ34QGZCNadGaQiB3t22ywNHGSonZAjkWOpGfd0xB32z0tFv8XnXWHdem858a2teFZBzn2ZCsfhiQiTa54U1nT80mNUSZAOGB8dRNDKpmiL8Px1Dlp4AMwzSVq36SEuNuRDGwUwDvXZCKKVOeOYFRszYKkZC2qdZCVKrwjiA4pN7eLGF6P90gSRzWhYUZC19uHr1dp4IPz0UitUbZCnwWKO3WeVFAgZDZD")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    try:
        resp = requests.get(
            "https://graph.facebook.com/v18.0/me/accounts",
            params={"access_token": token},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- META: Post to Facebook Page ---
@meta_bp.route("/meta/post/facebook", methods=["POST"])
def meta_post_fb():
    """Post to Facebook page."""
    token = os.getenv("META_ACCESS_TOKEN", "EAA9bZBDR9P9UBS4TBpGcE2x2nxgFYT1IuQVIK3hNZBW8ao7o5s3uc4fsPYR8VJ34QGZCNadGaQiB3t22ywNHGSonZAjkWOpGfd0xB32z0tFv8XnXWHdem858a2teFZBzn2ZCsfhiQiTa54U1nT80mNUSZAOGB8dRNDKpmiL8Px1Dlp4AMwzSVq36SEuNuRDGwUwDvXZCKKVOeOYFRszYKkZC2qdZCVKrwjiA4pN7eLGF6P90gSRzWhYUZC19uHr1dp4IPz0UitUbZCnwWKO3WeVFAgZDZD")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    data = request.json or {}
    page_id = data.get("page_id", "")
    message = data.get("message", "")
    if not page_id or not message:
        return jsonify({"error": "page_id and message required"}), 400
    try:
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{page_id}/feed",
            data={"message": message, "access_token": token},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- META: Post to Instagram ---
@meta_bp.route("/meta/post/instagram", methods=["POST"])
def meta_post_ig():
    """Post to Instagram (requires media)."""
    token = os.getenv("META_ACCESS_TOKEN", "EAA9bZBDR9P9UBS4TBpGcE2x2nxgFYT1IuQVIK3hNZBW8ao7o5s3uc4fsPYR8VJ34QGZCNadGaQiB3t22ywNHGSonZAjkWOpGfd0xB32z0tFv8XnXWHdem858a2teFZBzn2ZCsfhiQiTa54U1nT80mNUSZAOGB8dRNDKpmiL8Px1Dlp4AMwzSVq36SEuNuRDGwUwDvXZCKKVOeOYFRszYKkZC2qdZCVKrwjiA4pN7eLGF6P90gSRzWhYUZC19uHr1dp4IPz0UitUbZCnwWKO3WeVFAgZDZD")
    if not token:
        return jsonify({"error": "Not connected"}), 400
    data = request.json or {}
    ig_user_id = data.get("ig_user_id", "")
    image_url = data.get("image_url", "")
    caption = data.get("caption", "")
    if not ig_user_id or not image_url:
        return jsonify({"error": "ig_user_id and image_url required"}), 400
    try:
        # Step 1: Create media container
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_user_id}/media",
            data={"image_url": image_url, "caption": caption, "access_token": token},
            timeout=30,
        )
        container = resp.json()
        if "id" not in container:
            return jsonify({"error": "Failed to create media container", "details": container}), 400
        
        # Step 2: Publish
        resp2 = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish",
            data={"creation_id": container["id"], "access_token": token},
            timeout=30,
        )
        return jsonify(resp2.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- META: Status ---
@meta_bp.route("/meta/status")
def meta_status():
    """Get Meta connection status."""
    return jsonify({
        "configured": bool(META_APP_ID),
        "connected": bool(os.getenv("META_ACCESS_TOKEN", "EAA9bZBDR9P9UBS4TBpGcE2x2nxgFYT1IuQVIK3hNZBW8ao7o5s3uc4fsPYR8VJ34QGZCNadGaQiB3t22ywNHGSonZAjkWOpGfd0xB32z0tFv8XnXWHdem858a2teFZBzn2ZCsfhiQiTa54U1nT80mNUSZAOGB8dRNDKpmiL8Px1Dlp4AMwzSVq36SEuNuRDGwUwDvXZCKKVOeOYFRszYKkZC2qdZCVKrwjiA4pN7eLGF6P90gSRzWhYUZC19uHr1dp4IPz0UitUbZCnwWKO3WeVFAgZDZD")),
        "app_id_preview": META_APP_ID[:10] + "..." if META_APP_ID else None,
    })


if __name__ == "__main__":
    print("=== META (FACEBOOK/INSTAGRAM) INTEGRATION ===")
    print(f"App ID configured: {bool(META_APP_ID)}")
    print(f"Connected: {bool(os.getenv('META_ACCESS_TOKEN', ''))}")
    print("\n=== ENDPOINTS ===")
    print("  GET  /meta/login          - OAuth login")
    print("  GET  /meta/callback       - OAuth callback")
    print("  GET  /meta/pages          - List Facebook pages")
    print("  POST /meta/post/facebook  - Post to Facebook")
    print("  POST /meta/post/instagram - Post to Instagram")
    print("  GET  /meta/status         - Connection status")