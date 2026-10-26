import os
import json
import logging
import stripe
from flask import Blueprint, request, jsonify, redirect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [STRIPE]: %(message)s")
logger = logging.getLogger("STRIPE")

# ============================================================
# STRIPE CONFIGURATION
# ============================================================

STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_51UQ4de9eKNQUQpsYNAT0XkGPlKzlHFrD2xrTanTLqLdAIQ62BGgStLofZkUPRRFBWwW1NV6QGksb6hVUuUd049Z600m7Sak35P")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_SECRET_KEY

# ============================================================
# STRIPE INTEGRATION MODULE
# ============================================================

stripe_bp = Blueprint("stripe", __name__)

# --- PAYMENTS: One-time Checkout Session ---
@stripe_bp.route("/stripe/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create a Stripe Checkout Session for one-time payment."""
    data = request.json or {}
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": data.get("currency", "usd"),
                    "product_data": {
                        "name": data.get("product_name", "Product"),
                        "description": data.get("description", ""),
                    },
                    "unit_amount": data.get("amount", 1000),  # in cents
                },
                "quantity": data.get("quantity", 1),
            }],
            mode="payment",
            success_url=data.get("success_url", "https://auldihasibuan.pythonanywhere.com/stripe/success?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=data.get("cancel_url", "https://auldihasibuan.pythonanywhere.com/stripe/cancel"),
            managed_payments={"enabled": True},  # Tax compliance
        )
        return jsonify({"session_id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Checkout session error: {e}")
        return jsonify({"error": str(e)}), 400


# --- BILLING: Create Subscription ---
@stripe_bp.route("/stripe/create-subscription", methods=["POST"])
def create_subscription():
    """Create a subscription for recurring billing."""
    data = request.json or {}
    try:
        # Create or retrieve customer
        customer = stripe.Customer.create(
            email=data.get("email"),
            name=data.get("name"),
            metadata={"division": data.get("division", "general")},
        )
        
        # Create price if not exists
        price = stripe.Price.create(
            unit_amount=data.get("amount", 1000),
            currency=data.get("currency", "usd"),
            recurring={"interval": data.get("interval", "month")},
            product_data={"name": data.get("product_name", "Subscription")},
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price.id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
        
        return jsonify({
            "subscription_id": subscription.id,
            "customer_id": customer.id,
            "status": subscription.status,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None,
        })
    except stripe.error.StripeError as e:
        logger.error(f"Subscription error: {e}")
        return jsonify({"error": str(e)}), 400


# --- INVOICING: Create Invoice ---
@stripe_bp.route("/stripe/create-invoice", methods=["POST"])
def create_invoice():
    """Create and send an invoice."""
    data = request.json or {}
    try:
        # Create customer
        customer = stripe.Customer.create(
            email=data.get("email"),
            name=data.get("name"),
            metadata={"division": data.get("division", "general")},
        )
        
        # Create invoice item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=data.get("amount", 1000),
            currency=data.get("currency", "usd"),
            description=data.get("description", "Invoice item"),
        )
        
        # Create invoice
        invoice = stripe.Invoice.create(
            customer=customer.id,
            auto_advance=True,
            collection_method="send_invoice",
            days_until_due=data.get("days_until_due", 30),
            metadata={"division": data.get("division", "general")},
        )
        
        # Finalize and send
        invoice = stripe.Invoice.finalize_invoice(invoice.id)
        stripe.Invoice.send_invoice(invoice.id)
        
        return jsonify({
            "invoice_id": invoice.id,
            "status": invoice.status,
            "hosted_invoice_url": invoice.hosted_invoice_url,
            "invoice_pdf": invoice.invoice_pdf,
        })
    except stripe.error.StripeError as e:
        logger.error(f"Invoice error: {e}")
        return jsonify({"error": str(e)}), 400


# --- CONNECT: Create Connected Account ---
@stripe_bp.route("/stripe/create-connected-account", methods=["POST"])
def create_connected_account():
    """Create a connected account for marketplace sellers."""
    data = request.json or {}
    try:
        account = stripe.Account.create(
            type=data.get("type", "express"),
            country=data.get("country", "SG"),
            email=data.get("email"),
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            metadata={"division": data.get("division", "general")},
        )
        
        # Create account link for onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url=data.get("refresh_url", "https://auldihasibuan.pythonanywhere.com/stripe/connect/refresh"),
            return_url=data.get("return_url", "https://auldihasibuan.pythonanywhere.com/stripe/connect/return"),
            type="account_onboarding",
        )
        
        return jsonify({
            "account_id": account.id,
            "onboarding_url": account_link.url,
        })
    except stripe.error.StripeError as e:
        logger.error(f"Connect account error: {e}")
        return jsonify({"error": str(e)}), 400


