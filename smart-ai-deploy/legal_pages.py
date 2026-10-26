from flask import Blueprint, render_template_string

legal_bp = Blueprint("legal", __name__)

TOS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="tiktok-developers-site-verification" content="rhhPWWVpfq6zkinXLbqdmT9z7ZY1oNa3" />
<title>Terms of Service - APH Media</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
h1 { color: #2E7D32; }
h2 { color: #1B5E20; margin-top: 20px; }
</style>
</head>
<body>
<h1>Terms of Service</h1>
<p><strong>Effective Date:</strong> October 26, 2026</p>
<p><strong>Last Updated:</strong> October 26, 2026</p>

<h2>1. Acceptance of Terms</h2>
<p>By accessing or using APH Media services ("Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>

<h2>2. Description of Service</h2>
<p>APH Media provides digital content management, social media integration, and business automation tools. The Service includes API integrations with third-party platforms (TikTok, Facebook, Instagram, etc.) for authorized content publishing and analytics.</p>

<h2>3. User Responsibilities</h2>
<p>You are responsible for:</p>
<ul>
<li>Maintaining the confidentiality of your account credentials</li>
<li>All activities that occur under your account</li>
<li>Ensuring your content complies with applicable laws and platform terms</li>
<li>Not using the Service for any illegal or unauthorized purpose</li>
</ul>

<h2>4. Third-Party Platform Integration</h2>
<p>The Service integrates with third-party platforms (TikTok, Meta/Facebook, Instagram, etc.). Your use of these platforms is subject to their respective terms of service and privacy policies. APH Media is not responsible for third-party platform actions or content.</p>

<h2>5. Content Ownership</h2>
<p>You retain ownership of all content you create and publish through the Service. By using the Service, you grant APH Media a limited license to process and transmit your content to authorized third-party platforms.</p>

<h2>6. Prohibited Uses</h2>
<p>You may not use the Service to:</p>
<ul>
<li>Violate any applicable laws or regulations</li>
<li>Infringe on intellectual property rights</li>
<li>Transmit harmful, offensive, or illegal content</li>
<li>Attempt to gain unauthorized access to systems</li>
<li>Interfere with the Service's operation</li>
</ul>

<h2>7. Limitation of Liability</h2>
<p>APH Media shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of the Service.</p>

<h2>8. Termination</h2>
<p>We may terminate or suspend your access to the Service at any time, with or without cause, with or without notice.</p>

<h2>9. Changes to Terms</h2>
<p>We reserve the right to modify these terms at any time. Continued use of the Service constitutes acceptance of modified terms.</p>

<h2>10. Contact</h2>
<p>For questions about these Terms, contact: auldihasibuan@gmail.com</p>

<p>&copy; 2026 APH Media. All rights reserved.</p>
</body>
</html>"""

PRIVACY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="tiktok-developers-site-verification" content="rhhPWWVpfq6zkinXLbqdmT9z7ZY1oNa3" />
<title>Privacy Policy - APH Media</title>
<style>
body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; }
h1 { color: #2E7D32; }
h2 { color: #1B5E20; margin-top: 20px; }
</style>
</head>
<body>
<h1>Privacy Policy</h1>
<p><strong>Effective Date:</strong> October 26, 2026</p>
<p><strong>Last Updated:</strong> October 26, 2026</p>

<h2>1. Information We Collect</h2>
<p>We collect information you provide directly:</p>
<ul>
<li>Account information (name, email, username)</li>
<li>Content you create and publish</li>
<li>Third-party platform authorization tokens (with your consent)</li>
<li>Usage data and analytics</li>
</ul>

<h2>2. How We Use Your Information</h2>
<p>We use your information to:</p>
<ul>
<li>Provide and maintain the Service</li>
<li>Process and publish content to authorized third-party platforms</li>
<li>Send notifications about your account and sales</li>
<li>Improve and optimize the Service</li>
<li>Comply with legal obligations</li>
</ul>

<h2>3. Third-Party Platform Data</h2>
<p>When you connect third-party platforms (TikTok, Facebook, Instagram, etc.), we access and store:</p>
<ul>
<li>Profile information (username, avatar, display name)</li>
<li>Content metadata (video titles, descriptions, engagement metrics)</li>
<li>Access tokens (encrypted and stored securely)</li>
</ul>
<p>We only access data necessary for the Service's functionality and in accordance with each platform's API terms.</p>

<h2>4. Data Storage and Security</h2>
<p>Your data is stored securely on our servers. We implement industry-standard security measures including encryption, access controls, and regular security audits. Access tokens are stored encrypted and are never shared with third parties.</p>

<h2>5. Data Sharing</h2>
<p>We do not sell your personal information. We may share data with:</p>
<ul>
<li>Third-party platforms you have authorized (for content publishing)</li>
<li>Service providers (hosting, analytics) under confidentiality agreements</li>
<li>Legal authorities when required by law</li>
</ul>

<h2>6. Your Rights</h2>
<p>You have the right to:</p>
<ul>
<li>Access your personal data</li>
<li>Correct inaccurate data</li>
<li>Delete your account and associated data</li>
<li>Revoke third-party platform authorizations</li>
<li>Export your data</li>
</ul>

<h2>7. Cookies and Tracking</h2>
<p>We use cookies and similar technologies to maintain sessions and improve user experience. You can control cookie settings through your browser.</p>

<h2>8. Children's Privacy</h2>
<p>The Service is not intended for users under 13 years of age. We do not knowingly collect information from children.</p>

<h2>9. Changes to Privacy Policy</h2>
<p>We may update this policy periodically. We will notify users of significant changes via email or in-app notification.</p>

<h2>10. Contact</h2>
<p>For privacy questions or requests, contact: auldihasibuan@gmail.com</p>

<p>&copy; 2026 APH Media. All rights reserved.</p>
</body>
</html>"""

@legal_bp.route("/terms")
def terms():
    return render_template_string(TOS_HTML)

@legal_bp.route("/tiktokrhhPWWVpfq6zkinXLbqdmT9z7ZY1oNa3.txt")
def tiktok_verify2():
    return "tiktok-developers-site-verification=rhhPWWVpfq6zkinXLbqdmT9z7ZY1oNa3", 200, {"Content-Type": "text/plain"}

@legal_bp.route("/tiktokdjAEHrDKibHwcL3T6NxP3tPhFlsn1JCy.txt")
def tiktok_verify():
    return "tiktok-developers-site-verification=djAEHrDKibHwcL3T6NxP3tPhFlsn1JCy", 200, {"Content-Type": "text/plain"}

@legal_bp.route("/privacy")
def privacy():
    return render_template_string(PRIVACY_HTML)

if __name__ == "__main__":
    print("=== LEGAL PAGES ===")
    print("  GET /terms   - Terms of Service")
    print("  GET /privacy - Privacy Policy")