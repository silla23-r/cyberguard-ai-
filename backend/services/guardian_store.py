"""
SQLite Persistence Store for CyberGuard AI Real-Time Guardian Alerts.
Handles mutual 6-digit consent OTP pairing, VAPID push subscriptions,
SHA-256 alert cooldown deduplication, and 24-hour alert audit history.
"""
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from config import settings


def _get_conn() -> sqlite3.Connection:
    db_path = settings.GUARDIAN_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_guardian_db() -> None:
    """Initializes Guardian tables idempotently."""
    with _get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS guardian_links (
                device_id TEXT PRIMARY KEY,
                protected_label TEXT NOT NULL DEFAULT 'Mom',
                protected_phone TEXT NOT NULL DEFAULT '',
                guardian_name TEXT NOT NULL DEFAULT 'Family Guardian',
                guardian_phone TEXT NOT NULL,
                push_subscription_json TEXT,
                share_raw_context INTEGER NOT NULL DEFAULT 1,
                is_verified INTEGER NOT NULL DEFAULT 0,
                is_paused INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS otp_challenges (
                device_id TEXT PRIMARY KEY,
                otp_code TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                expires_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alert_cooldowns (
                dedup_key TEXT PRIMARY KEY,
                last_alerted_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS guardian_alerts (
                alert_id TEXT PRIMARY KEY,
                device_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                scam_archetype TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                delivery_channels TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def create_pairing_otp(
    device_id: str,
    guardian_phone: str,
    protected_label: str = "Mom",
    guardian_name: str = "Family Guardian",
    protected_phone: str = "",
    share_raw_context: bool = True,
) -> str:
    """Creates/updates an unverified guardian pairing and issues a 10-minute 6-digit consent OTP."""
    init_guardian_db()
    otp = f"{secrets.randbelow(900000) + 100000}"
    now = datetime.now(timezone.utc)
    expires = (now + timedelta(minutes=10)).isoformat()

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO guardian_links (
                device_id, protected_label, protected_phone, guardian_name,
                guardian_phone, share_raw_context, is_verified, is_paused, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                protected_label=excluded.protected_label,
                protected_phone=excluded.protected_phone,
                guardian_name=excluded.guardian_name,
                guardian_phone=excluded.guardian_phone,
                share_raw_context=excluded.share_raw_context,
                is_verified=0,
                is_paused=0
            """,
            (
                device_id.strip(),
                protected_label.strip() or "Mom",
                protected_phone.strip(),
                guardian_name.strip() or "Family Guardian",
                guardian_phone.strip(),
                int(share_raw_context),
                now.isoformat(),
            ),
        )
        conn.execute(
            """
            INSERT INTO otp_challenges (device_id, otp_code, attempts, expires_at)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                otp_code=excluded.otp_code, attempts=0, expires_at=excluded.expires_at
            """,
            (device_id.strip(), otp, expires),
        )
    return otp


def verify_pairing_otp(device_id: str, otp_code: str) -> bool:
    """Verifies the 6-digit consent OTP with a strict 5-attempt and 10-minute limit."""
    init_guardian_db()
    clean_id = device_id.strip()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT otp_code, attempts, expires_at FROM otp_challenges WHERE device_id = ?",
            (clean_id,),
        ).fetchone()
        if not row or row["attempts"] >= 5:
            return False
        if datetime.now(timezone.utc) > datetime.fromisoformat(row["expires_at"]):
            return False
        if not secrets.compare_digest(row["otp_code"], otp_code.strip()):
            conn.execute(
                "UPDATE otp_challenges SET attempts = attempts + 1 WHERE device_id = ?",
                (clean_id,),
            )
            return False

        conn.execute("UPDATE guardian_links SET is_verified = 1 WHERE device_id = ?", (clean_id,))
        conn.execute("DELETE FROM otp_challenges WHERE device_id = ?", (clean_id,))
        return True


def save_guardian_push_subscription(device_id: str, subscription: Dict[str, Any]) -> bool:
    """Stores the Guardian phone's Web Push subscription JSON for an already-verified link."""
    init_guardian_db()
    with _get_conn() as conn:
        cur = conn.execute(
            "UPDATE guardian_links SET push_subscription_json = ? WHERE device_id = ? AND is_verified = 1",
            (json.dumps(subscription), device_id.strip()),
        )
        return cur.rowcount > 0


def set_guardian_paused(device_id: str, paused: bool) -> bool:
    """Temporarily pauses or resumes alerts for a verified link."""
    init_guardian_db()
    with _get_conn() as conn:
        cur = conn.execute(
            "UPDATE guardian_links SET is_paused = ? WHERE device_id = ? AND is_verified = 1",
            (int(paused), device_id.strip()),
        )
        return cur.rowcount > 0


def get_guardian_link(device_id: str) -> Optional[Dict[str, Any]]:
    """Returns verified link metadata regardless of pause status (for UI status checks)."""
    if not device_id:
        return None
    init_guardian_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM guardian_links WHERE device_id = ? AND is_verified = 1",
            (device_id.strip(),),
        ).fetchone()
        return dict(row) if row else None


def get_active_guardian(device_id: str) -> Optional[Dict[str, Any]]:
    """Returns verified, unpaused guardian link ready to receive alerts."""
    link = get_guardian_link(device_id)
    if link and not link.get("is_paused"):
        return link
    return None


def is_in_cooldown(dedup_key: str, window_minutes: int = 15) -> bool:
    """Suppresses duplicate CAUTION notifications for identical indicators inside the cooldown window."""
    init_guardian_db()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(minutes=window_minutes)).isoformat()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT last_alerted_at FROM alert_cooldowns WHERE dedup_key = ?",
            (dedup_key,),
        ).fetchone()
        if row and row["last_alerted_at"] > cutoff:
            return True
        conn.execute(
            """
            INSERT INTO alert_cooldowns (dedup_key, last_alerted_at) VALUES (?, ?)
            ON CONFLICT(dedup_key) DO UPDATE SET last_alerted_at=excluded.last_alerted_at
            """,
            (dedup_key, now.isoformat()),
        )
        return False


def record_guardian_alert(
    alert_id: str,
    device_id: str,
    session_id: str,
    severity: str,
    risk_score: int,
    scam_archetype: str,
    payload: Dict[str, Any],
    delivery_channels: List[str],
) -> None:
    """Logs dispatched alert telemetry for 24-hour audit and in-app Guardian alert inbox."""
    init_guardian_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO guardian_alerts (
                alert_id, device_id, session_id, severity, risk_score,
                scam_archetype, payload_json, delivery_channels, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                device_id.strip(),
                session_id,
                severity,
                int(risk_score),
                scam_archetype,
                json.dumps(payload),
                json.dumps(delivery_channels),
                now_iso,
            ),
        )


def list_guardian_alerts(device_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Lists recent alerts for a linked protected device."""
    if not device_id:
        return []
    init_guardian_db()
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT alert_id, device_id, session_id, severity, risk_score,
                   scam_archetype, payload_json, delivery_channels, created_at
            FROM guardian_alerts
            WHERE device_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (device_id.strip(), limit),
        ).fetchall()
        results: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d.pop("payload_json"))
            except Exception:
                d["payload"] = {}
            try:
                d["delivery_channels"] = json.loads(d["delivery_channels"])
            except Exception:
                d["delivery_channels"] = []
            results.append(d)
        return results


def revoke_guardian(device_id: str) -> None:
    """Immediately deletes guardian pairing, push subscription, OTPs, and queued alert history."""
    init_guardian_db()
    clean_id = device_id.strip()
    with _get_conn() as conn:
        conn.execute("DELETE FROM guardian_links WHERE device_id = ?", (clean_id,))
        conn.execute("DELETE FROM otp_challenges WHERE device_id = ?", (clean_id,))
        conn.execute("DELETE FROM guardian_alerts WHERE device_id = ?", (clean_id,))


def purge_expired_guardian_records(max_age_hours: int = 24) -> int:
    """Purges expired OTPs, stale cooldown keys, and alert logs older than max_age_hours."""
    init_guardian_db()
    now = datetime.now(timezone.utc)
    cutoff_alerts = (now - timedelta(hours=max_age_hours)).isoformat()
    cutoff_otps = now.isoformat()
    with _get_conn() as conn:
        c1 = conn.execute("DELETE FROM otp_challenges WHERE expires_at < ?", (cutoff_otps,)).rowcount
        c2 = conn.execute("DELETE FROM alert_cooldowns WHERE last_alerted_at < ?", (cutoff_alerts,)).rowcount
        c3 = conn.execute("DELETE FROM guardian_alerts WHERE created_at < ?", (cutoff_alerts,)).rowcount
        return (c1 or 0) + (c2 or 0) + (c3 or 0)
