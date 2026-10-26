import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [GUMROAD]: %(message)s")
logger = logging.getLogger("GUMROAD")

# ============================================================
# GUMROAD / LEMON SQUEEZY INTEGRATION
# ============================================================

GUMROAD_ACCESS_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN", "Yj625fV9OEF4EFtncJlezzwN3nIhhaRsljReVmrxUdA")
LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NGQ1OWNlZi1kYmI4LTRlYTUtYjE3OC1kMjU0MGZjZDY5MTkiLCJqdGkiOiI3ODEwZmU4M2UxY2ZiNDI0ZWRlYzE4Y2UwM2ZkZjBiZTlkNGE2Y2ZjYTM0NDJmZTZlOGUwZjYzNDU4NzlhYzMwMmJmM2VjOTY5YzIyNWQ4NCIsImlhdCI6MTc5Mjk1MTE3MS42NTkwODMsIm5iZiI6MTc5Mjk1MTE3MS42NTkwODUsImV4cCI6MTgwODY5NzYwMC4wNDUwNjIsInN1YiI6IjgyNDMxMDIiLCJzY29wZXMiOltdfQ.Fy_ly7Mm2vUQCDFDKUNTfNLCdEiKjMeKOzT3qE4uda9UMGB2Qex_LW8T5INVTRhoNB9e6PM8mCFAFOFsYun-oM8xvsKcfbGpAvLQqq62jkxCOy2wmXh7CAg-9TsOK8Kp0e3LeDTpGH4qBArNg7zIihUQBy6pt2S6cqcPBcLKxuQylcT87A0uIJAC5280ZFkrwQFNiil74GpDIgr-jtkcxVBi1DNVjGQt2dTzZ6g0E0EcY1N1fRJGWjO4UQ6ioKpSeA_2SZaUsSekpyDL5YyGs5xn4QpRRiqQhm2VKBhzZ-5QDJv0_UG0_NMlR7WKN3Eccc1kOHnGhCTCVyC8Mu6SEbPxaOZFCj2e8mkDcvFvldoGincumKKPv0fbyxor1QvTsLak3imMEQLW7lvNCwIhLNaslc1xDdb5HAf6VMn72gankaEtNa4JRToONikAslh9orWiB7jUGo67JSyMZKXxJ4y6L3C7FXQE1aMll11EymirvpvBzgVkw-KLn_fUii5Te4UUMouQmOBki0WBq21eR6wOHvvhrPnanvZ4Fj8lZVLaom2knl-G9A7caoXaSNuOUACHNNFGre48pM7cQAwmxfbv8otdSewvBMhfdel5Umx_l83jCcXmDa3Fo7afs_oV-eUry8SpoOFh9Uo6PvvasniM911ilyxpKlp98KWLmwk")

gumroad_bp = Blueprint("gumroad", __name__)

