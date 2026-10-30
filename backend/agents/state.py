"""
State definitions for CyberGuard AI LangGraph workflow.
Maintains state across vision, audio, threat intelligence, and redress nodes.
"""
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict

from models.schemas import (
    ForensicEvidence,
    ThreatIntelligence,
    CoercionAnalysis,
    RiskVerdict,
    AgentStep
)

class AgentState(TypedDict):
    # Session identifiers
    session_id: str
    user_language: str
    
    # Raw Multi-Modal Inputs
    image_bytes: Optional[bytes]
    audio_bytes: Optional[bytes]
    audio_filename: Optional[str]
    raw_text_input: Optional[str]
    
    # Processing Intermediate Outputs
    evidence: ForensicEvidence
    threat_intel: ThreatIntelligence
    coercion: Optional[CoercionAnalysis]
    
    # Final Verdict & Artifacts
    verdict: Optional[RiskVerdict]
    report_pdf_url: Optional[str]
    audio_advisory_url: Optional[str]
    
    # Real-Time Execution Trace
    steps: List[AgentStep]

