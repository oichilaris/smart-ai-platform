import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [LUMA]: %(message)s")
logger = logging.getLogger("LUMA")

LUMA_API_KEY = os.getenv("LUMA_API_KEY", "")
LUMA_BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

luma_bp = Blueprint("luma", __name__)

@luma_bp.route("/luma/status")
def luma_status():
    return jsonify({"configured": bool(LUMA_API_KEY), "connected": bool(LUMA_API_KEY)})

@luma_bp.route("/luma/generate", methods=["POST"])
def luma_generate():
    if not LUMA_API_KEY:
        return jsonify({"error": "LUMA_API_KEY not set. Get from https://lumalabs.ai"}), 400
    data = request.json or {}
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    try:
        payload = {"prompt": prompt}
        if data.get("image_url"):
            payload["keyframes"] = {"frame0": {"type": "image", "url": data["image_url"]}}
        if data.get("aspect_ratio"):
            payload["aspect_ratio"] = data["aspect_ratio"]
        if data.get("loop"):
            payload["loop"] = data["loop"]
        resp = requests.post(
            f"{LUMA_BASE_URL}/generations",
            headers={"Authorization": f"Bearer {LUMA_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@luma_bp.route("/luma/status/<generation_id>")
def luma_gen_status(generation_id):
    if not LUMA_API_KEY:
        return jsonify({"error": "LUMA_API_KEY not set"}), 400
    try:
        resp = requests.get(
            f"{LUMA_BASE_URL}/generations/{generation_id}",
            headers={"Authorization": f"Bearer {LUMA_API_KEY}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Luma Dream Machine Integration")
    print(f"Configured: {bool(LUMA_API_KEY)}")
    print("Endpoints: /luma/status, /luma/generate, /luma/status/<id>")