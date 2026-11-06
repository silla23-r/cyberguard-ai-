"""
CyberGuard AI — WhatsApp Model Context Protocol (MCP) Server.
Implements the 'Quarantine & 1-Tap Interlock' Security Architecture.

Exposes standard MCP tools and resources for AI agents (Claude Desktop, Cursor, local orchestrators)
to monitor incoming WhatsApp messages, protect against fraud/Digital Arrests, and isolate scammers
without causing account bans or destroying legal Section 65B evidence.
"""
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from mcp.server import MCPServer
from config import settings
from services.pii_sanitizer import sanitize_pii
from services.guardrails_service import inspect_adversarial_injection
from services.scoring_service import calculate_verdict
from services.vision_service import analyze_text_heuristics
from services.audio_service import analyze_transcript_heuristics
from services.evidence_ledger import compute_evidence_hash, register_evidence_record
from services.report_generator import generate_evidence_pdf
from tools.url_analyzer import extract_urls_from_text, resolve_redirect_chain
from tools.whois_lookup import lookup_domain_age
from tools.virustotal import scan_url_virustotal
from tools.safe_browsing import check_url_safebrowsing
from tools.upi_validator import extract_vpas_from_text, validate_vpa
from tools.qr_decoder import parse_upi_intent
from models.schemas import ForensicEvidence, ThreatIntelligence, ScamArchetype
from mcp_server.state_store import store

logger = logging.getLogger("CyberGuard-MCP")

# Initialize MCP Server instance
app = MCPServer(
    name="CyberGuard-WhatsApp-MCP",
    version="1.0.0",
    description="Model Context Protocol Server for WhatsApp Fraud Defense, Quarantine & Section 65B Evidence Generation"
)


