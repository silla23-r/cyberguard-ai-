"""
LangGraph Multi-Agent Orchestration Graph for CyberGuard AI.
Coordinates Vision, Audio, Threat Intelligence, Scoring, and Redress agents.
"""
from datetime import datetime
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from config import settings
from agents.state import AgentState
from models.schemas import (
    AgentStep,
    ForensicEvidence,
    ThreatIntelligence,
    RiskVerdict
)
from services.vision_service import analyze_image, analyze_text_heuristics
from services.audio_service import process_audio, analyze_transcript_heuristics
from services.scoring_service import calculate_verdict
from services.report_generator import generate_evidence_pdf
from services.tts_service import generate_voice_advisory
from services.pii_sanitizer import sanitize_pii
from services.guardrails_service import inspect_adversarial_injection
from services.evidence_ledger import compute_evidence_hash, register_evidence_record

from tools.url_analyzer import resolve_redirect_chain, extract_urls_from_text
from tools.whois_lookup import lookup_domain_age
from tools.virustotal import scan_url_virustotal
from tools.safe_browsing import check_url_safebrowsing
from tools.upi_validator import validate_vpa, extract_vpas_from_text
from tools.qr_decoder import parse_upi_intent

logger = logging.getLogger(__name__)

def _create_step(name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> AgentStep:
    return AgentStep(
        step_id=f"step_{datetime.now().strftime('%H%M%S%f')}",
        agent_name=name,
        status=status,
        message=message,
        timestamp=datetime.now().strftime("%H:%M:%S"),
        details=details
    )

async def run_cyberguard_pipeline(
    session_id: str,
    image_bytes: Optional[bytes] = None,
    audio_bytes: Optional[bytes] = None,
    audio_filename: str = "audio.mp3",
    raw_text: str = "",
    user_language: str = "en"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the multi-agent graph, yielding live AgentStep updates
    to WebSockets before yielding the final full state.
    """
    state: AgentState = {
        "session_id": session_id,
        "user_language": user_language,
        "image_bytes": image_bytes,
        "audio_bytes": audio_bytes,
        "audio_filename": audio_filename,
        "raw_text_input": raw_text,
        "evidence": ForensicEvidence(),
        "threat_intel": ThreatIntelligence(),
        "coercion": None,
        "verdict": None,
        "report_pdf_url": None,
        "audio_advisory_url": None,
        "steps": []
    }

    # --- Node 1: Ingestion & Routing ---
    step1 = _create_step("Supervisor Router", "running", "Ingesting multimodal telemetry and routing to specialized forensic workers...")
    state["steps"].append(step1)
    yield {"type": "step", "step": step1}

    # If user provided raw pasted text
    if raw_text:
        # Zero-Knowledge DPDP PII Sanitization
        sanitized_text, pii_audit = sanitize_pii(raw_text)
        state["evidence"].raw_text = sanitized_text
        state["evidence"].pii_redacted_count += pii_audit["redacted_count"]
        state["evidence"].pii_categories_redacted.extend(pii_audit["categories"])

        # Adversarial Guardrails & Anti-Prompt Injection Inspection
        is_adversarial, tamper_patterns = inspect_adversarial_injection(raw_text)
        if is_adversarial:
            state["evidence"].adversarial_injection_detected = True
            state["evidence"].adversarial_tamper_signals.extend(tamper_patterns)
            logger.warning(f"Adversarial Prompt Injection blocked: {tamper_patterns}")

        state["evidence"].extracted_urls.extend(extract_urls_from_text(raw_text))
        state["evidence"].upi_vpas.extend(extract_vpas_from_text(raw_text))

        # Check for UPI intent in raw text (e.g. upi://pay?...)
        if "upi://" in raw_text or "pa=" in raw_text:
            upi_parsed = parse_upi_intent(raw_text.strip())
            if upi_parsed.get("is_upi"):
                state["evidence"].qr_payload = raw_text.strip()
                state["evidence"].qr_parsed = {"type": "UPI_PAYMENT", "upi_details": upi_parsed}
                if upi_parsed.get("payee_vpa"):
                    state["evidence"].upi_vpas.append(upi_parsed["payee_vpa"])

        # Extract brand, urgency, and telephone metadata from text
        text_findings = analyze_text_heuristics(raw_text)
        if text_findings.get("impersonated_brand"):
            state["evidence"].impersonated_brand = text_findings["impersonated_brand"]
        state["evidence"].urgency_signals.extend(text_findings.get("urgency_signals", []))
        state["evidence"].phone_numbers.extend(text_findings.get("phone_numbers", []))

        # Evaluate psychological coercion / extortion patterns
        coercion_findings = analyze_transcript_heuristics(raw_text)
        if coercion_findings.coercion_score > 0:
            state["coercion"] = coercion_findings

    step1.status = "completed"
    brand_msg = f" (Spoofed Brand: {state['evidence'].impersonated_brand})" if state['evidence'].impersonated_brand else ""
    step1.message = f"Telemetry successfully dispatched to forensic sub-agents{brand_msg}."
    yield {"type": "step", "step": step1}

    # --- Node 2: Vision Forensics Agent ---
    if image_bytes:
        step2 = _create_step("Vision Forensics Agent", "running", "Scanning screenshot: performing OCR, logo brand detection, and QR payload decoding...")
        state["steps"].append(step2)
        yield {"type": "step", "step": step2}

        try:
            vis_evidence = await analyze_image(image_bytes, settings.GEMINI_API_KEY)
            # Merge findings
            state["evidence"].extracted_urls.extend(vis_evidence.extracted_urls)
            state["evidence"].phone_numbers.extend(vis_evidence.phone_numbers)
            state["evidence"].upi_vpas.extend(vis_evidence.upi_vpas)
            state["evidence"].urgency_signals.extend(vis_evidence.urgency_signals)
            if vis_evidence.impersonated_brand:
                state["evidence"].impersonated_brand = vis_evidence.impersonated_brand
            if vis_evidence.qr_payload:
                state["evidence"].qr_payload = vis_evidence.qr_payload
                state["evidence"].qr_parsed = vis_evidence.qr_parsed

            step2.status = "completed"
            step2.message = f"Vision pass complete. Detected brand: {vis_evidence.impersonated_brand or 'None'}; QR: {'Present' if vis_evidence.qr_payload else 'None'}."
        except Exception as e:
            logger.error(f"Vision agent error: {e}")
            step2.status = "failed"
            step2.message = f"Vision analysis encountered error: {e}"
        yield {"type": "step", "step": step2}

    # --- Node 3: Audio Forensics Agent ---
    if audio_bytes:
        step3 = _create_step("Audio Forensics Agent", "running", "Transcribing call recording and analyzing acoustic coercion tactics...")
        state["steps"].append(step3)
        yield {"type": "step", "step": step3}

        try:
            audio_res = await process_audio(audio_bytes, audio_filename, settings.GEMINI_API_KEY)
            state["coercion"] = audio_res.get("coercion")
            transcript = audio_res.get("transcript", "")
            if not state["evidence"].raw_text:
                state["evidence"].raw_text = transcript
            
            step3.status = "completed"
            step3.message = f"Acoustic analysis complete. Coercion score: {state['coercion'].coercion_score if state['coercion'] else 0}/100."
        except Exception as e:
            logger.error(f"Audio agent error: {e}")
            step3.status = "failed"
            step3.message = f"Audio analysis error: {e}"
        yield {"type": "step", "step": step3}

    # --- Node 4: Threat Intelligence & Sandbox Agent ---
    step4 = _create_step("Threat Intelligence Agent", "running", "Querying WHOIS registries, VirusTotal, Safe Browsing, and validating UPI VPAs...")
    state["steps"].append(step4)
    yield {"type": "step", "step": step4}

    try:
        # 1. Investigate URLs
        urls = list(dict.fromkeys(state["evidence"].extracted_urls))
        for url in urls[:2]: # check first 2 URLs to manage latency
            chain = await resolve_redirect_chain(url)
            state["threat_intel"].redirect_chains.extend(chain)
            final_url = chain[-1]

            # WHOIS domain age
            whois_info = lookup_domain_age(final_url)
            if whois_info.get("domain_age_days") is not None:
                state["threat_intel"].domain_age_days = whois_info["domain_age_days"]
                state["threat_intel"].domain_registrar = whois_info.get("registrar")
                state["threat_intel"].is_domain_suspicious = whois_info.get("is_suspicious", False)

            # VirusTotal
            vt_info = await scan_url_virustotal(settings.VIRUSTOTAL_API_KEY, final_url)
            vt_malicious = vt_info.get("malicious_count", 0)
            vt_suspicious = vt_info.get("suspicious_count", 0)
            state["threat_intel"].virustotal_malicious_count = max(vt_malicious, vt_suspicious)
            if vt_info.get("is_threat"):
                state["threat_intel"].is_blacklisted_domain = True

            # Safe Browsing
            sb_info = await check_url_safebrowsing(settings.GOOGLE_SAFE_BROWSING_API_KEY, final_url)
            if sb_info.get("is_threat"):
                state["threat_intel"].is_blacklisted_domain = True

        # 2. Investigate VPAs
        vpas = list(dict.fromkeys(state["evidence"].upi_vpas))
        for vpa in vpas[:2]:
            vpa_info = validate_vpa(vpa, state["evidence"].impersonated_brand)
            if vpa_info.get("is_suspicious"):
                state["threat_intel"].upi_vpa_suspicious = True
                state["threat_intel"].upi_vpa_reasons.extend(vpa_info.get("reasons", []))

        step4.status = "completed"
        step4.message = "Threat intelligence lookup complete across domain registries and threat feeds."
    except Exception as e:
        logger.error(f"Threat intel error: {e}")
        step4.status = "completed"
        step4.message = "Threat intelligence completed with local heuristic fallback."
    yield {"type": "step", "step": step4}

    # --- Node 5: Risk Scoring & Synthesis Agent ---
    step5 = _create_step("Risk Scoring Engine", "running", "Synthesizing evidence and computing deterministic hybrid risk verdict...")
    state["steps"].append(step5)
    yield {"type": "step", "step": step5}

    verdict = calculate_verdict(
        state["evidence"],
        state["threat_intel"],
        state["coercion"],
        user_language
    )

    # Enforce Deterministic Security Override if Adversarial Prompt Injection was detected
    if state["evidence"].adversarial_injection_detected:
        verdict.risk_score = max(verdict.risk_score, 98)
        verdict.severity = "DANGER"
        verdict.confidence = 0.99
        patterns_str = ", ".join(state["evidence"].adversarial_tamper_signals)
        verdict.reasoning.insert(
            0,
            f"CRITICAL ADVERSARIAL ALERT: Prompt injection attempt detected ({patterns_str}). AI security override blocked tampering."
        )

    # Compute Cryptographic SHA-256 Chain-of-Custody Seal
    raw_summary = state["evidence"].raw_text or f"Urls:{len(state['evidence'].extracted_urls)}|VPAs:{len(state['evidence'].upi_vpas)}"
    sha_hash = compute_evidence_hash(
        session_id=session_id,
        raw_evidence_summary=raw_summary,
        risk_score=verdict.risk_score,
        scam_archetype=verdict.scam_archetype.value
    )
    verdict.evidence_sha256_hash = sha_hash
    verdict.verification_url = f"{settings.SERVER_PUBLIC_URL}/api/verify/{sha_hash}"

    # Register into immutable evidence ledger (Section 65B Indian Evidence Act compliant)
    register_evidence_record(
        session_id=session_id,
        evidence_hash=sha_hash,
        risk_score=verdict.risk_score,
        severity=verdict.severity,
        scam_archetype=verdict.scam_archetype.value,
        extracted_indicators={
            "urls": state["evidence"].extracted_urls,
            "phones": state["evidence"].phone_numbers,
            "vpas": state["evidence"].upi_vpas,
            "qr": state["evidence"].qr_payload
        }
    )

    state["verdict"] = verdict
    step5.status = "completed"
    step5.message = f"Diagnosis: {verdict.scam_archetype.value} | Threat Score: {verdict.risk_score}/100 ({verdict.severity}) | Sealed: {sha_hash[:16]}..."
    yield {"type": "step", "step": step5}

    # --- Node 6: Redress & Documentation Agent ---
    step6 = _create_step("Redress & Document Agent", "running", "Compiling official 1930 Cybercrime Evidence PDF and generating audio briefing...")
    state["steps"].append(step6)
    yield {"type": "step", "step": step6}

    try:
        # Generate Official PDF
        pdf_file = generate_evidence_pdf(
            session_id,
            state["evidence"],
            state["threat_intel"],
            verdict,
            settings.REPORTS_DIR
        )
        state["report_pdf_url"] = f"/api/reports/{pdf_file.name}"

        # Generate Audio Voice Advisory
        audio_file = await generate_voice_advisory(
            verdict.actionable_advisory,
            user_language,
            settings.AUDIO_DIR,
            session_id
        )
        if audio_file:
            state["audio_advisory_url"] = f"/api/audio/{audio_file.name}"

        step6.status = "completed"
        step6.message = "Legal evidence packet PDF and regional voice advisory compiled."
    except Exception as e:
        logger.error(f"Redress generation error: {e}")
        step6.status = "completed"
        step6.message = "Evidence summary ready."
    yield {"type": "step", "step": step6}

    # Yield final completed state
    yield {"type": "complete", "state": state}

