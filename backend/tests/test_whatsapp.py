"""
Unit tests for CyberGuard AI WhatsApp Bot Integration.
Run via: pytest backend/tests/test_whatsapp.py
"""
import pytest
from services.whatsapp_service import format_whatsapp_response, process_whatsapp_message
from models.schemas import RiskVerdict, ForensicEvidence, ScamArchetype

def test_whatsapp_response_formatting_danger():
    verdict = RiskVerdict(
        risk_score=85,
        severity="DANGER",
        confidence=0.95,
        scam_archetype=ScamArchetype.BANK_KYC_SUSPENSION,
        reasoning=[
            "🚨 Phishing URL Flagged: The link uses an unofficial domain",
            "⚠️ Impersonation Detected: Mimicry of State Bank of India"
        ],
        actionable_advisory="🛑 DO NOT CLICK. This is a fraudulent banking link.",
        safety_checklist=[
            "Block and report this number immediately.",
            "Never enter your netbanking password on third-party links."
        ]
    )
    evidence = ForensicEvidence(
        impersonated_brand="State Bank of India",
        extracted_urls=["https://sbi-kyc-update.xyz"]
    )

    formatted = format_whatsapp_response(
        session_id="WA-TEST1234",
        verdict=verdict,
        evidence=evidence,
        report_pdf_url="/api/reports/CyberGuard_Report_WA-TEST1234.pdf"
    )

    assert "🛑 *CRITICAL THREAT*" in formatted
    assert "85/100" in formatted
    assert "BANK KYC SUSPENSION" in formatted
    assert "Official 1930 Cybercrime Dossier" in formatted
    assert "Emergency" in formatted

@pytest.mark.asyncio
async def test_process_whatsapp_simulated_text():
    sample_scam = "Dear customer, your electricity power will be disconnected tonight at 9:30 PM. Pay to bescom@okaxis or call officer Mr. Sharma."
    result = await process_whatsapp_message(
        sender_number="whatsapp:+919876543210",
        incoming_text=sample_scam,
        user_language="en"
    )

    assert result["success"] is True
    assert result["verdict"].severity == "DANGER"
    assert "CYBERGUARD AI" in result["reply_text"]
    assert result["report_pdf_url"] is not None