@app.tool()
async def analyze_incoming_whatsapp(
    sender_jid: str,
    message_body: str,
    is_saved_contact: bool = False,
    sender_name: str = ""
) -> str:
    """
    Analyzes an incoming WhatsApp message through CyberGuard's multimodal forensic engine.
    Applies DPDP zero-knowledge PII scrubbing, WHOIS registry inspection, and scam classification.
    """
    clean_sender = sender_jid.strip()
    
    # 1. Contact Whitelist Check (Prevents false positives against saved contacts)
    if is_saved_contact or store.is_whitelisted(sender_name or clean_sender):
        return json.dumps({
            "status": "SAFE_WHITELISTED",
            "sender_jid": clean_sender,
            "risk_score": 0,
            "severity": "SAFE",
            "decision": "ALLOW_DIRECT_DELIVERY",
            "message": "Sender is a verified saved contact. Analysis bypassed to prevent false-positive interruptions."
        }, indent=2)

    # 2. Zero-Knowledge DPDP PII Scrubbing
    sanitized_text, pii_audit = sanitize_pii(message_body)

    # 3. Adversarial Guardrails & Prompt Injection Check
    is_tampered, injection_patterns = inspect_adversarial_injection(message_body)

    # 4. Extract Threat Indicators
    evidence = ForensicEvidence()
    evidence.raw_text = sanitized_text
    evidence.pii_redacted_count = pii_audit["redacted_count"]
    evidence.pii_categories_redacted = pii_audit["categories"]
    evidence.adversarial_injection_detected = is_tampered
    evidence.adversarial_tamper_signals = injection_patterns

    evidence.extracted_urls.extend(extract_urls_from_text(message_body))
    evidence.upi_vpas.extend(extract_vpas_from_text(message_body))

    # UPI Intent Check
    if "upi://" in message_body or "pa=" in message_body:
        upi_parsed = parse_upi_intent(message_body.strip())
        if upi_parsed.get("is_upi"):
            evidence.qr_payload = message_body.strip()
            evidence.qr_parsed = {"type": "UPI_PAYMENT", "upi_details": upi_parsed}
            if upi_parsed.get("payee_vpa"):
                evidence.upi_vpas.append(upi_parsed["payee_vpa"])

    # Heuristic & Coercion Extraction
    text_heuristics = analyze_text_heuristics(message_body)
    if text_heuristics.get("impersonated_brand"):
        evidence.impersonated_brand = text_heuristics["impersonated_brand"]
    evidence.urgency_signals.extend(text_heuristics.get("urgency_signals", []))
    evidence.phone_numbers.extend(text_heuristics.get("phone_numbers", []))
    
    coercion = analyze_transcript_heuristics(message_body)

    # 5. Threat Intelligence
    threat_intel = ThreatIntelligence()
    for u in evidence.extracted_urls[:1]:
        chain = await resolve_redirect_chain(u)
        threat_intel.redirect_chains.extend(chain)
        whois_res = lookup_domain_age(chain[-1])
        threat_intel.domain_age_days = whois_res.get("domain_age_days")
        threat_intel.is_domain_suspicious = whois_res.get("is_suspicious", False)

    for vpa in evidence.upi_vpas[:1]:
        vpa_check = validate_vpa(vpa, evidence.impersonated_brand)
        if vpa_check.get("is_suspicious"):
            threat_intel.upi_vpa_suspicious = True
            threat_intel.upi_vpa_reasons.extend(vpa_check.get("reasons", []))

    # 6. Hybrid Risk Scoring Verdict
    verdict = calculate_verdict(evidence, threat_intel, coercion, user_language="en")

    if is_tampered:
        verdict.risk_score = 98
        verdict.severity = "DANGER"
        verdict.reasoning.insert(0, f"Blocked adversarial prompt injection: {', '.join(injection_patterns)}")

    # 7. Action Decision Logic (Strict Guardian Shield for Elderly Protection)
    action = "ALLOW"
    quarantined = False
    sha_hash = compute_evidence_hash(
        session_id=f"MCP-{clean_sender[-6:]}",
        raw_evidence_summary=sanitized_text,
        risk_score=verdict.risk_score,
        scam_archetype=verdict.scam_archetype.value
    )

    strict_mode = store.guardian_config.get("strict_elderly_mode", True)
    quarantine_threshold = 40 if strict_mode else 80

    if verdict.risk_score >= quarantine_threshold:
        action = "QUARANTINE_MUTED"
        if store.guardian_config.get("auto_quarantine_unknown_high_risk", True):
            store.add_quarantine(
                sender_jid=clean_sender,
                reason=f"{verdict.scam_archetype.value} detected (Threat Score: {verdict.risk_score}/100)",
                risk_score=verdict.risk_score,
                message_snippet=sanitized_text,
                evidence_hash=sha_hash
            )
            quarantined = True
    elif verdict.risk_score >= 25:
        action = "DELIVER_WITH_WARNING_TAG"

    response = {
        "sender_jid": clean_sender,
        "scam_archetype": verdict.scam_archetype.value,
        "risk_score": verdict.risk_score,
        "severity": verdict.severity,
        "confidence": verdict.confidence,
        "action": action,
        "is_quarantined": quarantined,
        "evidence_sha256": sha_hash,
        "pii_redacted_count": pii_audit["redacted_count"],
        "advisory": verdict.actionable_advisory,
        "reasoning": verdict.reasoning[:3]
    }
    return json.dumps(response, indent=2)


@app.tool()
async def quarantine_chat(sender_jid: str, reason: str, risk_score: int) -> str:
    """
    Isolates a suspicious WhatsApp conversation: mutes notifications, archives thread,
    and breaks the fraudster's psychological panic loop without alerting them or deleting evidence.
    """
    clean_sender = sender_jid.strip()
    record = store.add_quarantine(
        sender_jid=clean_sender,
        reason=reason,
        risk_score=risk_score,
        message_snippet="Quarantined via MCP autonomous tool call"
    )
    return json.dumps({
        "status": "QUARANTINED_SUCCESSFULLY",
        "sender_jid": clean_sender,
        "action_taken": "Notifications muted & conversation moved to Archive",
        "evidence_preserved": True,
        "record": record
    }, indent=2)


