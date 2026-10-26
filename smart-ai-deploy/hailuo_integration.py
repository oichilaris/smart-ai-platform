import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [HAILUO]: %(message)s")
logger = logging.getLogger("HAILUO")

HAILUO_API_KEY = os.getenv("HAILUO_API_KEY", "")
HAILUO_BASE_URL = "https://api.minimaxi.chat/v1"

hailuo_bp = Blueprint("hailuo", __name__)

@hailuo_bp.route("/hailuo/status")
def hailuo_status():
    return jsonify({"configured": bool(HAILUO_API_KEY), "connected": bool(HAILUO_API_KEY)})

@hailuo_bp.route("/hailuo/generate", methods=["POST"])
def hailuo_generate():
    if not HAILUO_API_KEY:
        return jsonify({"error": "HAILUO_API_KEY not set. Get from https://minimaxi.com"}), 400
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    try:
        payload = {
            "model": "video-01",
            "prompt": prompt,
        }
        if data.get("image_url"):
            payload["first_frame_image"] = data["image_url"]
        if data.get("duration"):
            payload["duration"] = data["duration"]
        if data.get("resolution"):
            payload["resolution"] = data["resolution"]
        resp = requests.post(
            f"{HAILUO_BASE_URL}/video_generation",
            headers={"Authorization": f"Bearer {HAILUO_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@hailuo_bp.route("/hailuo/status/<task_id>")
def hailuo_gen_status(task_id):
    if not HAILUO_API_KEY:
        return jsonify({"error": "HAILUO_API_KEY not set"}), 400
    try:
        resp = requests.get(
            f"{HAILUO_BASE_URL}/query/video_generation?task_id={task_id}",
            headers={"Authorization": f"Bearer {HAILUO_API_KEY}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Hailuo AI (MiniMax) Integration")
    print(f"Configured: {bool(HAILUO_API_KEY)}")
    print("Endpoints: /hailuo/status, /hailuo/generate, /hailuo/status/<id>")