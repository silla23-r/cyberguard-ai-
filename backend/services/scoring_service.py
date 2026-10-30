"""
Deterministic Hybrid Risk Scoring and Verdict Engine for CyberGuard AI.
Combines empirical threat intelligence, cryptographic/syntax validations,
and psychological coercion signals into an explainable 0-100 threat score.
"""
import logging
from typing import List, Optional

from models.schemas import (
    ForensicEvidence,
    ThreatIntelligence,
    CoercionAnalysis,
    RiskVerdict,
    ScamArchetype
)

logger = logging.getLogger(__name__)

def calculate_verdict(
    evidence: ForensicEvidence,
    threat_intel: ThreatIntelligence,
    coercion: Optional[CoercionAnalysis] = None,
    user_language: str = "en"
) -> RiskVerdict:
    """
    Computes a deterministic threat score (0-100) with full evidentiary justification.
    """
    score = 0
    reasoning: List[str] = []
    archetype = ScamArchetype.UNKNOWN_SUSPICIOUS

    # 1. Threat Intelligence URL & Domain Checks
    if threat_intel.virustotal_malicious_count > 0:
        points = min(40, threat_intel.virustotal_malicious_count * 10)
        score += points
        reasoning.append(f"🚨 Known Threat: Flagged as malicious by {threat_intel.virustotal_malicious_count} antivirus vendor(s) on VirusTotal (+{points} pts).")

    if threat_intel.is_blacklisted_domain:
        score += 30
        reasoning.append("🚨 Blacklist Match: Destination domain appears on Google Safe Browsing / Phishing registries (+30 pts).")

    if threat_intel.is_domain_suspicious and threat_intel.domain_age_days is not None:
        score += 25
        reasoning.append(f"⚠️ Brand New Domain: Web domain was created only {threat_intel.domain_age_days} days ago. Legitimate banks and utilities never operate on freshly registered domains (+25 pts).")

    # 1B. Heuristic Phishing & Spoofed URL Patterns
    suspicious_tlds = [".xyz", ".top", ".site", ".live", ".buzz", ".online", ".guru", ".link", ".cc"]
    phishing_keywords = ["verify", "kyc", "update", "secure", "login", "reward", "freemoney", "free-recharge", "apk", "task", "bonus"]
    
    for url in evidence.extracted_urls:
        u_lower = url.lower()
        has_tld = any(u_lower.endswith(t) or f"{t}/" in u_lower for t in suspicious_tlds)
        has_keyword = any(k in u_lower for k in phishing_keywords)
        is_apk = u_lower.endswith(".apk") or ".apk?" in u_lower

        if is_apk:
            score += 45
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"🚨 Dangerous APK Download: The link directs to an unverified Android package (.apk), which commonly installs banking trojans or spyware (+45 pts).")
            break
        elif (has_tld or has_keyword) and evidence.impersonated_brand:
            score += 35
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"🚨 Phishing URL Flagged: The link uses an unofficial domain/path containing high-risk credential-harvesting keywords (+35 pts).")
            break
        elif has_tld and has_keyword:
            score += 30
            archetype = ScamArchetype.PHISHING_LINK
            reasoning.append(f"⚠️ Suspicious Web Link: The URL contains deceptive keywords paired with an unusual domain extension (+30 pts).")
            break

    # 2. UPI & QR Code Transaction Forensic Checks
    if evidence.qr_parsed:
        qr_type = evidence.qr_parsed.get("type")
        if qr_type == "UPI_PAYMENT":
            upi = evidence.qr_parsed.get("upi_details", {})
            if upi.get("is_collect_request"):
                score += 45
                archetype = ScamArchetype.UPI_COLLECT_FRAUD
                reasoning.append("🛑 UPI Collect Fraud: The QR code is programmed to DEBIT/COLLECT money from your bank account, not credit money to you (+45 pts).")
            
            if upi.get("amount") and float(upi.get("amount") or 0) > 0:
                score += 15
                reasoning.append(f"⚠️ Pre-filled Deduction: QR initiates an immediate debit authorization for ₹{upi.get('amount')} (+15 pts).")
        elif qr_type == "WEB_URL":
            qr_url = (evidence.qr_parsed.get("url") or "").lower()
            if any(t in qr_url for t in suspicious_tlds) or any(k in qr_url for k in phishing_keywords):
                score += 40
                archetype = ScamArchetype.PHISHING_LINK
                reasoning.append("🚨 Concealed QR Phishing (Quishing): Embedded QR code payload redirects to an unofficial credential-harvesting domain (+40 pts).")

    if threat_intel.upi_vpa_suspicious:
        score += 25
        archetype = ScamArchetype.UPI_COLLECT_FRAUD
        for r in threat_intel.upi_vpa_reasons:
            reasoning.append(f"⚠️ Suspicious VPA: {r} (+25 pts).")

    # 3. Brand Impersonation Checks
    if evidence.impersonated_brand:
        score += 20
        reasoning.append(f"⚠️ Impersonation Detected: Visual or textual mimicry of '{evidence.impersonated_brand}' detected (+20 pts).")

    # 4. Psychological Coercion & Social Engineering Checks
    if coercion and coercion.coercion_score > 0:
        added_pts = int(coercion.coercion_score * 0.3)
        score += added_pts
        reasoning.append(f"⚠️ Psychological Pressure: Strong extortion / urgency tactics detected (+{added_pts} pts).")
        
        # Check for Digital Arrest or Utility Disconnection signatures
        for tactic in coercion.tactics_detected:
            reasoning.append(f"   • {tactic}")
            if "arrest" in tactic.lower() or "cbi" in tactic.lower() or "police" in tactic.lower():
                archetype = ScamArchetype.DIGITAL_ARREST
            elif "electricity" in tactic.lower() or "power" in tactic.lower():
                archetype = ScamArchetype.FAKE_ELECTRICITY_BILL

    if evidence.urgency_signals:
        score += 10
        reasoning.append(f"⚠️ Artificial Urgency: Identified {len(evidence.urgency_signals)} high-pressure phrases designed to prevent rational thinking (+10 pts).")

    # 5. Steganography & Concealed Data Checks
    if any("steganography" in u.lower() for u in evidence.urgency_signals):
        score += 40
        reasoning.append("🚨 Pixel Steganography Unmasked: Hidden payload was extracted from the image's Least Significant Bits (+40 pts).")
        if archetype == ScamArchetype.UNKNOWN_SUSPICIOUS:
            archetype = ScamArchetype.PHISHING_LINK

    # Cap final risk score at 100
    final_score = min(100, max(0, score))

    # Determine Severity Tier
    if final_score >= 65:
        severity = "DANGER"
    elif final_score >= 30:
        severity = "CAUTION"
    else:
        severity = "SAFE"
        if not reasoning:
            reasoning.append("✅ No known phishing signatures, brand spoofing, or fraudulent QR triggers detected.")
            archetype = ScamArchetype.LEGITIMATE_SAFE

    # Refine Archetype if still unknown or specific
    raw_lower = (evidence.raw_text or "").lower()
    if "kyc" in raw_lower and ("suspend" in raw_lower or "block" in raw_lower or "bank" in raw_lower):
        if final_score >= 35:
            archetype = ScamArchetype.BANK_KYC_SUSPENSION
    elif archetype == ScamArchetype.UNKNOWN_SUSPICIOUS:
        if evidence.extracted_urls and final_score >= 40:
            archetype = ScamArchetype.PHISHING_LINK
        elif evidence.impersonated_brand and "electricity" in (evidence.impersonated_brand or "").lower():
            archetype = ScamArchetype.FAKE_ELECTRICITY_BILL
        elif final_score < 30:
            archetype = ScamArchetype.LEGITIMATE_SAFE

    # Generate Plain-Language Advisory & Immediate Action Checklist
    if severity == "DANGER":
        advisory = (
            f"🛑 DO NOT PROCEED. This is a high-confidence {archetype.value.replace('_', ' ')}. "
            "Do NOT scan this QR code, do NOT click the link, and do NOT send money. "
            "Official organizations (police, banks, electricity boards) NEVER demand immediate UPI transfers "
            "or threaten arrest over video calls."
        )
        checklist = [
            "Block and report the sender's phone number on WhatsApp / SMS immediately.",
            "Never enter your UPI PIN. Remember: You NEVER need to enter your PIN to receive money.",
            "If you have already sent money, immediately call the National Cyber Crime Helpline at 1930.",
            "Report the fraud with evidence on the official portal: cybercrime.gov.in."
        ]
    elif severity == "CAUTION":
        advisory = (
            "⚠️ PROCEED WITH CAUTION. We detected suspicious indicators such as a recently created web domain "
            "or unverified sender handle. Verify directly through the official website or verified mobile app."
        )
        checklist = [
            "Do not click links received via SMS/WhatsApp. Open your browser and type the official URL yourself.",
            "Check the URL carefully for subtle spelling mistakes (e.g. sbi-kyc-update.com instead of sbi.co.in).",
            "Never share OTPs, passwords, or install remote assistance apps like AnyDesk or TeamViewer."
        ]
    else:
        advisory = "✅ NO THREATS DETECTED. This communication appears clean of known fraud indicators."
        checklist = [
            "Always verify payment amounts and recipient names before confirming transactions.",
            "Remember that genuine organizations will never ask for your confidential banking credentials."
        ]

    confidence = 0.95 if final_score > 70 or final_score < 20 else 0.82

    return RiskVerdict(
        risk_score=final_score,
        severity=severity,
        confidence=confidence,
        scam_archetype=archetype,
        reasoning=reasoning,
        actionable_advisory=advisory,
        safety_checklist=checklist
    )

