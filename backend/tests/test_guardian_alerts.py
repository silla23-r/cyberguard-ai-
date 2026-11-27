"""
Unit and integration tests for CyberGuard AI Real-Time Guardian Alert System.
Covers SQLite consent OTP pairing, RFC 8291 Web Push encryption, false-positive
dampening, critical threat escalation, Twilio fallback, and API route handlers.
"""
import base64
import json
import os
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.guardian_routes import (
    PairRequest,
    PairVerifyRequest,
    PauseToggleRequest,
    get_pairing_status,
    get_recent_alerts,
    request_guardian_pair,
    toggle_guardian_pause,
    unlink_guardian,
    verify_guardian_pair,
)
from config import settings
from models.schemas import (
    ApkInspectionResult,
    CoercionAnalysis,
    ForensicEvidence,
    RiskVerdict,
    ScamArchetype,
)
from services.guardian_notifier import (
    dispatch_guardian_alert,
    encrypt_web_push_payload,
    should_dispatch_guardian_alert,
)
from services.guardian_store import (
    create_pairing_otp,
    get_active_guardian,
    list_guardian_alerts,
    revoke_guardian,
    save_guardian_push_subscription,
    set_guardian_paused,
    verify_pairing_otp,
)


def _run_coro_sync(coro):
    try:
        while True:
            coro.send(None)
    except StopIteration as stop:
        return stop.value


@pytest.fixture
def isolated_guardian_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "GUARDIAN_DB_PATH", tmp_path / "guardian_test.db")
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    return tmp_path


def test_consent_otp_pairing_pause_and_revoke(isolated_guardian_db):
    dev_id = "DEV-MOM-01"
    otp = create_pairing_otp(
        device_id=dev_id,
        guardian_phone="+919876543210",
        protected_label="Mom",
        guardian_name="Rohan",
        protected_phone="+919111122222",
        share_raw_context=True,
    )
    assert len(otp) == 6
    assert get_active_guardian(dev_id) is None  # Not verified yet

    # Wrong OTP rejected
    assert verify_pairing_otp(dev_id, "000000") is False
    assert get_active_guardian(dev_id) is None

    # Correct OTP verifies pairing
    assert verify_pairing_otp(dev_id, otp) is True
    active = get_active_guardian(dev_id)
    assert active is not None
    assert active["protected_label"] == "Mom"
    assert active["share_raw_context"] == 1

    # Pausing suspends active dispatch without deleting consent record
    assert set_guardian_paused(dev_id, True) is True
    assert get_active_guardian(dev_id) is None
    assert set_guardian_paused(dev_id, False) is True
    assert get_active_guardian(dev_id) is not None

    # Revoke deletes completely
    revoke_guardian(dev_id)
    assert get_active_guardian(dev_id) is None


def test_false_positive_dampening_and_critical_bypass(isolated_guardian_db):
    dev_id = "DEV-MOM-02"

    # 1. Safe verdict -> never alerts
    safe_verdict = RiskVerdict(
        risk_score=0,
        severity="SAFE",
        confidence=0.95,
        scam_archetype=ScamArchetype.LEGITIMATE_SAFE,
        actionable_advisory="Safe",
    )
    assert should_dispatch_guardian_alert(dev_id, ForensicEvidence(), safe_verdict, None) == (False, False)

    # 2. Official allowlisted bank domain flagged lightly -> suppressed
    caution_verdict = RiskVerdict(
        risk_score=35,
        severity="CAUTION",
        confidence=0.82,
        scam_archetype=ScamArchetype.UNKNOWN_SUSPICIOUS,
        actionable_advisory="Check domain",
    )
    official_ev = ForensicEvidence(extracted_urls=["https://sbi.co.in/login"])
    assert should_dispatch_guardian_alert(dev_id, official_ev, caution_verdict, None) == (False, False)

    # 3. Weak CAUTION without IOC or coercion -> suppressed
    assert should_dispatch_guardian_alert(dev_id, ForensicEvidence(), caution_verdict, None) == (False, False)

    # 4. Actionable CAUTION -> first alerts, duplicate within 15m suppressed
    caution_ev = ForensicEvidence(upi_vpas=["ramesh.bill@okaxis"])
    assert should_dispatch_guardian_alert(dev_id, caution_ev, caution_verdict, None) == (True, False)
    assert should_dispatch_guardian_alert(dev_id, caution_ev, caution_verdict, None) == (False, False)

    # 5. Critical DANGER APK trojan -> always bypasses cooldown & triggers escalation
    apk_ev = ForensicEvidence(
        apk_analysis=ApkInspectionResult(
            is_valid_apk=True,
            filename="RTO_eChallan.apk",
            sms_interception_risk=True,
            accessibility_abuse_risk=True,
        ),
        upi_vpas=["ramesh.bill@okaxis"],
    )
    danger_verdict = RiskVerdict(
        risk_score=95,
        severity="DANGER",
        confidence=0.95,
        scam_archetype=ScamArchetype.APK_TROJAN_MALWARE,
        actionable_advisory="Do not install",
    )
    assert should_dispatch_guardian_alert(dev_id, apk_ev, danger_verdict, None) == (True, True)


