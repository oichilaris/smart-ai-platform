import os
import json
import logging
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [CRON]: %(message)s")
logger = logging.getLogger("CRON")

cron_bp = Blueprint("cron", __name__)

# --- In-memory job store ---
JOBS = {}

@cron_bp.route("/cron/status")
def cron_status():
    return jsonify({"status": "running", "jobs": len(JOBS), "job_list": list(JOBS.keys())})

@cron_bp.route("/cron/add", methods=["POST"])
def cron_add():
    data = request.json or {}
    job_name = data.get("name", "")
    interval = data.get("interval", "daily")  # daily, hourly, every_5min, etc.
    url = data.get("url", "")
    method = data.get("method", "GET")
    payload = data.get("payload", {})
    if not job_name or not url:
        return jsonify({"error": "name and url required"}), 400
    JOBS[job_name] = {
        "interval": interval,
        "url": url,
        "method": method,
        "payload": payload,
        "created": datetime.now().isoformat(),
        "last_run": None,
        "run_count": 0,
    }
    logger.info(f"Job added: {job_name} ({interval}) -> {url}")
    return jsonify({"status": "added", "job": job_name})

@cron_bp.route("/cron/remove", methods=["POST"])
def cron_remove():
    data = request.json or {}
    job_name = data.get("name", "")
    if job_name in JOBS:
        del JOBS[job_name]
        return jsonify({"status": "removed", "job": job_name})
    return jsonify({"error": "job not found"}), 404

@cron_bp.route("/cron/list")
def cron_list():
    return jsonify({"jobs": JOBS})

@cron_bp.route("/cron/run", methods=["POST"])
def cron_run_now():
    data = request.json or {}
    job_name = data.get("name", "")
    if job_name not in JOBS:
        return jsonify({"error": "job not found"}), 404
    job = JOBS[job_name]
    try:
        if job["method"].upper() == "POST":
            resp = requests.post(job["url"], json=job["payload"], timeout=30)
        else:
            resp = requests.get(job["url"], timeout=30)
        job["last_run"] = datetime.now().isoformat()
        job["run_count"] += 1
        return jsonify({"status": "executed", "job": job_name, "response_code": resp.status_code, "response": resp.text[:500]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Scheduled tasks (pre-configured) ---
def job_gm_report_telegram():
    """Send GM financial report to Telegram daily."""
    try:
        requests.get("https://auldihasibuan.pythonanywhere.com/api/gm-report/telegram", timeout=30)
        logger.info("GM report sent to Telegram")
    except Exception as e:
        logger.error(f"GM report failed: {e}")

def job_marketplace_check():
    """Check marketplace inventory and alerts."""
    try:
        requests.get("https://auldihasibuan.pythonanywhere.com/marketplace/api", timeout=30)
        logger.info("Marketplace checked")
    except Exception as e:
        logger.error(f"Marketplace check failed: {e}")

# Pre-register default jobs
JOBS["gm_report_daily"] = {
    "interval": "daily_08:00",
    "url": "https://auldihasibuan.pythonanywhere.com/api/gm-report/telegram",
    "method": "GET",
    "payload": {},
    "created": datetime.now().isoformat(),
    "last_run": None,
    "run_count": 0,
    "description": "Kirim GM financial report ke Telegram setiap pagi",
}

JOBS["marketplace_check"] = {
    "interval": "every_6h",
    "url": "https://auldihasibuan.pythonanywhere.com/marketplace/api",
    "method": "GET",
    "payload": {},
    "created": datetime.now().isoformat(),
    "last_run": None,
    "run_count": 0,
    "description": "Cek inventory marketplace setiap 6 jam",
}

if __name__ == "__main__":
    print("=== CRON JOB SCHEDULER ===")
    print(f"Jobs: {len(JOBS)}")
    for name, job in JOBS.items():
        print(f"  - {name}: {job['interval']} -> {job['url']}")
    print("\n=== ENDPOINTS ===")
    print("  GET  /cron/status    - Scheduler status")
    print("  POST /cron/add       - Add new job")
    print("  POST /cron/remove    - Remove job")
    print("  GET  /cron/list      - List all jobs")
    print("  POST /cron/run       - Run job now")