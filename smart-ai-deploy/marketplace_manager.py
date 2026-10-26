import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MKT-MGR]: %(message)s")
logger = logging.getLogger("MKT-MGR")

# ============================================================
# AB NUTRISI MARKETPLACE MANAGEMENT
# ============================================================

PRODUCT = {
    "name": "Pupuk Cair Organik AB Nutrisi",
    "brand": "AB Nutrisi",
    "category": "Pupuk & Nutrisi Tanaman",
    "description": "Pupuk cair organik premium untuk pertanian organik, urban farming, dan hidroponik. Formula khusus dengan mikroorganisme aktif yang meningkatkan kesuburan tanah dan pertumbuhan tanaman.",
    "variants": [
        {"size": "1 Liter", "price": 50000, "discount": 23000, "stock": 100, "sku": "ABN-1L"},
        {"size": "5 Liter", "price": 225000, "discount": 50000, "stock": 50, "sku": "ABN-5L"},
    ],
    "features": [
        "100% Organik - tanpa bahan kimia berbahaya",
        "Meningkatkan kesuburan tanah",
        "Mempercepat pertumbuhan tanaman",
        "Cocok untuk semua jenis tanaman",
        "Aman untuk lingkungan",
        "Produksi lokal Indonesia"
    ],
    "usage": "Campur 10-20ml per liter air, semprotkan ke daun atau siram ke akar. Gunakan 2-3 kali seminggu.",
    "storage": "Simpan di tempat sejuk, kering, dan terhindar dari sinar matahari langsung.",
    "weight": {"1L": 1.2, "5L": 5.5},
}

PLATFORMS = {
    "shopee": {"name": "Shopee", "fee": 0.05, "shipping": "Shopee Xpress", "color": "#EE4D2D"},
    "tokopedia": {"name": "Tokopedia", "fee": 0.04, "shipping": "Tokopedia Send", "color": "#42B549"},
    "lazada": {"name": "Lazada", "fee": 0.06, "shipping": "Lazada Express", "color": "#0F146D"},
}

COMPETITORS = [
    {"name": "GDM", "price": 100000, "size": "2L", "platform": "Tokopedia"},
    {"name": "EM4 Pertanian", "price": 32160, "size": "1L", "platform": "Multi"},
    {"name": "INFARM", "price": 27000, "size": "1L", "platform": "Shopee"},
    {"name": "Cityfarm Booster", "price": 44550, "size": "1L", "platform": "Multi"},
    {"name": "Jimmy Hantu NPK Cair", "price": 85000, "size": "1L", "platform": "Shopee"},
]

# ============================================================
# MARKETPLACE FUNCTIONS
# ============================================================

def get_listings() -> Dict:
    """Generate listings for all platforms."""
    listings = {}
    for platform_key, platform_info in PLATFORMS.items():
        listings[platform_key] = []
        for variant in PRODUCT["variants"]:
            price = variant["price"] - variant["discount"]
            listings[platform_key].append({
                "platform": platform_info["name"],
                "product_name": f"{PRODUCT['name']} - {variant['size']}",
                "price": price,
                "original_price": variant["price"],
                "discount": variant["discount"],
                "discount_percent": round((variant["discount"] / variant["price"]) * 100, 1),
                "stock": variant["stock"],
                "sku": variant["sku"],
                "weight": PRODUCT["weight"].get(variant["size"].replace(" ", ""), 1.2),
                "shipping": platform_info["shipping"],
                "fee_percent": platform_info["fee"] * 100,
                "commission": round(price * platform_info["fee"]),
                "net_revenue": round(price * (1 - platform_info["fee"])),
                "color": platform_info["color"],
            })
    return listings

def get_pricing_analysis() -> Dict:
    """Analyze pricing vs competitors."""
    abn_price_1l = PRODUCT["variants"][0]["price"] - PRODUCT["variants"][0]["discount"]
    abn_price_5l = PRODUCT["variants"][1]["price"] - PRODUCT["variants"][1]["discount"]
    
    analysis = {
        "abn_1l": abn_price_1l,
        "abn_5l": abn_price_5l,
        "competitors": COMPETITORS,
        "position": "Mid-premium (between POC general Rp 27k and booster premium Rp 71k)",
        "recommended_actions": [
            "Maintain 1L price at Rp 27,000 (competitive vs INFARM Rp 27,000)",
            "5L bundle at Rp 175,000 (better value than 5x 1L)",
            "Flash sale: Rp 25,000 for 1L during promo periods",
            "Bundle deal: 2x 1L + gratis ongkir"
        ]
    }
    return analysis

def get_inventory() -> Dict:
    """Get inventory status."""
    total_stock = sum(v["stock"] for v in PRODUCT["variants"])
    total_value = sum(v["stock"] * (v["price"] - v["discount"]) for v in PRODUCT["variants"])
    return {
        "total_stock": total_stock,
        "total_value": total_value,
        "variants": PRODUCT["variants"],
        "reorder_point": 20,
        "needs_reorder": any(v["stock"] < 20 for v in PRODUCT["variants"]),
        "last_updated": datetime.now().isoformat()
    }

