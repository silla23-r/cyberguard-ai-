"""
Unit and integration tests for CyberGuard AI tools and scoring engine.
Run via: pytest backend/tests/test_tools.py
"""
import pytest
from tools.upi_validator import validate_vpa, extract_vpas_from_text
from tools.url_analyzer import extract_urls_from_text
from tools.whois_lookup import extract_domain
from services.scoring_service import calculate_verdict
from models.schemas import ForensicEvidence, ThreatIntelligence, ScamArchetype

def test_vpa_extraction():
    text = "Please pay your electricity bill to bescom.bill@okaxis or backup at test@ybl now"
    vpas = extract_vpas_from_text(text)
    assert len(vpas) == 2
    assert "bescom.bill@okaxis" in vpas
    assert "test@ybl" in vpas

def test_vpa_impersonation_detection():
    # Personal handle claiming to be Electricity Dept
    result = validate_vpa("user883921@okaxis", claimed_brand="Electricity Board")
    assert result["is_valid_format"] is True
    assert result["is_suspicious"] is True
    assert any("personal retail consumer" in r for r in result["reasons"])

def test_url_extraction():
    text = "Click http://bit.ly/sbi-verify and also visit https://cybercrime.gov.in"
    urls = extract_urls_from_text(text)
    assert len(urls) == 2
    assert "http://bit.ly/sbi-verify" in urls
    assert "https://cybercrime.gov.in" in urls

def test_domain_extraction():
    assert extract_domain("https://sub.scam-bank.com/login?id=1") == "sub.scam-bank.com"
    assert extract_domain("phishing-site.xyz/path") == "phishing-site.xyz"

def test_deterministic_scoring_high_risk():
    evidence = ForensicEvidence(
        extracted_urls=["https://fake-sbi-update.xyz"],
        impersonated_brand="State Bank of India",
        urgency_signals=["Account will be blocked immediately"]
    )
    threat_intel = ThreatIntelligence(
        domain_age_days=3,
        is_domain_suspicious=True,
        virustotal_malicious_count=4,
        is_blacklisted_domain=True
    )
    verdict = calculate_verdict(evidence, threat_intel)
    
    assert verdict.risk_score >= 70
    assert verdict.severity == "DANGER"
    assert verdict.scam_archetype in [ScamArchetype.PHISHING_LINK, ScamArchetype.UNKNOWN_SUSPICIOUS]
    assert len(verdict.reasoning) > 0

def test_deterministic_scoring_safe():
    evidence = ForensicEvidence(
        extracted_urls=["https://sbi.co.in"],
        impersonated_brand=None
    )
    threat_intel = ThreatIntelligence(
        domain_age_days=4500,
        is_domain_suspicious=False,
        virustotal_malicious_count=0,
        is_blacklisted_domain=False
    )
    verdict = calculate_verdict(evidence, threat_intel)
    
    assert verdict.risk_score < 30
    assert verdict.severity == "SAFE"
    assert verdict.scam_archetype == ScamArchetype.LEGITIMATE_SAFE

