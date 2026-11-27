"""
Low-Latency Real-Time Guardian Alert Notifier for CyberGuard AI.
Implements zero-dependency RFC 8291 (aes128gcm) + RFC 8292 (VAPID ES256) Web Push
paired with Twilio WhatsApp & SMS fallback escalation and false-positive dampening.
"""
import base64
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from api.websocket import ws_manager
from config import settings
from models.schemas import CoercionAnalysis, ForensicEvidence, RiskVerdict, ScamArchetype
from services.guardian_store import (
    get_active_guardian,
    is_in_cooldown,
    record_guardian_alert,
)

logger = logging.getLogger(__name__)

CRITICAL_ARCHETYPES = {
    ScamArchetype.APK_TROJAN_MALWARE,
    ScamArchetype.REMOTE_ACCESS_SCAM,
    ScamArchetype.DIGITAL_ARREST,
    ScamArchetype.UPI_COLLECT_FRAUD,
}

TRUSTED_OFFICIAL_DOMAINS = (
    "sbi.co.in",
    "onlinesbi.sbi",
    "hdfcbank.com",
    "icicibank.com",
    "axisbank.com",
    "parivahan.gov.in",
    "cybercrime.gov.in",
    "npci.org.in",
)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(val: str) -> bytes:
    rem = len(val) % 4
    if rem:
        val += "=" * (4 - rem)
    return base64.urlsafe_b64decode(val.encode("ascii"))