# --- CONNECT: Create Payment with Application Fee ---
@stripe_bp.route("/stripe/create-connect-payment", methods=["POST"])
def create_connect_payment():
    """Create a payment that splits between platform and connected account."""
    data = request.json or {}
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": data.get("currency", "usd"),
                    "product_data": {"name": data.get("product_name", "Product")},
                    "unit_amount": data.get("amount", 1000),
                },
                "quantity": data.get("quantity", 1),
            }],
            mode="payment",
            success_url=data.get("success_url", "https://auldihasibuan.pythonanywhere.com/stripe/success"),
            cancel_url=data.get("cancel_url", "https://auldihasibuan.pythonanywhere.com/stripe/cancel"),
            payment_intent_data={
                "application_fee_amount": data.get("platform_fee", 100),  # Platform fee in cents
                "transfer_data": {
                    "destination": data.get("connected_account_id"),
                },
            },
        )
        return jsonify({"session_id": session.id, "url": session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Connect payment error: {e}")
        return jsonify({"error": str(e)}), 400


# --- WEBHOOKS ---
@stripe_bp.route("/stripe/webhook", methods=["POST"])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
        
        event_type = event.get("type", "")
        logger.info(f"Webhook received: {event_type}")
        
        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            logger.info(f"Payment completed: {session.get('id')}")
            # Fulfill order here
        
        elif event_type == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            logger.info(f"Invoice paid: {invoice.get('id')}")
        
        elif event_type == "customer.subscription.created":
            sub = event["data"]["object"]
            logger.info(f"Subscription created: {sub.get('id')}")
        
        elif event_type == "customer.subscription.deleted":
            sub = event["data"]["object"]
            logger.info(f"Subscription cancelled: {sub.get('id')}")
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 400


# --- STATUS ---
@stripe_bp.route("/stripe/status")
def status():
    """Get Stripe integration status."""
    try:
        account = stripe.Account.retrieve()
        return jsonify({
            "connected": True,
            "account_id": account.id,
            "business_name": account.business_profile.name if account.business_profile else "N/A",
            "country": account.country,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "publishable_key": STRIPE_PUBLISHABLE_KEY[:20] + "...",
        })
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 400


@stripe_bp.route("/stripe/success")
def success():
    session_id = request.args.get("session_id")
    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>✅ Payment Successful!</h1>
    <p>Session ID: {session_id}</p>
    <a href="/">Back to Home</a>
    </body></html>
    """


@stripe_bp.route("/stripe/cancel")
def cancel():
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>❌ Payment Cancelled</h1>
    <p>Your payment was cancelled.</p>
    <a href="/">Back to Home</a>
    </body></html>
    """


@stripe_bp.route("/stripe/connect/refresh")
def connect_refresh():
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>⚠️ Onboarding Incomplete</h1>
    <p>Please complete your account setup.</p>
    <a href="/">Back to Home</a>
    </body></html>
    """


@stripe_bp.route("/stripe/connect/return")
def connect_return():
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;">
    <h1>✅ Account Setup Complete!</h1>
    <p>Your connected account has been set up.</p>
    <a href="/">Back to Home</a>
    </body></html>
    """


if __name__ == "__main__":
    print("=== STRIPE INTEGRATION STATUS ===")
    try:
        account = stripe.Account.retrieve()
        print(f"Account ID: {account.id}")
        print(f"Business: {account.business_profile.name if account.business_profile else 'N/A'}")
        print(f"Country: {account.country}")
        print(f"Charges enabled: {account.charges_enabled}")
        print(f"Payouts enabled: {account.payouts_enabled}")
    except Exception as e:
        print(f"Error: {e}")
    print("\n=== ENDPOINTS ===")
    print("  POST /stripe/create-checkout-session  - One-time payment")
    print("  POST /stripe/create-subscription      - Recurring billing")
    print("  POST /stripe/create-invoice          - Send invoice")
    print("  POST /stripe/create-connected-account - Marketplace seller onboarding")
    print("  POST /stripe/create-connect-payment   - Split payment")
    print("  POST /stripe/webhook                 - Webhook handler")
    print("  GET  /stripe/status                  - Integration status")
    print("  GET  /stripe/success                 - Payment success page")
    print("  GET  /stripe/cancel                  - Payment cancelled page")