def get_sales_targets() -> Dict:
    """Get sales targets and tracking."""
    return {
        "monthly_target": 50,
        "current_month": 0,
        "progress_percent": 0,
        "daily_target": 2,
        "revenue_target": 1350000,  # 50 orders x avg Rp 27,000
        "channels": {
            "shopee": {"target": 20, "current": 0},
            "tokopedia": {"target": 20, "current": 0},
            "lazada": {"target": 10, "current": 0},
        }
    }

def get_marketing_content() -> Dict:
    """Generate marketing content for social media."""
    return {
        "promo_text": "🌿 Pupuk Cair Organik AB Nutrisi — Solusi Pertanian Organik!\n\n✅ 100% Organik\n✅ Meningkatkan kesuburan tanah\n✅ Cocok untuk semua tanaman\n\n💰 Harga spesial: Rp 27.000 (dari Rp 50.000)\n📦 Gratis ongkir min. pembelian 2 botol\n\n#PupukOrganik #PetaniMilenial #PertanianOrganik #ABNutrisi",
        "hashtags": ["#PupukOrganik", "#PetaniMilenial", "#PertanianOrganik", "#ABNutrisi", "#UrbanFarming", "#Hidroponik"],
        "caption_short": "🌿 Pupuk Organik AB Nutrisi — Rp 27.000 (hemat 46%)! Cocok untuk semua tanaman. Gratis ongkir min 2 botol. 📦",
        "caption_long": "🌿 Pupuk Cair Organik AB Nutrisi — Solusi Pertanian Organik!\n\nPupuk cair organik premium dengan mikroorganisme aktif yang meningkatkan kesuburan tanah dan mempercepat pertumbuhan tanaman.\n\n✅ 100% Organik tanpa bahan kimia\n✅ Cocok untuk semua jenis tanaman\n✅ Aman untuk lingkungan\n✅ Produksi lokal Indonesia\n\n💰 Harga: Rp 27.000 (dari Rp 50.000)\n📦 Gratis ongkir min. pembelian 2 botol\n\nOrder sekarang di Shopee/Tokopedia/Lazada!\n\n#PupukOrganik #PetaniMilenial #PertanianOrganik #ABNutrisi #UrbanFarming",
    }

def generate_full_report() -> str:
    """Generate comprehensive marketplace report."""
    listings = get_listings()
    pricing = get_pricing_analysis()
    inventory = get_inventory()
    targets = get_sales_targets()
    marketing = get_marketing_content()
    
    report = []
    report.append("=" * 70)
    report.append("AB NUTRISI — MARKETPLACE MANAGEMENT DASHBOARD")
    report.append(f"Generated: {datetime.now().strftime('%d %B %Y %H:%M WIB')}")
    report.append("=" * 70)
    report.append("")
    
    # Inventory
    report.append("📦 INVENTORY STATUS")
    report.append(f"   Total Stock: {inventory['total_stock']} unit")
    report.append(f"   Total Value: Rp {inventory['total_value']:,}")
    for v in inventory["variants"]:
        report.append(f"   - {v['size']}: {v['stock']} unit (reorder: {'⚠️ YES' if v['stock'] < 20 else 'OK'})")
    report.append("")
    
    # Pricing
    report.append("💰 PRICING ANALYSIS")
    report.append(f"   AB Nutrisi 1L: Rp {pricing['abn_1l']:,}")
    report.append(f"   AB Nutrisi 5L: Rp {pricing['abn_5l']:,}")
    report.append(f"   Position: {pricing['position']}")
    report.append("")
    report.append("   Competitor Prices (per Liter):")
    for c in pricing["competitors"]:
        report.append(f"   - {c['name']}: Rp {c['price']:,} ({c['size']}) — {c['platform']}")
    report.append("")
    
    # Platform listings
    report.append("📋 PLATFORM LISTINGS")
    for platform, items in listings.items():
        info = PLATFORMS[platform]
        report.append(f"\n   {info['name'].upper()} (Fee: {info['fee']*100}%)")
        for item in items:
            report.append(f"     SKU: {item['sku']} | {item['product_name']}")
            report.append(f"     Harga: Rp {item['price']:,} | Stock: {item['stock']} | Net: Rp {item['net_revenue']:,}")
    report.append("")
    
    # Sales targets
    report.append("🎯 SALES TARGETS")
    report.append(f"   Monthly: {targets['current_month']}/{targets['monthly_target']} orders")
    report.append(f"   Revenue Target: Rp {targets['revenue_target']:,}")
    for ch, data in targets["channels"].items():
        report.append(f"   - {ch}: {data['current']}/{data['target']}")
    report.append("")
    
    # Marketing
    report.append("📢 MARKETING CONTENT")
    report.append(f"   Short: {marketing['caption_short']}")
    report.append(f"   Hashtags: {', '.join(marketing['hashtags'])}")
    report.append("")
    
    # Recommendations
    report.append("🎯 RECOMMENDATIONS")
    for i, rec in enumerate(pricing["recommended_actions"], 1):
        report.append(f"   {i}. {rec}")
    report.append("   5. Upload foto produk high-quality ke semua platform")
    report.append("   6. Respond chat pembeli dalam 5 menit")
    report.append("   7. Kumpulkan review dari 10 pembeli pertama")
    report.append("")
    report.append("=" * 70)
    
    return "\n".join(report)

if __name__ == "__main__":
    print(generate_full_report())