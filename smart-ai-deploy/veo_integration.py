import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [VEO]: %(message)s")
logger = logging.getLogger("VEO")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
VEO_MODEL = "veo-3.0-generate-preview"

veo_bp = Blueprint("veo", __name__)

@veo_bp.route("/veo/status")
def veo_status():
    return jsonify({"configured": bool(GOOGLE_API_KEY), "connected": bool(GOOGLE_API_KEY), "model": VEO_MODEL})

@veo_bp.route("/veo/generate", methods=["POST"])
def veo_generate():
    if not GOOGLE_API_KEY:
        return jsonify({"error": "GOOGLE_API_KEY not set. Get from https://aistudio.google.com"}), 400
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    try:
        payload = {
            "prompt": prompt,
            "config": {
                "aspectRatio": data.get("aspect_ratio", "16:9"),
                "numberOfVideos": 1,
            }
        }
        if data.get("image_url"):
            payload["image"] = {"uri": data["image_url"]}
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{VEO_MODEL}:predictLongRunning",
            headers={"x-goog-api-key": GOOGLE_API_KEY, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@veo_bp.route("/veo/status/<operation_id>")
def veo_gen_status(operation_id):
    if not GOOGLE_API_KEY:
        return jsonify({"error": "GOOGLE_API_KEY not set"}), 400
    try:
        resp = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/{operation_id}",
            headers={"x-goog-api-key": GOOGLE_API_KEY},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Google Veo Integration")
    print(f"Configured: {bool(GOOGLE_API_KEY)}")
    print("Endpoints: /veo/status, /veo/generate, /veo/status/<id>")