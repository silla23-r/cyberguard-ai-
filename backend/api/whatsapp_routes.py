"""
WhatsApp Bot Webhook API Endpoints for CyberGuard AI.
Supports Twilio WhatsApp Webhooks, Meta WhatsApp Cloud API, and an interactive Simulator.
"""
import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Response, Form, Query, HTTPException

from config import settings
from services.whatsapp_service import process_whatsapp_message
from api.security_middleware import verify_meta_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Bot"])

class WhatsAppSimulateRequest(BaseModel):
    sender: str = "whatsapp:+919876543210"
    message: str = ""
    media_url: Optional[str] = None
    media_content_type: Optional[str] = None
    language: str = "en"

# --- 1. Twilio WhatsApp Webhook Endpoint ---
@router.post("/webhook")
async def twilio_whatsapp_webhook(
    From: str = Form(""),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None)
):
    """
    Receives incoming forwarded messages, photos, or voice notes from Twilio WhatsApp.
    Returns standard TwiML XML containing the formatted forensic warning.
    """
    logger.info(f"Incoming WhatsApp message from {From} | Body: {Body[:60]}... | Media: {MediaUrl0}")

    has_media = int(NumMedia or 0) > 0
    media_url = MediaUrl0 if has_media else None
    content_type = MediaContentType0 if has_media else None

    result = await process_whatsapp_message(
        sender_number=From,
        incoming_text=Body,
        media_url=media_url,
        media_content_type=content_type,
        user_language="en"
    )

    reply_text = result.get("reply_text", "CyberGuard analysis completed.")

    # Escape XML characters for TwiML
    import html
    escaped_body = html.escape(reply_text)

    # Return valid TwiML XML
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
        <Body>{escaped_body}</Body>
    </Message>
</Response>"""

    return Response(content=twiml_response, media_type="application/xml")

# --- 2. Meta WhatsApp Cloud API Webhook Endpoints ---
@router.get("/meta-webhook")
async def meta_webhook_verification(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
):
    """
    Verifies Meta WhatsApp Webhook endpoint during initial setup.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("Meta WhatsApp webhook successfully verified.")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch.")

@router.post("/meta-webhook")
async def meta_webhook_event(request: Request):
    """
    Receives incoming WhatsApp Cloud API events from Meta.
    Verifies HMAC-SHA256 signature to prevent spoofed webhook requests.
    """
    signature = request.headers.get("X-Hub-Signature-256", "")
    raw_body = await request.body()
    if signature and not verify_meta_webhook_signature(raw_body, signature, settings.META_WHATSAPP_TOKEN):
        logger.warning("Rejected Meta webhook request: Invalid HMAC signature.")
        raise HTTPException(status_code=401, detail="Invalid HMAC webhook signature.")

    payload = await request.json()
    logger.info(f"Received verified Meta WhatsApp event: {payload}")

    # Acknowledge receipt immediately to Meta
    return {"status": "received"}

# --- 3. Interactive WhatsApp Simulator Endpoint ---
@router.post("/simulate")
async def simulate_whatsapp_bot(request: WhatsAppSimulateRequest):
    """
    Simulator for demonstrations, presentations, and viva reviews.
    Emulates the exact WhatsApp conversation flow without requiring an active SIM or phone.
    """
    if not request.message and not request.media_url:
        raise HTTPException(status_code=400, detail="Either message text or media_url must be provided.")

    result = await process_whatsapp_message(
        sender_number=request.sender,
        incoming_text=request.message,
        media_url=request.media_url,
        media_content_type=request.media_content_type,
        user_language=request.language
    )

    return {
        "simulator_status": "success",
        "sender": request.sender,
        "incoming_message": request.message,
        "whatsapp_rendered_reply": result.get("reply_text"),
        "verdict": result.get("verdict"),
        "evidence": result.get("evidence"),
        "report_pdf_url": result.get("report_pdf_url"),
        "audio_advisory_url": result.get("audio_advisory_url"),
        "steps": result.get("steps")
    }

