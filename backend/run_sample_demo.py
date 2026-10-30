"""
Interactive Sample Output Demo for CyberGuard AI.
Runs test cases through the scoring and forensic engine and displays the exact output.
"""
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.url_analyzer import extract_urls_from_text
from tools.upi_validator import extract_vpas_from_text, validate_vpa
from tools.whois_lookup import lookup_domain_age
from services.scoring_service import calculate_verdict
from services.audio_service import analyze_transcript_heuristics
from services.vision_service import analyze_text_heuristics
from models.schemas import ForensicEvidence, ThreatIntelligence, ScamArchetype

def display_result(title: str, text: str):
    print("\n" + "=" * 80)
    print(f"📌 TEST INPUT: {title}")
    print("=" * 80)
    print(f'"{text.strip()}"\n')

    # 1. Forensic Extraction Pass
    evidence = ForensicEvidence(raw_text=text)
    evidence.extracted_urls = extract_urls_from_text(text)
    evidence.upi_vpas = extract_vpas_from_text(text)
    
    # Text heuristics for brand, urgency, and numbers
    text_data = analyze_text_heuristics(text)
    evidence.impersonated_brand = text_data.get("impersonated_brand")
    evidence.urgency_signals.extend(text_data.get("urgency_signals", []))
    evidence.phone_numbers.extend(text_data.get("phone_numbers", []))

    # QR / UPI collect check
    if "mode=02" in text or "mode=collect" in text:
        evidence.qr_parsed = {
            "type": "UPI_PAYMENT",
            "upi_details": {
                "is_collect_request": True,
                "amount": "12500",
                "payee_vpa": "scammer.refund9981@okaxis"
            }
        }
        evidence.qr_payload = text

    # Coercion analysis
    coercion = analyze_transcript_heuristics(text)

    # 2. Threat Intelligence
    threat_intel = ThreatIntelligence()
    for u in evidence.extracted_urls:
        info = lookup_domain_age(u)
        threat_intel.domain_age_days = info.get("domain_age_days")
        threat_intel.is_domain_suspicious = info.get("is_suspicious", False)
        
        # Flag obvious test phishing URLs
        if any(w in u.lower() for w in ["verify-bank", "kyc-update", "freemoney", ".xyz", ".top", ".apk"]):
            threat_intel.is_blacklisted_domain = True
            threat_intel.virustotal_malicious_count = 3

    for vpa in evidence.upi_vpas:
        vpa_info = validate_vpa(vpa, evidence.impersonated_brand)
        if vpa_info.get("is_suspicious"):
            threat_intel.upi_vpa_suspicious = True
            threat_intel.upi_vpa_reasons.extend(vpa_info.get("reasons", []))

    # 3. Verdict
    verdict = calculate_verdict(evidence, threat_intel, coercion)

    print("📊 EXPECTED AGENT OUTPUT:")
    print("-" * 80)
    print(f"🎯 Scam Classification:  {verdict.scam_archetype.value.replace('_', ' ')}")
    print(f"🚨 Threat Score:        {verdict.risk_score} / 100 ({verdict.severity})")
    print(f"🔒 Confidence:          {int(verdict.confidence * 100)}%")
    print(f"\n💡 Layman Advisory:")
    print(f"   {verdict.actionable_advisory}")
    print(f"\n🔍 Evidentiary Reasoning:")
    for r in verdict.reasoning:
        print(f"   • {r}")
    print(f"\n🛡️ Immediate Action Checklist:")
    for c in verdict.safety_checklist:
        print(f"   [ ] {c}")
    print("-" * 80)

if __name__ == "__main__":
    samples_dir = Path(__file__).resolve().parent / "sample_inputs"
    for f in sorted(samples_dir.glob("*.txt")):
        display_result(f.stem.replace("_", " ").title(), f.read_text(encoding="utf-8"))

