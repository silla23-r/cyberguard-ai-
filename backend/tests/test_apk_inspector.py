"""
Unit and integration tests for CyberGuard AI's APK Trojan & Remote-Access Inspector.
Run via: pytest backend/tests/test_apk_inspector.py
"""
import io
import sys
import zipfile
from pathlib import Path

# Ensure backend directory is importable regardless of working directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api.routes import analyze_submission
from models.schemas import ForensicEvidence, ScamArchetype, ThreatIntelligence
from sample_inputs.create_sample_malicious_apk import build_mock_apk_bytes
from services.audio_service import analyze_transcript_heuristics
from services.report_generator import generate_evidence_pdf
from services.scoring_service import calculate_verdict
from services.vision_service import analyze_text_heuristics
from services.whatsapp_service import format_whatsapp_response
from tools.apk_inspector import MAX_APK_UPLOAD_BYTES, inspect_apk_bytes


def _run_coro_sync(coro):
    """Drives a non-blocking coroutine synchronously without binding Windows event-loop pipes."""
    try:
        while True:
            coro.send(None)
    except StopIteration as stop:
        return stop.value


def test_clean_apk_passes_safely():
    clean_bytes = build_mock_apk_bytes(
        package_name="com.example.notes",
        permissions=["INTERNET"],
        extra_strings=["Offline notes helper"],
        encode_utf16=False,
    )
    apk_res = inspect_apk_bytes(clean_bytes, filename="clean_notes.apk")

    assert apk_res.is_valid_apk is True
    assert apk_res.package_name == "com.example.notes"
    assert apk_res.dangerous_permissions == []
    assert apk_res.sms_interception_risk is False
    assert apk_res.accessibility_abuse_risk is False

    verdict = calculate_verdict(
        ForensicEvidence(apk_analysis=apk_res),
        ThreatIntelligence(),
    )
    assert verdict.severity == "SAFE"
    assert verdict.risk_score < 30


def test_malicious_utf16_apk_trojan_detected():
    trojan_bytes = build_mock_apk_bytes(
        package_name="com.rto.echallan.update",
        permissions=[
            "READ_SMS",
            "RECEIVE_SMS",
            "BIND_ACCESSIBILITY_SERVICE",
            "REQUEST_INSTALL_PACKAGES",
        ],
        extra_strings=[
            "com.sbi.lotusintouch",
            "https://rto-challan-verify.xyz/c2",
        ],
        encode_utf16=True,
    )
    apk_res = inspect_apk_bytes(trojan_bytes, filename="RTO_eChallan_Pay.apk")

    assert apk_res.is_valid_apk is True
    assert apk_res.package_name == "com.rto.echallan.update"
    assert apk_res.sms_interception_risk is True
    assert apk_res.accessibility_abuse_risk is True
    assert apk_res.sideload_dropper_risk is True
    assert "READ_SMS" in apk_res.dangerous_permissions
    assert "BIND_ACCESSIBILITY_SERVICE" in apk_res.dangerous_permissions
    assert any("SBI YONO" in app_name for app_name in apk_res.targeted_banking_apps)
    assert "https://rto-challan-verify.xyz/c2" in apk_res.embedded_urls

    verdict = calculate_verdict(
        ForensicEvidence(
            apk_analysis=apk_res,
            extracted_urls=apk_res.embedded_urls,
            impersonated_brand="Traffic Police / RTO e-Challan",
        ),
        ThreatIntelligence(),
    )
    assert verdict.risk_score >= 90
    assert verdict.severity == "DANGER"
    assert verdict.scam_archetype == ScamArchetype.APK_TROJAN_MALWARE
    assert any("Airplane Mode" in step for step in verdict.safety_checklist)


def test_corrupt_non_apk_rejected_gracefully():
    bad_res = inspect_apk_bytes(b"NOT_A_ZIP_OR_APK_FILE", filename="fake.apk")
    assert bad_res.is_valid_apk is False
    assert len(bad_res.risk_flags) > 0

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "zip without manifest")
    no_manifest = inspect_apk_bytes(buf.getvalue(), filename="random.zip")
    assert no_manifest.is_valid_apk is False
    assert any("AndroidManifest.xml" in flag for flag in no_manifest.risk_flags)