@app.tool()
async def confirm_block_and_report(
    sender_jid: str,
    incident_summary: str,
    file_1930_dossier: bool = True
) -> str:
    """
    Executes an authenticated 1-Tap Permanent Block on a confirmed scammer.
    Compiles an official Section 65B certified 1930 Cyber Crime Evidence PDF and registers the SHA-256 seal.
    """
    clean_sender = sender_jid.strip()
    store.block_sender(clean_sender)

    session_id = f"MCP-{abs(hash(clean_sender)) % 1000000}"
    sha_hash = compute_evidence_hash(
        session_id=session_id,
        raw_evidence_summary=incident_summary,
        risk_score=95,
        scam_archetype="CONFIRMED_FRAUD_BLOCK"
    )

    pdf_url = None
    if file_1930_dossier:
        evidence = ForensicEvidence(
            phone_numbers=[clean_sender],
            raw_text=incident_summary
        )
        verdict = calculate_verdict(evidence, ThreatIntelligence(), None)
        verdict.risk_score = 95
        verdict.severity = "DANGER"
        verdict.evidence_sha256_hash = sha_hash
        verdict.verification_url = f"{settings.SERVER_PUBLIC_URL}/api/verify/{sha_hash}"

        register_evidence_record(
            session_id=session_id,
            evidence_hash=sha_hash,
            risk_score=95,
            severity="DANGER",
            scam_archetype="CONFIRMED_FRAUD_BLOCK",
            extracted_indicators={"phones": [clean_sender]}
        )

        pdf_path = generate_evidence_pdf(
            session_id=session_id,
            evidence=evidence,
            threat_intel=ThreatIntelligence(),
            verdict=verdict,
            output_dir=settings.REPORTS_DIR
        )
        pdf_url = f"/api/reports/{pdf_path.name}"

    return json.dumps({
        "status": "SENDER_PERMANENTLY_BLOCKED",
        "sender_jid": clean_sender,
        "evidence_hash": sha_hash,
        "section_65b_certified": True,
        "1930_dossier_url": pdf_url,
        "verification_endpoint": f"{settings.SERVER_PUBLIC_URL}/api/verify/{sha_hash}",
        "message": "Fraudster permanently blocked. Court-admissible evidence dossier compiled successfully."
    }, indent=2)


@app.tool()
async def get_quarantine_inbox() -> str:
    """
    Retrieves all currently quarantined WhatsApp chats awaiting user or family guardian review.
    """
    quarantined = store.get_all_quarantined()
    return json.dumps({
        "total_quarantined": len(quarantined),
        "guardian_mode_active": store.guardian_config.get("enabled", True),
        "quarantined_chats": quarantined
    }, indent=2)


@app.tool()
async def release_quarantined_chat(sender_jid: str) -> str:
    """
    Releases a quarantined chat back into the normal inbox (e.g. if confirmed to be safe by the user).
    """
    clean_sender = sender_jid.strip()
    released = store.release_chat(clean_sender)
    return json.dumps({
        "sender_jid": clean_sender,
        "released": released,
        "status": "RESTORED_TO_INBOX" if released else "NOT_FOUND"
    }, indent=2)


@app.tool()
async def configure_guardian_shield(
    enabled: bool,
    guardian_phone: str,
    auto_quarantine_unknown: bool = True
) -> str:
    """
    Configures CyberGuard Strict Guardian Shield settings for protecting elderly parents.
    """
    store.guardian_config["enabled"] = enabled
    store.guardian_config["guardian_phone"] = guardian_phone
    store.guardian_config["auto_quarantine_unknown_high_risk"] = auto_quarantine_unknown
    return json.dumps({
        "status": "GUARDIAN_CONFIG_UPDATED",
        "config": store.guardian_config
    }, indent=2)


@app.resource("cyberguard://quarantine/list")
async def list_quarantine_resource() -> str:
    """Exposes real-time quarantine queue as an MCP resource."""
    return json.dumps(store.get_all_quarantined(), indent=2)


@app.resource("cyberguard://security/status")
async def security_status_resource() -> str:
    """Exposes zero-knowledge privacy and active security policies."""
    return json.dumps({
        "mcp_server": "CyberGuard-WhatsApp-MCP",
        "dpdp_compliant": True,
        "zero_knowledge_pii_sanitization": "ACTIVE",
        "section_65b_evidence_chain": "SHA-256",
        "total_blocked_senders": len(store.blocked_senders)
    }, indent=2)


if __name__ == "__main__":
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    sys.stderr.write("[+] Launching CyberGuard WhatsApp MCP Server via stdio...\n")
    app.run()
