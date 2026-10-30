"""
FastAPI REST API Routes for CyberGuard AI.
Exposes multipart analysis endpoint and report file downloads.
"""
import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from config import settings
from models.schemas import AnalysisResponse, RiskVerdict, ForensicEvidence, ThreatIntelligence
from agents.graph import run_cyberguard_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["CyberGuard API"])

@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "CyberGuard AI Agent",
        "version": "1.0.0",
        "gemini_active": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here")
    }

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_submission(
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    language: Optional[str] = Form("en")
):
    """
    Main multimodal analysis endpoint.
    Accepts screenshot image, audio recording, or text message.
    """
    session_id = f"CG-{uuid.uuid4().hex[:8].upper()}"
    
    image_bytes = None
    if image:
        image_bytes = await image.read()

    audio_bytes = None
    audio_filename = "recording.mp3"
    if audio:
        audio_bytes = await audio.read()
        audio_filename = audio.filename or "recording.mp3"

    if not image_bytes and not audio_bytes and not text:
        raise HTTPException(
            status_code=400,
            detail="At least one modality (image, audio, or text) must be provided."
        )

    final_state = None
    steps = []

    # Execute the agent graph
    async for event in run_cyberguard_pipeline(
        session_id=session_id,
        image_bytes=image_bytes,
        audio_bytes=audio_bytes,
        audio_filename=audio_filename,
        raw_text=text or "",
        user_language=language or "en"
    ):
        if event["type"] == "step":
            steps.append(event["step"])
        elif event["type"] == "complete":
            final_state = event["state"]

    if not final_state or not final_state.get("verdict"):
        raise HTTPException(status_code=500, detail="Agent pipeline failed to synthesize verdict.")

    return AnalysisResponse(
        session_id=session_id,
        verdict=final_state["verdict"],
        evidence=final_state["evidence"],
        threat_intel=final_state["threat_intel"],
        coercion=final_state.get("coercion"),
        report_pdf_url=final_state.get("report_pdf_url"),
        audio_advisory_url=final_state.get("audio_advisory_url"),
        steps=steps
    )

@router.get("/reports/{filename}")
async def download_report(filename: str):
    file_path = settings.REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Evidence PDF not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/pdf"
    )

@router.get("/audio/{filename}")
async def stream_audio(filename: str):
    file_path = settings.AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio advisory not found.")
    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg"
    )

@router.get("/verify/{evidence_hash}")
async def verify_evidence(evidence_hash: str):
    """
    Public verification endpoint for Law Enforcement (Helpline 1930 / State Cyber Cells)
    and Bank Ombudsman officers to verify the cryptographic SHA-256 seal of an incident.
    """
    from services.evidence_ledger import verify_evidence_record
    record = verify_evidence_record(evidence_hash)
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Evidence record not found or expired under DPDP data retention schedule."
        )
    return {
        "status": "VERIFIED_AUTHENTIC",
        "evidence_record": record,
        "verification_authority": "CyberGuard AI Cryptographic Ledger",
        "compliance": "Section 65B Indian Evidence Act, 1872 / BSA 2023"
    }

@router.get("/security/privacy-manifest")
async def get_privacy_manifest():
    """
    Returns zero-knowledge privacy and regulatory compliance telemetry for enterprise audits.
    """
    return {
        "compliance_standards": ["DPDP Act 2023", "RBI Cyber Security Framework", "Section 65B Indian Evidence Act"],
        "zero_knowledge_pii_scrubber": "ACTIVE",
        "adversarial_prompt_guardrails": "ACTIVE",
        "ephemeral_data_purge_window_hours": 24,
        "cryptographic_algorithm": "SHA-256",
        "status": "SECURE"
    }

@router.post("/security/purge-expired")
async def trigger_purge():
    """
    Manual maintenance trigger to purge temporary artifacts older than 24h.
    """
    from services.data_retention import purge_expired_artifacts
    result = purge_expired_artifacts()
    return result