def _get_or_create_vapid_keys() -> Tuple[str, ec.EllipticCurvePrivateKey]:
    """
    Returns (vapid_public_key_b64url, EC_P256_private_key).
    Uses configured .env VAPID keys if set; otherwise generates and persists a local keypair.
    """
    pub_env = (settings.VAPID_PUBLIC_KEY or "").strip()
    priv_env = (settings.VAPID_PRIVATE_KEY or "").strip()
    if pub_env and priv_env:
        try:
            if "BEGIN " in priv_env:
                priv_key = serialization.load_pem_private_key(priv_env.encode("utf-8"), password=None)
            else:
                priv_int = int.from_bytes(_b64url_decode(priv_env), "big")
                priv_key = ec.derive_private_key(priv_int, ec.SECP256R1())
            return pub_env, priv_key
        except Exception as exc:
            logger.warning(f"Invalid configured VAPID keys ({exc}); falling back to auto-generated keys.")

    key_file = settings.DATA_DIR / "vapid_keys.json"
    if key_file.exists():
        try:
            saved = json.loads(key_file.read_text(encoding="utf-8"))
            priv_int = int.from_bytes(_b64url_decode(saved["private_key"]), "big")
            priv_key = ec.derive_private_key(priv_int, ec.SECP256R1())
            return saved["public_key"], priv_key
        except Exception as exc:
            logger.warning(f"Could not read persisted VAPID keys ({exc}); regenerating.")

    priv_key = ec.generate_private_key(ec.SECP256R1())
    priv_bytes = priv_key.private_numbers().private_value.to_bytes(32, "big")
    pub_bytes = priv_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = _b64url_encode(pub_bytes)
    priv_b64 = _b64url_encode(priv_bytes)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(
            json.dumps({"public_key": pub_b64, "private_key": priv_b64}, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning(f"Could not persist VAPID keys to disk: {exc}")
    return pub_b64, priv_key


def get_vapid_public_key() -> str:
    pub_b64, _ = _get_or_create_vapid_keys()
    return pub_b64


def encrypt_web_push_payload(
    subscription: Dict[str, Any],
    payload_bytes: bytes,
    urgency: str = "high",
) -> Tuple[bytes, Dict[str, str]]:
    """
    Encrypts a Web Push payload according to RFC 8291 (aes128gcm) and signs a VAPID
    ES256 JWT (RFC 8292) using the built-in cryptography library.
    """
    endpoint = subscription["endpoint"]
    keys = subscription.get("keys", {})
    ua_pub_bytes = _b64url_decode(keys["p256dh"])
    auth_secret = _b64url_decode(keys["auth"])

    ua_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_pub_bytes)
    as_priv = ec.generate_private_key(ec.SECP256R1())
    as_pub_bytes = as_priv.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )

    shared_secret = as_priv.exchange(ec.ECDH(), ua_pub)
    ikm = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=auth_secret,
        info=b"WebPush: info\x00" + ua_pub_bytes + as_pub_bytes,
    ).derive(shared_secret)

    salt = os.urandom(16)
    cek = HKDF(
        algorithm=hashes.SHA256(),
        length=16,
        salt=salt,
        info=b"Content-Encoding: aes128gcm\x00",
    ).derive(ikm)
    nonce = HKDF(
        algorithm=hashes.SHA256(),
        length=12,
        salt=salt,
        info=b"Content-Encoding: nonce\x00",
    ).derive(ikm)

    ciphertext = AESGCM(cek).encrypt(nonce, payload_bytes + b"\x02", None)
    body = salt + (4096).to_bytes(4, "big") + bytes([len(as_pub_bytes)]) + as_pub_bytes + ciphertext

    parsed = urlparse(endpoint)
    audience = f"{parsed.scheme}://{parsed.netloc}"
    vapid_pub_b64, vapid_priv = _get_or_create_vapid_keys()

    jwt_header = _b64url_encode(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    jwt_claims = _b64url_encode(
        json.dumps(
            {
                "aud": audience,
                "exp": int(time.time()) + 12 * 3600,
                "sub": settings.VAPID_CLAIM_EMAIL,
            },
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{jwt_header}.{jwt_claims}".encode("ascii")
    der_sig = vapid_priv.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der_sig)
    raw_sig = _b64url_encode(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
    jwt_token = f"{jwt_header}.{jwt_claims}.{raw_sig}"

    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Encoding": "aes128gcm",
        "TTL": "120",
        "Urgency": urgency,
        "Authorization": f"vapid t={jwt_token}, k={vapid_pub_b64}",
    }
    return body, headers


def _is_allowlisted_official_only(evidence: ForensicEvidence) -> bool:
    """Returns True if extracted URLs point strictly to verified official portals without other risky signals."""
    if not evidence.extracted_urls or evidence.upi_vpas or evidence.apk_analysis or evidence.remote_access_tools_detected:
        return False
    for u in evidence.extracted_urls:
        host = urlparse(u).netloc.lower()
        if not any(host == d or host.endswith(f".{d}") for d in TRUSTED_OFFICIAL_DOMAINS):
            return False
    return True


def should_dispatch_guardian_alert(
    device_id: str,
    evidence: ForensicEvidence,
    verdict: RiskVerdict,
    coercion: Optional[CoercionAnalysis],
) -> Tuple[bool, bool]:
    """
    Determines whether to fire a Guardian notification and whether to escalate across SMS/WhatsApp.
    Returns (should_send, is_critical_escalation).
    """
    apk = evidence.apk_analysis
    has_critical_signal = (
        verdict.scam_archetype in CRITICAL_ARCHETYPES
        or bool(evidence.remote_access_tools_detected)
        or bool(apk and (apk.sms_interception_risk or apk.accessibility_abuse_risk))
        or bool(evidence.adversarial_injection_detected)
    )

    if verdict.severity == "DANGER" or verdict.risk_score >= 65 or has_critical_signal:
        return True, True

    if verdict.severity == "CAUTION" and verdict.risk_score >= 30:
        if _is_allowlisted_official_only(evidence):
            return False, False

        has_actionable_ioc = bool(
            evidence.extracted_urls
            or evidence.upi_vpas
            or evidence.phone_numbers
            or evidence.apk_analysis
        )
        has_coercion = bool(coercion and coercion.coercion_score >= 20)
        if not (has_actionable_ioc or has_coercion):
            return False, False

        primary_ioc = (
            (evidence.extracted_urls or evidence.upi_vpas or evidence.phone_numbers or [verdict.scam_archetype.value])[0]
        )
        dedup_key = hashlib.sha256(f"{device_id}|{primary_ioc}".encode("utf-8")).hexdigest()
        if is_in_cooldown(dedup_key, window_minutes=15):
            return False, False
        return True, False

    return False, False


async def _send_web_push(subscription_json: str, payload: Dict[str, Any], is_critical: bool) -> bool:
    if not subscription_json:
        return False
    try:
        sub = json.loads(subscription_json)
        body, headers = encrypt_web_push_payload(
            sub,
            json.dumps(payload).encode("utf-8"),
            urgency="high" if is_critical else "normal",
        )
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
            async with session.post(sub["endpoint"], data=body, headers=headers) as resp:
                if 200 <= resp.status < 300:
                    return True
                logger.warning(f"Push service responded with status {resp.status}")
                return False
    except Exception as exc:
        logger.warning(f"VAPID Web Push delivery failed: {exc}")
        return False


async def send_twilio_message(to_number: str, body: str, use_whatsapp: bool = True) -> bool:
    """Dispatches WhatsApp or SMS via Twilio REST API cleanly over aiohttp."""
    sid = (settings.TWILIO_ACCOUNT_SID or "").strip()
    token = (settings.TWILIO_AUTH_TOKEN or "").strip()
    if not sid or not token or sid == "your_twilio_sid_here":
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    clean_to = to_number.strip().replace("whatsapp:", "")
    from_val = (
        settings.TWILIO_WHATSAPP_NUMBER
        if use_whatsapp
        else settings.TWILIO_WHATSAPP_NUMBER.replace("whatsapp:", "")
    )
    to_val = f"whatsapp:{clean_to}" if use_whatsapp else clean_to

    auth = aiohttp.BasicAuth(sid, token)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.post(url, data={"From": from_val, "To": to_val, "Body": body}, auth=auth) as resp:
                if 200 <= resp.status < 300:
                    return True
                logger.warning(f"Twilio {'WhatsApp' if use_whatsapp else 'SMS'} failed: HTTP {resp.status}")
                return False
    except Exception as exc:
        logger.warning(f"Twilio dispatch error: {exc}")
        return False


async def dispatch_guardian_alert(
    device_id: Optional[str],
    session_id: str,
    raw_unredacted_text: str,
    evidence: ForensicEvidence,
    verdict: RiskVerdict,
    coercion: Optional[CoercionAnalysis],
    modality: str = "multimodal",
    report_pdf_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Evaluates alert policy and fans out notifications across WebSocket, Web Push, and Twilio fallback.
    """
    if not device_id:
        return None

    guardian = get_active_guardian(device_id)
    if not guardian:
        return None

    should_send, is_critical = should_dispatch_guardian_alert(device_id, evidence, verdict, coercion)
    if not should_send:
        return None

    alert_id = f"ALRT-{uuid.uuid4().hex[:8].upper()}"
    full_pdf_url = (
        f"{settings.SERVER_PUBLIC_URL.rstrip('/')}{report_pdf_url}"
        if report_pdf_url and report_pdf_url.startswith("/")
        else report_pdf_url
    )
    context_text = (
        (raw_unredacted_text or evidence.raw_text or "[Media scan triggered alert]")[:500]
        if guardian.get("share_raw_context")
        else "[Raw context hidden by protected user privacy preference]"
    )

    payload: Dict[str, Any] = {
        "alert_id": alert_id,
        "device_id": device_id,
        "session_id": session_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protected_user_label": guardian["protected_label"],
        "protected_phone": guardian.get("protected_phone", ""),
        "guardian_name": guardian.get("guardian_name", "Family Guardian"),
        "severity": verdict.severity,
        "risk_score": verdict.risk_score,
        "scam_archetype": verdict.scam_archetype.value,
        "modality": modality,
        "raw_context": context_text,
        "indicators": {
            "urls": evidence.extracted_urls[:4],
            "upi_vpas": evidence.upi_vpas[:4],
            "phone_numbers": evidence.phone_numbers[:4],
            "remote_tools": evidence.remote_access_tools_detected[:4],
            "apk_package": evidence.apk_analysis.package_name if evidence.apk_analysis else None,
            "apk_permissions": evidence.apk_analysis.dangerous_permissions[:6] if evidence.apk_analysis else [],
        },
        "top_reasons": verdict.reasoning[:3],
        "evidence_sha256_hash": verdict.evidence_sha256_hash,
        "verify_url": verdict.verification_url,
        "report_pdf_url": full_pdf_url,
        "action_url": f"/?guardian_device={device_id}&alert={alert_id}",
    }

    channels_used: List[str] = ["guardian_inbox"]

    # Tier 0: Instant WebSocket stream to any active Guardian tab
    try:
        await ws_manager.broadcast_step(f"guardian:{device_id}", {"type": "guardian_alert", "alert": payload})
        channels_used.append("websocket_live")
    except Exception:
        pass

    # Tier 1: Primary Web Push (VAPID)
    push_ok = False
    if guardian.get("push_subscription_json"):
        push_ok = await _send_web_push(guardian["push_subscription_json"], payload, is_critical)
        if push_ok:
            channels_used.append("web_push")

    # Tier 2 / 3: Escalate to Twilio WhatsApp -> SMS on CRITICAL/DANGER or if Web Push fails
    if is_critical or not push_ok:
        archetype_label = verdict.scam_archetype.value.replace("_", " ")
        msg_body = (
            f"CYBERGUARD GUARDIAN ALERT [{verdict.severity} {verdict.risk_score}/100]\n"
            f"Protected User: {guardian['protected_label']} | {archetype_label}\n"
            f"Context: {context_text[:200]}\n"
            f"Action: Call {guardian['protected_label']} immediately. Tell them NOT to pay, share OTP, or install APKs.\n"
            f"Verify: {verdict.verification_url or settings.SERVER_PUBLIC_URL}"
        )
        wa_ok = await send_twilio_message(guardian["guardian_phone"], msg_body, use_whatsapp=True)
        if wa_ok:
            channels_used.append("twilio_whatsapp")
        else:
            sms_ok = await send_twilio_message(guardian["guardian_phone"], msg_body, use_whatsapp=False)
            if sms_ok:
                channels_used.append("twilio_sms")

    record_guardian_alert(
        alert_id=alert_id,
        device_id=device_id,
        session_id=session_id,
        severity=verdict.severity,
        risk_score=verdict.risk_score,
        scam_archetype=verdict.scam_archetype.value,
        payload=payload,
        delivery_channels=channels_used,
    )
    logger.info(f"Guardian alert {alert_id} logged for device {device_id} via {channels_used}")
    return payload
