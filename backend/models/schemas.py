"""
Pydantic Schemas and Domain Models for CyberGuard AI.
Strict typing ensures high-reliability data exchange across agent states.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ScamArchetype(str, Enum):
    DIGITAL_ARREST = "DIGITAL_ARREST"
    UPI_COLLECT_FRAUD = "UPI_COLLECT_FRAUD"
    PHISHING_LINK = "PHISHING_LINK"
    FAKE_ELECTRICITY_BILL = "FAKE_ELECTRICITY_BILL"
    JOB_TASK_SCAM = "JOB_TASK_SCAM"
    LOTTERY_PRIZE_SCAM = "LOTTERY_PRIZE_SCAM"
    BANK_KYC_SUSPENSION = "BANK_KYC_SUSPENSION"
    SEXTORTION_BLACKMAIL = "SEXTORTION_BLACKMAIL"
    LEGITIMATE_SAFE = "LEGITIMATE_SAFE"
    UNKNOWN_SUSPICIOUS = "UNKNOWN_SUSPICIOUS"

class ForensicEvidence(BaseModel):
    extracted_urls: List[str] = Field(default_factory=list, description="Extracted web links")
    qr_payload: Optional[str] = Field(None, description="Decoded QR payload or UPI intent")
    qr_parsed: Optional[Dict[str, Any]] = Field(None, description="Structured parsed fields of QR code")
    impersonated_brand: Optional[str] = Field(None, description="Spoofed brand/authority logo detected")
    phone_numbers: List[str] = Field(default_factory=list, description="Extracted contact phone numbers")
    upi_vpas: List[str] = Field(default_factory=list, description="Extracted UPI addresses (e.g. name@okhdfcbank)")
    urgency_signals: List[str] = Field(default_factory=list, description="Identified high-pressure psychological phrases")
    raw_text: Optional[str] = Field(None, description="Extracted OCR or transcript text")
    pii_redacted_count: int = Field(0, description="Count of sensitive PII entities redacted under DPDP Act")
    pii_categories_redacted: List[str] = Field(default_factory=list, description="Categories of masked citizen PII")
    adversarial_injection_detected: bool = Field(False, description="Flagged prompt injection or jailbreak attempt")
    adversarial_tamper_signals: List[str] = Field(default_factory=list, description="Detected prompt injection signatures")

class ThreatIntelligence(BaseModel):
    domain_age_days: Optional[int] = Field(None, description="Age of domain in days")
    domain_registrar: Optional[str] = Field(None, description="Domain registrar name")
    is_domain_suspicious: bool = Field(False, description="Whether domain registration is very fresh (<30 days)")
    virustotal_malicious_count: int = Field(0, description="Number of security vendors flagging URL as malicious")
    is_blacklisted_domain: bool = Field(False, description="Flagged by Safe Browsing or VT")
    upi_vpa_suspicious: bool = Field(False, description="VPA mismatches claimed corporate entity")
    upi_vpa_reasons: List[str] = Field(default_factory=list, description="Reasons for VPA flags")
    redirect_chains: List[str] = Field(default_factory=list, description="Terminal URLs after resolving shorteners")

class CoercionAnalysis(BaseModel):
    coercion_score: int = Field(0, description="Urgency / Psychological coercion score 0-100")
    tactics_detected: List[str] = Field(default_factory=list, description="Tactics like arrest threat, time limit, isolation")
    sentiment: Optional[str] = Field(None, description="Detected emotional tone of speaker/text")

class RiskVerdict(BaseModel):
    risk_score: int = Field(ge=0, le=100, description="Overall threat score (0=Safe, 100=Extreme Danger)")
    severity: str = Field(description="SAFE, CAUTION, or DANGER")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence in diagnosis")
    scam_archetype: ScamArchetype = Field(default=ScamArchetype.UNKNOWN_SUSPICIOUS)
    reasoning: List[str] = Field(default_factory=list, description="Step-by-step evidence justification")
    actionable_advisory: str = Field(description="Layman plain-language instructions on what to do")
    safety_checklist: List[str] = Field(default_factory=list, description="Immediate protective steps to take")
    evidence_sha256_hash: Optional[str] = Field(None, description="Cryptographic SHA-256 seal for Section 65B legal evidence")
    verification_url: Optional[str] = Field(None, description="Public verification endpoint URL for authorities")
    section_65b_certified: bool = Field(True, description="Certified under Section 65B Indian Evidence Act / BSA 2023")

class AgentStep(BaseModel):
    step_id: str
    agent_name: str
    status: str = Field(description="pending, running, completed, or failed")
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    session_id: str
    verdict: RiskVerdict
    evidence: ForensicEvidence
    threat_intel: ThreatIntelligence
    coercion: Optional[CoercionAnalysis] = None
    report_pdf_url: Optional[str] = None
    audio_advisory_url: Optional[str] = None
    steps: List[AgentStep] = Field(default_factory=list)
