import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [RUNWAY]: %(message)s")
logger = logging.getLogger("RUNWAY")

RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")
RUNWAY_BASE_URL = "https://api.dev.runwayml.com/v1"

runway_bp = Blueprint("runway", __name__)

@runway_bp.route("/runway/status")
def runway_status():
    return jsonify({"configured": bool(RUNWAY_API_KEY), "connected": bool(RUNWAY_API_KEY)})

@runway_bp.route("/runway/generate", methods=["POST"])
def runway_generate():
    if not RUNWAY_API_KEY:
        return jsonify({"error": "RUNWAY_API_KEY not set. Get from https://runwayml.com"}), 400
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    try:
        payload = {
            "promptText": prompt,
            "model": data.get("model", "gen3a_turbo"),
            "ratio": data.get("aspect_ratio", "1280:720"),
            "duration": data.get("duration", 5),
        }
        if data.get("image_url"):
            payload["promptImage"] = data["image_url"]
        resp = requests.post(
            f"{RUNWAY_BASE_URL}/image_to_video",
            headers={"Authorization": f"Bearer {RUNWAY_API_KEY}", "Content-Type": "application/json", "X-Runway-Version": "2024-11-06"},
            json=payload,
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@runway_bp.route("/runway/status/<task_id>")
def runway_gen_status(task_id):
    if not RUNWAY_API_KEY:
        return jsonify({"error": "RUNWAY_API_KEY not set"}), 400
    try:
        resp = requests.get(
            f"{RUNWAY_BASE_URL}/tasks/{task_id}",
            headers={"Authorization": f"Bearer {RUNWAY_API_KEY}", "X-Runway-Version": "2024-11-06"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Runway Integration")
    print(f"Configured: {bool(RUNWAY_API_KEY)}")
    print("Endpoints: /runway/status, /runway/generate, /runway/status/<id>")