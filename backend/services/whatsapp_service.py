"""
WhatsApp Bot Service for CyberGuard AI.
Processes forwarded messages, screenshots, and audio notes from WhatsApp,
executes multimodal forensics, and sends structured alerts back to the user.
"""
import aiohttp
import logging
import uuid
from typing import Dict, Any, Optional, Tuple

from config import settings
from agents.graph import run_cyberguard_pipeline
from models.schemas import RiskVerdict, ForensicEvidence

logger = logging.getLogger(__name__)

async def download_media(media_url: str, auth: Optional[Tuple[str, str]] = None) -> Optional[bytes]:
    """
    Downloads media attachment (screenshot image or voice note) from WhatsApp/Twilio CDN.
    """
    try:
        auth_header = None
        if auth and auth[0] and auth[1]:
            import base64
            token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
            auth_header = {"Authorization": f"Basic {token}"}

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(media_url, headers=auth_header, allow_redirects=True) as resp:
                if resp.status == 200:
                    return await resp.read()
                logger.warning(f"Failed to fetch media from {media_url}: status {resp.status}")
    except Exception as e:
        logger.error(f"Error downloading WhatsApp media from {media_url}: {e}")
    return None

def format_whatsapp_response(
    session_id: str,
    verdict: RiskVerdict,
    evidence: ForensicEvidence,
    report_pdf_url: Optional[str] = None,
    audio_advisory_url: Optional[str] = None
) -> str:
    """
    Formats the analysis verdict into an aesthetically formatted, WhatsApp-optimized markdown message.
    """
    if verdict.severity == "DANGER":
        badge = "🛑 *CRITICAL THREAT*"
        indicator = "🚨"
    elif verdict.severity == "CAUTION":
        badge = "⚠️ *SUSPICIOUS / CAUTION*"
        indicator = "⚠️"
    else:
        badge = "✅ *SAFE / CLEAN*"
        indicator = "✅"

    archetype_title = verdict.scam_archetype.value.replace("_", " ")

    lines = [
        "🛡️ *CYBERGUARD AI — FRAUD DEFENSE*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"{indicator} *Verdict*: {badge} (*{verdict.risk_score}/100*)",
        f"🎯 *Classification*: *{archetype_title}*",
        f"🔒 *Confidence*: {int(verdict.confidence * 100)}%",
        "",
        "💡 *What You Should Know*:",
        verdict.actionable_advisory,
        ""
    ]

    # Add forensic findings
    if verdict.reasoning:
        lines.append("🔍 *Key Evidentiary Findings*:")
        for r in verdict.reasoning[:4]:
            lines.append(f"• {r}")
        lines.append("")

    # Add immediate checklist
    if verdict.safety_checklist:
        lines.append("🛡️ *Immediate Next Steps*:")
        for i, item in enumerate(verdict.safety_checklist[:3], 1):
            lines.append(f"{i}. {item}")
        lines.append("")

    base_url = settings.SERVER_PUBLIC_URL.rstrip("/")
    if report_pdf_url:
        full_pdf_url = f"{base_url}{report_pdf_url}"
        lines.append(f"📄 *Download Official 1930 Cybercrime Dossier*:\n{full_pdf_url}")

    if audio_advisory_url:
        full_audio_url = f"{base_url}{audio_advisory_url}"
        lines.append(f"🎙️ *Listen to Regional Voice Warning*:\n{full_audio_url}")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "🚨 *Emergency*: Dial *1930* or visit *cybercrime.gov.in*",
        "_Forward any suspicious message or screenshot here anytime._"
    ])

    return "\n".join(lines)

async def process_whatsapp_message(
    sender_number: str,
    incoming_text: str = "",
    media_url: Optional[str] = None,
    media_content_type: Optional[str] = None,
    user_language: str = "en"
) -> Dict[str, Any]:
    """
    Unified processor for WhatsApp messages.
    Fetches media if attached, executes agent pipeline, and builds the response.
    """
    session_id = f"WA-{uuid.uuid4().hex[:8].upper()}"

    image_bytes = None
    audio_bytes = None
    audio_filename = "voice_note.mp3"

    if media_url:
        auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        media_bytes = await download_media(media_url, auth=auth)
        if media_bytes:
            content_type = (media_content_type or "").lower()
            if "image" in content_type:
                image_bytes = media_bytes
            elif "audio" in content_type or "ogg" in content_type:
                audio_bytes = media_bytes
                audio_filename = "voice_note.ogg"
            else:
                # Default to image if undetermined
                image_bytes = media_bytes

    # Execute the agent graph
    final_state = None
    steps = []

    async for event in run_cyberguard_pipeline(
        session_id=session_id,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        raw_text=incoming_text or "",
        user_language=user_language
    ):
        if event["type"] == "step":
            steps.append(event["step"])
        elif event["type"] == "complete":
            final_state = event["state"]

    if not final_state or not final_state.get("verdict"):
        return {
            "session_id": session_id,
            "success": False,
            "reply_text": "⚠️ CyberGuard AI was unable to complete forensic analysis. Please try sending the message again."
        }

    formatted_reply = format_whatsapp_response(
        session_id=session_id,
        verdict=final_state["verdict"],
        evidence=final_state["evidence"],
        report_pdf_url=final_state.get("report_pdf_url"),
        audio_advisory_url=final_state.get("audio_advisory_url")
    )

    return {
        "session_id": session_id,
        "success": True,
        "reply_text": formatted_reply,
        "verdict": final_state["verdict"],
        "evidence": final_state["evidence"],
        "report_pdf_url": final_state.get("report_pdf_url"),
        "audio_advisory_url": final_state.get("audio_advisory_url"),
        "steps": steps
    }