# --- GUMROAD: List Products ---
@gumroad_bp.route("/gumroad/products")
def list_products():
    """List all products on Gumroad."""
    if not GUMROAD_ACCESS_TOKEN:
        return jsonify({"error": "GUMROAD_ACCESS_TOKEN not set"}), 400
    try:
        resp = requests.get(
            "https://api.gumroad.com/v2/products",
            params={"access_token": GUMROAD_ACCESS_TOKEN},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- GUMROAD: Create Product ---
@gumroad_bp.route("/gumroad/create-product", methods=["POST"])
def create_product():
    """Create a new product on Gumroad."""
    if not GUMROAD_ACCESS_TOKEN:
        return jsonify({"error": "GUMROAD_ACCESS_TOKEN not set"}), 400
    data = request.json or {}
    try:
        resp = requests.post(
            "https://api.gumroad.com/v2/products",
            data={
                "access_token": GUMROAD_ACCESS_TOKEN,
                "name": data.get("name", "Digital Product"),
                "description": data.get("description", ""),
                "price": data.get("price", 1000),  # in cents
                "currency": data.get("currency", "usd"),
            },
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- GUMROAD: Sales Summary ---
@gumroad_bp.route("/gumroad/sales")
def sales_summary():
    """Get sales summary from Gumroad."""
    if not GUMROAD_ACCESS_TOKEN:
        return jsonify({"error": "GUMROAD_ACCESS_TOKEN not set"}), 400
    try:
        resp = requests.get(
            "https://api.gumroad.com/v2/sales",
            params={"access_token": GUMROAD_ACCESS_TOKEN},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- LEMON SQUEEZY: List Products ---
@gumroad_bp.route("/lemonsqueezy/products")
def ls_products():
    """List products on Lemon Squeezy."""
    if not LEMONSQUEEZY_API_KEY:
        return jsonify({"error": "LEMONSQUEEZY_API_KEY not set"}), 400
    try:
        resp = requests.get(
            "https://api.lemonsqueezy.com/v1/products",
            headers={"Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- LEMON SQUEEZY: List Orders ---
@gumroad_bp.route("/lemonsqueezy/orders")
def ls_orders():
    """List orders on Lemon Squeezy."""
    if not LEMONSQUEEZY_API_KEY:
        return jsonify({"error": "LEMONSQUEEZY_API_KEY not set"}), 400
    try:
        resp = requests.get(
            "https://api.lemonsqueezy.com/v1/orders",
            headers={"Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}"},
            timeout=30,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- WEBHOOK: Gumroad Sale Notification ---
@gumroad_bp.route("/gumroad/webhook", methods=["POST"])
def gumroad_webhook():
    """Handle Gumroad sale webhook."""
    data = request.form.to_dict() if request.form else (request.json or {})
    product_name = data.get("product_name", "Unknown Product")
    price = data.get("price", "0")
    buyer_email = data.get("email", "N/A")
    logger.info(f"Gumroad sale: {product_name} - ${price} - Buyer: {buyer_email}")
    
    # Send notification to Telegram
    try:
        import requests as req
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "8978211142:AAHcf8rAHAAZXJOtg6Kqoe_O4Rg8Z37PVeg")
        tg_chat = os.getenv("TELEGRAM_CHAT_ID", "7335538063")
        if tg_token:
            msg = f"💰 PENJUALAN BARU!\n\nProduk: {product_name}\nHarga: ${price}\nPembeli: {buyer_email}\nPlatform: Gumroad\n\nCatatan: Dicatat oleh GM Financial"
            req.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                     data={"chat_id": tg_chat, "text": msg}, timeout=10)
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
    
    return jsonify({"status": "received"}), 200


# --- WEBHOOK: Lemon Squeezy Sale Notification ---
@gumroad_bp.route("/lemonsqueezy/webhook", methods=["POST"])
def ls_webhook():
    """Handle Lemon Squeezy sale webhook."""
    data = request.json or {}
    event = data.get("meta", {}).get("event_name", "")
    logger.info(f"Lemon Squeezy event: {event}")
    
    # Send notification to Telegram on order_created
    if event == "order_created":
        try:
            import requests as req
            tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "8978211142:AAHcf8rAHAAZXJOtg6Kqoe_O4Rg8Z37PVeg")
            tg_chat = os.getenv("TELEGRAM_CHAT_ID", "7335538063")
            if tg_token:
                attrs = data.get("data", {}).get("attributes", {})
                product_name = attrs.get("product_name", "Unknown")
                total = attrs.get("total", 0) / 100
                buyer_email = attrs.get("user_email", "N/A")
                msg = f"💰 PENJUALAN BARU!\n\nProduk: {product_name}\nHarga: ${total}\nPembeli: {buyer_email}\nPlatform: Lemon Squeezy\n\nCatatan: Dicatat oleh GM Financial"
                req.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                         data={"chat_id": tg_chat, "text": msg}, timeout=10)
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
    
    return jsonify({"status": "received"}), 200


# --- STATUS ---
@gumroad_bp.route("/gumroad/status")
def status():
    """Get integration status."""
    return jsonify({
        "gumroad": {
            "configured": bool(GUMROAD_ACCESS_TOKEN),
            "token_preview": GUMROAD_ACCESS_TOKEN[:10] + "..." if GUMROAD_ACCESS_TOKEN else None,
        },
        "lemonsqueezy": {
            "configured": bool(LEMONSQUEEZY_API_KEY),
            "key_preview": LEMONSQUEEZY_API_KEY[:10] + "..." if LEMONSQUEEZY_API_KEY else None,
        },
    })


if __name__ == "__main__":
    print("=== GUMROAD / LEMON SQUEEZY STATUS ===")
    print(f"Gumroad configured: {bool(GUMROAD_ACCESS_TOKEN)}")
    print(f"Lemon Squeezy configured: {bool(LEMONSQUEEZY_API_KEY)}")
    print("\n=== ENVIRONMENT VARIABLES NEEDED ===")
    print("  GUMROAD_ACCESS_TOKEN")
    print("  LEMONSQUEEZY_API_KEY")
    print("\n=== ENDPOINTS ===")
    print("  GET  /gumroad/products          - List Gumroad products")
    print("  POST /gumroad/create-product    - Create Gumroad product")
    print("  GET  /gumroad/sales             - Sales summary")
    print("  GET  /lemonsqueezy/products     - List Lemon Squeezy products")
    print("  GET  /lemonsqueezy/orders       - List orders")
    print("  POST /gumroad/webhook           - Gumroad sale webhook")
    print("  POST /lemonsqueezy/webhook      - Lemon Squeezy sale webhook")
    print("  GET  /gumroad/status            - Integration status")