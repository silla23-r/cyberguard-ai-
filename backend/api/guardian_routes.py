"""
FastAPI Router for Real-Time Guardian Alert Pairing, Consent OTP Verification,
VAPID Web Push Subscriptions, Test Triggers, and Live Alert Inbox.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from services.guardian_notifier import _send_web_push, get_vapid_public_key, send_twilio_message
from services.guardian_store import (
    create_pairing_otp,
    get_active_guardian,
    get_guardian_link,
    list_guardian_alerts,
    record_guardian_alert,
    revoke_guardian,
    save_guardian_push_subscription,
    set_guardian_paused,
    verify_pairing_otp,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guardian", tags=["Guardian Alerts"])


class PairRequest(BaseModel):
    device_id: str
    guardian_phone: str
    guardian_name: str = "Family Guardian"
    protected_label: str = "Mom"
    protected_phone: str = ""
    share_raw_context: bool = True


class PairVerifyRequest(BaseModel):
    device_id: str
    otp_code: str


class PauseToggleRequest(BaseModel):
    device_id: str
    paused: bool


class PushSubscribeRequest(BaseModel):
    device_id: str
    subscription: Dict[str, Any]


@router.get("/vapid-public-key")
async def vapid_public_key():
    """Returns the VAPID P-256 public key for PWA Service Worker push subscription."""
    return {"public_key": get_vapid_public_key()}


@router.post("/pair/request")
async def request_guardian_pair(req: PairRequest):
    """Initiates mutual Guardian consent pairing and dispatches a 6-digit OTP."""
    if not req.device_id.strip() or not req.guardian_phone.strip():
        raise HTTPException(status_code=400, detail="device_id and guardian_phone are required.")

    otp = create_pairing_otp(
        device_id=req.device_id,
        guardian_phone=req.guardian_phone,
        protected_label=req.protected_label,
        guardian_name=req.guardian_name,
        protected_phone=req.protected_phone,
        share_raw_context=req.share_raw_context,
    )

    msg = (
        f"CyberGuard AI Consent OTP: {otp}. Share this 6-digit code with {req.protected_label} "
        "to activate real-time Guardian Scam Alerts."
    )
    delivered = await send_twilio_message(req.guardian_phone, msg, use_whatsapp=True)
    if not delivered:
        delivered = await send_twilio_message(req.guardian_phone, msg, use_whatsapp=False)

    response: Dict[str, Any] = {
        "status": "otp_issued",
        "delivered_via_twilio": delivered,
        "expires_in_minutes": 10,
    }
    # When Twilio is not configured (local/college demo mode), expose OTP preview safely for testing
    if not delivered and settings.ENVIRONMENT.lower() == "development":
        response["demo_otp_preview"] = otp

    return response


@router.post("/pair/verify")
async def verify_guardian_pair(req: PairVerifyRequest):
    """Verifies the 6-digit Consent OTP and marks the Guardian pairing active."""
    if not verify_pairing_otp(req.device_id, req.otp_code):
        raise HTTPException(status_code=400, detail="Invalid, expired, or locked 6-digit Consent OTP.")
    link = get_guardian_link(req.device_id)
    return {
        "status": "paired",
        "device_id": req.device_id,
        "protected_label": link["protected_label"] if link else "Mom",
        "guardian_name": link["guardian_name"] if link else "Family Guardian",
    }


@router.post("/push/subscribe")
async def subscribe_guardian_push(req: PushSubscribeRequest):
    """Registers the Guardian phone's Web Push subscription for a paired protected device."""
    ok = save_guardian_push_subscription(req.device_id, req.subscription)
    if not ok:
        raise HTTPException(status_code=404, detail="Device pairing not found or not yet verified.")
    return {"status": "subscribed", "device_id": req.device_id}


@router.get("/status/{device_id}")
async def get_pairing_status(device_id: str):
    """Returns active consent status, pause state, and push registration status."""
    link = get_guardian_link(device_id)
    if not link:
        return {"paired": False}
    return {
        "paired": True,
        "device_id": link["device_id"],
        "protected_label": link["protected_label"],
        "guardian_name": link["guardian_name"],
        "guardian_phone": link["guardian_phone"],
        "share_raw_context": bool(link["share_raw_context"]),
        "is_paused": bool(link["is_paused"]),
        "push_enabled": bool(link.get("push_subscription_json")),
    }


@router.post("/pause")
async def toggle_guardian_pause(req: PauseToggleRequest):
    """Allows the protected user to pause or resume Guardian alerts anytime."""
    ok = set_guardian_paused(req.device_id, req.paused)
    if not ok:
        raise HTTPException(status_code=404, detail="Active Guardian link not found.")
    return {"status": "paused" if req.paused else "active", "is_paused": req.paused}


@router.delete("/pair/{device_id}")
async def unlink_guardian(device_id: str):
    """One-tap permanent consent revocation and purge of linked records."""
    revoke_guardian(device_id)
    return {"status": "revoked"}


@router.get("/alerts/{device_id}")
async def get_recent_alerts(device_id: str):
    """Fetches recent alerts dispatched for the linked protected device."""
    alerts = list_guardian_alerts(device_id)
    return {"device_id": device_id, "alerts": alerts}


@router.post("/test-alert/{device_id}")
async def trigger_test_guardian_alert(device_id: str):
    """Sends a harmless verification alert so Guardian & Mom can verify delivery immediately."""
    guardian = get_active_guardian(device_id)
    if not guardian:
        raise HTTPException(status_code=404, detail="No active (unpaused) verified Guardian link found.")

    alert_id = f"ALRT-TEST-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "alert_id": alert_id,
        "device_id": device_id,
        "session_id": "CG-TEST",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "protected_user_label": guardian["protected_label"],
        "protected_phone": guardian.get("protected_phone", ""),
        "guardian_name": guardian.get("guardian_name", "Family Guardian"),
        "severity": "DANGER",
        "risk_score": 92,
        "scam_archetype": "REMOTE_ACCESS_SCAM",
        "modality": "test",
        "raw_context": "TEST ALERT: Simulated scam warning verifying instant Guardian delivery to your phone.",
        "indicators": {"remote_tools": ["AnyDesk"], "phone_numbers": ["+919876543210"]},
        "top_reasons": ["Verification check triggered from CyberGuard Guardian settings."],
        "action_url": f"/?guardian_device={device_id}&alert={alert_id}",
    }

    channels = ["guardian_inbox"]
    if guardian.get("push_subscription_json"):
        if await _send_web_push(guardian["push_subscription_json"], payload, is_critical=True):
            channels.append("web_push")

    wa_ok = await send_twilio_message(
        guardian["guardian_phone"],
        f"CYBERGUARD TEST ALERT: Real-time protection is active for {guardian['protected_label']}.",
        use_whatsapp=True,
    )
    if wa_ok:
        channels.append("twilio_whatsapp")

    record_guardian_alert(
        alert_id=alert_id,
        device_id=device_id,
        session_id="CG-TEST",
        severity="DANGER",
        risk_score=92,
        scam_archetype="REMOTE_ACCESS_SCAM",
        payload=payload,
        delivery_channels=channels,
    )
    return {"status": "sent", "alert_id": alert_id, "channels": channels}
