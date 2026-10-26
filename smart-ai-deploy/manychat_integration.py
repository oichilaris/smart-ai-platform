import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MANYCHAT]: %(message)s")
logger = logging.getLogger("MANYCHAT")

MANYCHAT_API_KEY = os.getenv("MANYCHAT_API_KEY", "")
MANYCHAT_BASE_URL = "https://api.manychat.com/fb"

manychat_bp = Blueprint("manychat", __name__)

@manychat_bp.route("/manychat/status")
def manychat_status():
    return jsonify({"configured": bool(MANYCHAT_API_KEY), "connected": bool(MANYCHAT_API_KEY)})

@manychat_bp.route("/manychat/send", methods=["POST"])
def manychat_send():
    if not MANYCHAT_API_KEY:
        return jsonify({"error": "MANYCHAT_API_KEY not set. Get from https://manychat.com"}), 400
    data = request.json or {}
    subscriber_id = data.get("subscriber_id", "")
    message = data.get("message", "")
    if not subscriber_id or not message:
        return jsonify({"error": "subscriber_id and message required"}), 400
    try:
        resp = requests.post(
            f"{MANYCHAT_BASE_URL}/sending/sendContent",
            headers={"Authorization": f"Bearer {MANYCHAT_API_KEY}", "Content-Type": "application/json"},
            json={
                "subscriber_id": subscriber_id,
                "data": {
                    "version": "v2",
                    "content": {
                        "messages": [{"type": "text", "text": message}]
                    }
                }
            },
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@manychat_bp.route("/manychat/flow", methods=["POST"])
def manychat_flow():
    if not MANYCHAT_API_KEY:
        return jsonify({"error": "MANYCHAT_API_KEY not set"}), 400
    data = request.json or {}
    subscriber_id = data.get("subscriber_id", "")
    flow_ns = data.get("flow_ns", "")
    if not subscriber_id or not flow_ns:
        return jsonify({"error": "subscriber_id and flow_ns required"}), 400
    try:
        resp = requests.post(
            f"{MANYCHAT_BASE_URL}/sending/sendFlow",
            headers={"Authorization": f"Bearer {MANYCHAT_API_KEY}", "Content-Type": "application/json"},
            json={"subscriber_id": subscriber_id, "flow_ns": flow_ns},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@manychat_bp.route("/manychat/subscriber/<subscriber_id>")
def manychat_subscriber(subscriber_id):
    if not MANYCHAT_API_KEY:
        return jsonify({"error": "MANYCHAT_API_KEY not set"}), 400
    try:
        resp = requests.get(
            f"{MANYCHAT_BASE_URL}/subscriber/getInfo?subscriber_id={subscriber_id}",
            headers={"Authorization": f"Bearer {MANYCHAT_API_KEY}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@manychat_bp.route("/manychat/tag", methods=["POST"])
def manychat_tag():
    if not MANYCHAT_API_KEY:
        return jsonify({"error": "MANYCHAT_API_KEY not set"}), 400
    data = request.json or {}
    subscriber_id = data.get("subscriber_id", "")
    tag_name = data.get("tag_name", "")
    if not subscriber_id or not tag_name:
        return jsonify({"error": "subscriber_id and tag_name required"}), 400
    try:
        resp = requests.post(
            f"{MANYCHAT_BASE_URL}/subscriber/addTagByName",
            headers={"Authorization": f"Bearer {MANYCHAT_API_KEY}", "Content-Type": "application/json"},
            json={"subscriber_id": subscriber_id, "tag_name": tag_name},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("ManyChat Auto-DM Integration")
    print(f"Configured: {bool(MANYCHAT_API_KEY)}")
    print("Endpoints: /manychat/status, /manychat/send, /manychat/flow, /manychat/subscriber/<id>, /manychat/tag")