def test_rfc8291_web_push_encryption_roundtrip(isolated_guardian_db):
    ua_priv = ec.generate_private_key(ec.SECP256R1())
    ua_pub_bytes = ua_priv.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    auth_secret = os.urandom(16)

    subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/demo-token-123",
        "keys": {
            "p256dh": base64.urlsafe_b64encode(ua_pub_bytes).rstrip(b"=").decode("ascii"),
            "auth": base64.urlsafe_b64encode(auth_secret).rstrip(b"=").decode("ascii"),
        },
    }
    sample_payload = json.dumps({"alert_id": "ALRT-1", "risk_score": 95}).encode("utf-8")

    body, headers = encrypt_web_push_payload(subscription, sample_payload, urgency="high")
    assert headers["Content-Encoding"] == "aes128gcm"
    assert headers["Authorization"].startswith("vapid t=")
    assert ", k=" in headers["Authorization"]

    # Decrypt body as client browser push agent to verify cryptographic accuracy
    salt = body[:16]
    idlen = body[20]
    as_pub_bytes = body[21 : 21 + idlen]
    ciphertext = body[21 + idlen :]

    as_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub_bytes)
    shared = ua_priv.exchange(ec.ECDH(), as_pub)
    ikm = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=auth_secret,
        info=b"WebPush: info\x00" + ua_pub_bytes + as_pub_bytes,
    ).derive(shared)
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
    plaintext = AESGCM(cek).decrypt(nonce, ciphertext, None)
    assert plaintext.endswith(b"\x02")
    assert json.loads(plaintext[:-1].decode("utf-8"))["alert_id"] == "ALRT-1"


def test_dispatch_cascade_and_privacy_toggle(isolated_guardian_db, monkeypatch):
    dev_id = "DEV-MOM-03"
    otp = create_pairing_otp(
        device_id=dev_id,
        guardian_phone="+919876543210",
        protected_label="Mom",
        share_raw_context=True,
    )
    assert verify_pairing_otp(dev_id, otp) is True
    save_guardian_push_subscription(
        dev_id,
        {"endpoint": "https://push.example/1", "keys": {"p256dh": "x", "auth": "y"}},
    )

    twilio_calls = []

    async def _fake_push(sub_json, payload, is_critical):
        return False  # Simulate push failure to force WhatsApp -> SMS cascade

    async def _fake_twilio(to_number, body, use_whatsapp=True):
        twilio_calls.append((use_whatsapp, body))
        # Fail WhatsApp, succeed SMS
        return not use_whatsapp

    monkeypatch.setattr("services.guardian_notifier._send_web_push", _fake_push)
    monkeypatch.setattr("services.guardian_notifier.send_twilio_message", _fake_twilio)

    ev = ForensicEvidence(
        remote_access_tools_detected=["AnyDesk"],
        phone_numbers=["+919999988888"],
    )
    verdict = RiskVerdict(
        risk_score=90,
        severity="DANGER",
        confidence=0.95,
        scam_archetype=ScamArchetype.REMOTE_ACCESS_SCAM,
        reasoning=["AnyDesk screen share demanded (+40 pts)"],
        actionable_advisory="Hang up immediately",
    )

    alert = _run_coro_sync(
        dispatch_guardian_alert(
            device_id=dev_id,
            session_id="CG-TST99",
            raw_unredacted_text="Install AnyDesk now or CBI will arrest you",
            evidence=ev,
            verdict=verdict,
            coercion=CoercionAnalysis(coercion_score=50),
            modality="whatsapp",
            report_pdf_url="/api/reports/test.pdf",
        )
    )
    assert alert is not None
    assert "Install AnyDesk now" in alert["raw_context"]
    assert twilio_calls[0][0] is True   # Attempted WhatsApp first
    assert twilio_calls[1][0] is False  # Escalated to SMS fallback

    logged = list_guardian_alerts(dev_id)
    assert len(logged) == 1
    assert "twilio_sms" in logged[0]["delivery_channels"]


def test_guardian_routes_consent_lifecycle(isolated_guardian_db, monkeypatch):
    async def _noop_twilio(*args, **kwargs):
        return False

    monkeypatch.setattr("api.guardian_routes.send_twilio_message", _noop_twilio)
    dev_id = "DEV-ROUTE-01"

    req_res = _run_coro_sync(
        request_guardian_pair(
            PairRequest(
                device_id=dev_id,
                guardian_phone="+919876543210",
                protected_label="Mom",
                share_raw_context=True,
            )
        )
    )
    assert req_res["status"] == "otp_issued"
    otp = req_res["demo_otp_preview"]

    ver_res = _run_coro_sync(verify_guardian_pair(PairVerifyRequest(device_id=dev_id, otp_code=otp)))
    assert ver_res["status"] == "paired"

    st = _run_coro_sync(get_pairing_status(dev_id))
    assert st["paired"] is True
    assert st["is_paused"] is False

    p_res = _run_coro_sync(toggle_guardian_pause(PauseToggleRequest(device_id=dev_id, paused=True)))
    assert p_res["is_paused"] is True

    alerts_res = _run_coro_sync(get_recent_alerts(dev_id))
    assert alerts_res["alerts"] == []

    rev_res = _run_coro_sync(unlink_guardian(dev_id))
    assert rev_res["status"] == "revoked"
    st_after = _run_coro_sync(get_pairing_status(dev_id))
    assert st_after["paired"] is False