def test_oversize_apk_guard():
    oversized = b"PK\x03\x04" + (b"\x00" * MAX_APK_UPLOAD_BYTES)
    res = inspect_apk_bytes(oversized, filename="huge_bomb.apk")
    assert res.is_valid_apk is False
    assert any("maximum safe" in flag.lower() for flag in res.risk_flags)


def test_remote_access_coercion_heuristics():
    msg = (
        "URGENT SBI KYC update: Download AnyDesk and TeamViewer QuickSupport immediately "
        "or enable Install Unknown Apps for yono_kyc.apk."
    )
    text_res = analyze_text_heuristics(msg)
    assert "AnyDesk" in text_res["remote_access_tools"]
    assert "TeamViewer" in text_res["remote_access_tools"]

    coercion = analyze_transcript_heuristics(msg)
    assert coercion.coercion_score >= 30

    evidence = ForensicEvidence(
        impersonated_brand=text_res["impersonated_brand"],
        urgency_signals=text_res["urgency_signals"],
        remote_access_tools_detected=text_res["remote_access_tools"],
        raw_text=msg,
    )
    verdict = calculate_verdict(evidence, ThreatIntelligence(), coercion)
    assert verdict.severity == "DANGER"
    assert verdict.risk_score >= 65


class _MemoryUploadFile:
    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self._data = data

    async def read(self) -> bytes:
        return self._data


def test_whatsapp_and_pdf_report_include_apk_findings(tmp_path):
    apk_res = inspect_apk_bytes(
        build_mock_apk_bytes(
            package_name="com.rto.challan.pay",
            permissions=["READ_SMS", "BIND_ACCESSIBILITY_SERVICE"],
            extra_strings=["com.phonepe.app"],
            encode_utf16=True,
        ),
        filename="RTO_eChallan.apk",
    )
    evidence = ForensicEvidence(
        apk_analysis=apk_res,
        remote_access_tools_detected=["AnyDesk"],
        impersonated_brand="Traffic Police / RTO e-Challan",
    )
    verdict = calculate_verdict(evidence, ThreatIntelligence(), user_language="hi")

    reply = format_whatsapp_response(
        session_id="WA-APK01",
        verdict=verdict,
        evidence=evidence,
        report_pdf_url="/api/reports/CyberGuard_Report_WA-APK01.pdf",
    )
    assert "APK Malware Permissions" in reply
    assert "READ_SMS" in reply

    pdf_path = generate_evidence_pdf(
        session_id="CG-APKPDF01",
        evidence=evidence,
        threat_intel=ThreatIntelligence(),
        verdict=verdict,
        output_dir=tmp_path,
    )
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_analyze_submission_apk_pipeline(monkeypatch, tmp_path):
    async def _noop_voice(*args, **kwargs):
        return None

    monkeypatch.setattr("agents.graph.generate_voice_advisory", _noop_voice)
    monkeypatch.setattr("agents.graph.settings.REPORTS_DIR", tmp_path)

    trojan_bytes = build_mock_apk_bytes(
        package_name="com.kyc.sbi.updater",
        permissions=["READ_SMS", "BIND_ACCESSIBILITY_SERVICE"],
        extra_strings=["com.sbi.lotusintouch"],
        encode_utf16=True,
    )
    upload = _MemoryUploadFile("SBI_KYC_Update.apk", trojan_bytes)
    res = _run_coro_sync(
        analyze_submission(image=None, audio=None, apk_file=upload, text=None, language="hi")
    )

    assert res.verdict.severity == "DANGER"
    assert res.verdict.scam_archetype == ScamArchetype.APK_TROJAN_MALWARE
    assert res.evidence.apk_analysis is not None
    assert res.evidence.apk_analysis.package_name == "com.kyc.sbi.updater"
    assert "READ_SMS" in res.evidence.apk_analysis.dangerous_permissions
    assert res.verdict.evidence_sha256_hash is not None
    assert res.report_pdf_url is not None
    assert any(s.agent_name == "APK Malware Inspector" and s.status == "completed" for s in res.steps)
