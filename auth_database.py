import sqlite3
import hashlib
import json
import os
import re
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [AUTH-DB]: %(message)s")
logger = logging.getLogger("AUTH_DB")

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_database")
DB_PATH = os.path.join(DB_DIR, "users.db")

# ============================================================
# DATABASE INITIALIZATION
# ============================================================
def init_db():
    """Inisialisasi database dan tabel user."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'USER',
            auth_provider TEXT DEFAULT 'local',
            provider_id TEXT,
            is_active INTEGER DEFAULT 1,
            is_suspicious INTEGER DEFAULT 0,
            suspicious_reason TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until TEXT,
            last_login TEXT,
            last_ip TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            auth_provider TEXT,
            status TEXT,
            reason TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT,
            severity TEXT,
            description TEXT,
            ip_address TEXT,
            user_id INTEGER,
            resolved INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create admin account if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='ADMIN'")
    if cursor.fetchone()[0] == 0:
        admin_hash = hash_password("Admin@SmartAI2026!")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role, auth_provider, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", "admin@smartai.id", admin_hash, "Administrator SMART AI", "ADMIN", "local", 1))
        logger.info("Admin account created.")

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")

# ============================================================
# SECURITY FUNCTIONS
# ============================================================
def hash_password(password):
    """Hash password dengan SHA-256 + salt."""
    salt = "SMART_AI_SALT_2026"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def is_ip_blocked(ip):
    """Cek apakah IP diblokir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM security_alerts
        WHERE ip_address=? AND resolved=0 AND severity='BLOCKED'
    """, (ip,))
    blocked = cursor.fetchone()[0] > 0
    conn.close()
    return blocked

def detect_suspicious(user_id, ip, action):
    """Deteksi akun mencurigakan."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    reasons = []

    # Cek failed login attempts
    cursor.execute("SELECT failed_login_attempts, locked_until FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] >= 5:
        reasons.append("Too many failed login attempts")

    # Cek login dari IP berbeda dalam waktu singkat
    cursor.execute("""
        SELECT COUNT(DISTINCT ip_address) FROM login_logs
        WHERE user_id=? AND timestamp > datetime('now', '-1 hour')
    """, (user_id,))
    distinct_ips = cursor.fetchone()[0]
    if distinct_ips > 3:
        reasons.append(f"Login from {distinct_ips} different IPs in 1 hour")

    # Cek brute force (banyak request dalam 1 menit)
    cursor.execute("""
        SELECT COUNT(*) FROM login_logs
        WHERE ip_address=? AND timestamp > datetime('now', '-1 minute')
    """, (ip,))
    recent_requests = cursor.fetchone()[0]
    if recent_requests > 10:
        reasons.append(f"Brute force detected: {recent_requests} requests in 1 minute")

    if reasons:
        cursor.execute("""
            UPDATE users SET is_suspicious=1, suspicious_reason=? WHERE id=?
        """, (", ".join(reasons), user_id))
        cursor.execute("""
            INSERT INTO security_alerts (alert_type, severity, description, ip_address, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, ("SUSPICIOUS_ACTIVITY", "WARNING", ", ".join(reasons), ip, user_id))
        conn.commit()
        logger.warning(f"Suspicious activity detected for user {user_id}: {reasons}")
    
    conn.close()
    return reasons

# ============================================================
# REGISTRATION
# ============================================================
def register_user(username, email, password, full_name, auth_provider="local", provider_id=None):
    """Daftar user baru."""
    # Validasi format
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return {"status": "error", "message": "Username harus 3-20 karakter, hanya huruf, angka, underscore."}
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return {"status": "error", "message": "Format email tidak valid."}
    if auth_provider == "local" and (not password or len(password) < 8):
        return {"status": "error", "message": "Password minimal 8 karakter."}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Cek duplikat
    cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
    if cursor.fetchone():
        conn.close()
        return {"status": "error", "message": "Username atau email sudah terdaftar."}

    pw_hash = hash_password(password) if password else None
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, auth_provider, provider_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, email, pw_hash, full_name, auth_provider, provider_id))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logger.info(f"User registered: {username} ({email}) via {auth_provider}")
    return {"status": "success", "user_id": user_id, "message": "Registrasi berhasil."}

# ============================================================
# LOGIN
# ============================================================
def login_user(username_or_email, password, ip_address, user_agent, auth_provider="local"):
    """Login user dengan verifikasi keamanan."""
    if is_ip_blocked(ip_address):
        return {"status": "error", "message": "IP Anda diblokir. Hubungi admin."}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Cari user
    cursor.execute("""
        SELECT id, username, email, password_hash, full_name, role, is_active, is_suspicious,
               failed_login_attempts, locked_until, auth_provider, provider_id
        FROM users WHERE (username=? OR email=?) AND auth_provider=?
    """, (username_or_email, username_or_email, auth_provider))
    user = cursor.fetchone()

    if not user:
        # Log failed attempt
        cursor.execute("""
            INSERT INTO login_logs (username, ip_address, user_agent, auth_provider, status, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username_or_email, ip_address, user_agent, auth_provider, "FAILED", "User not found"))
        conn.commit()
        conn.close()
        return {"status": "error", "message": "Username/email atau password salah."}

    user_id, username, email, pw_hash, full_name, role, is_active, is_suspicious, failed_attempts, locked_until, prov, prov_id = user

    # Cek apakah akun aktif
    if not is_active:
        cursor.execute("""
            INSERT INTO login_logs (user_id, username, ip_address, user_agent, auth_provider, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, ip_address, user_agent, auth_provider, "BLOCKED", "Account deactivated"))
        conn.commit()
        conn.close()
        return {"status": "error", "message": "Akun dinonaktifkan. Hubungi admin."}

    # Cek lockout
    if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
        conn.close()
        return {"status": "error", "message": f"Akun terkunci sampai {locked_until}. Coba lagi nanti."}

    # Verifikasi password (untuk local auth)
    if auth_provider == "local":
        if hash_password(password) != pw_hash:
            failed_attempts += 1
            cursor.execute("UPDATE users SET failed_login_attempts=? WHERE id=?", (failed_attempts, user_id))
            if failed_attempts >= 5:
                lock_time = (datetime.now() + timedelta(minutes=15)).isoformat()
                cursor.execute("UPDATE users SET locked_until=? WHERE id=?", (lock_time, user_id))
                cursor.execute("""
                    INSERT INTO security_alerts (alert_type, severity, description, ip_address, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """, ("BRUTE_FORCE", "WARNING", f"Account locked after {failed_attempts} failed attempts", ip_address, user_id))
            cursor.execute("""
                INSERT INTO login_logs (user_id, username, ip_address, user_agent, auth_provider, status, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, ip_address, user_agent, auth_provider, "FAILED", "Wrong password"))
            conn.commit()
            conn.close()
            return {"status": "error", "message": "Username/email atau password salah."}

    # Deteksi suspicious
    suspicious_reasons = detect_suspicious(user_id, ip_address, "login")

    # Reset failed attempts & update last login
    cursor.execute("""
        UPDATE users SET failed_login_attempts=0, locked_until=NULL, last_login=?, last_ip=?, updated_at=datetime('now') WHERE id=?
    """, (datetime.now().isoformat(), ip_address, user_id))

    cursor.execute("""
        INSERT INTO login_logs (user_id, username, ip_address, user_agent, auth_provider, status, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, ip_address, user_agent, auth_provider, "SUCCESS", "Login berhasil"))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "auth_provider": auth_provider,
            "is_suspicious": bool(is_suspicious or suspicious_reasons)
        },
        "suspicious_reasons": suspicious_reasons,
        "message": "Login berhasil."
    }

# ============================================================
# GOOGLE OAUTH LOGIN
# ============================================================
def login_google(google_id, email, full_name, ip_address, user_agent):
    """Login/register via Google OAuth."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE provider_id=? AND auth_provider='google'", (google_id,))
    user = cursor.fetchone()

    if user:
        user_id, username, role, is_active = user
        if not is_active:
            conn.close()
            return {"status": "error", "message": "Akun dinonaktifkan."}
    else:
        # Auto-register
        username = email.split("@")[0]
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            username = f"{username}_{google_id[:6]}"
        cursor.execute("""
            INSERT INTO users (username, email, full_name, role, auth_provider, provider_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, full_name, "USER", "google", google_id, 1))
        user_id = cursor.lastrowid
        conn.commit()
        logger.info(f"New Google user registered: {email}")

    conn.close()
    return login_user(username, None, ip_address, user_agent, auth_provider="google")

# ============================================================
# CAMPUS SSO LOGIN
# ============================================================
def login_campus(sso_id, email, full_name, campus_name, ip_address, user_agent):
    """Login/register via Campus SSO."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, is_active FROM users WHERE provider_id=? AND auth_provider='campus'", (sso_id,))
    user = cursor.fetchone()

    if user:
        user_id, username, role, is_active = user
        if not is_active:
            conn.close()
            return {"status": "error", "message": "Akun dinonaktifkan."}
    else:
        username = email.split("@")[0]
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            username = f"{username}_{sso_id[:6]}"
        cursor.execute("""
            INSERT INTO users (username, email, full_name, role, auth_provider, provider_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, email, full_name, "USER", "campus", sso_id, 1))
        user_id = cursor.lastrowid
        conn.commit()
        logger.info(f"New Campus SSO user registered: {email} from {campus_name}")

    conn.close()
    return login_user(username, None, ip_address, user_agent, auth_provider="campus")

# ============================================================
# ADMIN FUNCTIONS
# ============================================================
def admin_list_users():
    """Admin: list semua user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, email, full_name, role, auth_provider, is_active, is_suspicious, last_login, created_at
        FROM users ORDER BY created_at DESC
    """)
    users = []
    for row in cursor.fetchall():
        users.append({
            "id": row[0], "username": row[1], "email": row[2], "full_name": row[3],
            "role": row[4], "auth_provider": row[5], "is_active": bool(row[6]),
            "is_suspicious": bool(row[7]), "last_login": row[8], "created_at": row[9]
        })
    conn.close()
    return users

def admin_toggle_user(user_id, active):
    """Admin: aktifkan/nonaktifkan user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active=?, updated_at=datetime('now') WHERE id=?", (1 if active else 0, user_id))
    conn.commit()
    conn.close()
    logger.info(f"Admin toggled user {user_id} active={active}")
    return {"status": "success", "message": f"User {'diaktifkan' if active else 'dinonaktifkan'}."}

def admin_resolve_alert(alert_id):
    """Admin: resolve security alert."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE security_alerts SET resolved=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

def admin_get_security_alerts():
    """Admin: get unresolved security alerts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, alert_type, severity, description, ip_address, user_id, timestamp
        FROM security_alerts WHERE resolved=0 ORDER BY timestamp DESC
    """)
    alerts = []
    for row in cursor.fetchall():
        alerts.append({
            "id": row[0], "type": row[1], "severity": row[2], "description": row[3],
            "ip": row[4], "user_id": row[5], "timestamp": row[6]
        })
    conn.close()
    return alerts

def admin_get_login_logs(limit=50):
    """Admin: get login logs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, ip_address, auth_provider, status, reason, timestamp
        FROM login_logs ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    logs = []
    for row in cursor.fetchall():
        logs.append({
            "id": row[0], "username": row[1], "ip": row[2], "provider": row[3],
            "status": row[4], "reason": row[5], "timestamp": row[6]
        })
    conn.close()
    return logs

# ============================================================
# INIT ON IMPORT
# ============================================================
init_db()

if __name__ == "__main__":
    print("=== AUTH DATABASE MODULE ===")
    print(f"Database path: {DB_PATH}")
    print(f"Admin account: admin / Admin@SmartAI2026!")
    print("=== Test Registration ===")
    r = register_user("testuser", "test@example.com", "password123", "Test User")
    print(r)
    print("=== Test Login ===")
    r = login_user("testuser", "password123", "127.0.0.1", "Mozilla/5.0", "local")
    print(r)
    print("=== Test Google Login ===")
    r = login_google("google_123", "google@example.com", "Google User", "127.0.0.1", "Mozilla/5.0")
    print(r)
    print("=== Test Campus SSO ===")
    r = login_campus("campus_456", "campus@univ.ac.id", "Campus User", "UGM", "127.0.0.1", "Mozilla/5.0")
    print(r)
    print("=== Admin: List Users ===")
    users = admin_list_users()
    for u in users:
        print(f"  {u['username']} ({u['email']}) - {u['role']} - {u['auth_provider']} - suspicious: {u['is_suspicious']}")
    print("=== Security Alerts ===")
    alerts = admin_get_security_alerts()
    print(f"  Unresolved alerts: {len(alerts)}")
    print("=== Login Logs ===")
    logs = admin_get_login_logs(10)
    for l in logs:
        print(f"  {l['username']} from {l['ip']} - {l['status']} ({l['provider']})")
    print("=== DONE ===")
