export type Severity = "SAFE" | "CAUTION" | "DANGER";

export interface ApkInspectionResult {
  is_valid_apk: boolean;
  filename?: string | null;
  package_name?: string | null;
  sha256_hash?: string | null;
  file_size_bytes: number;
  dangerous_permissions: string[];
  sms_interception_risk: boolean;
  accessibility_abuse_risk: boolean;
  sideload_dropper_risk: boolean;
  targeted_banking_apps: string[];
  embedded_urls: string[];
  risk_flags: string[];
}

export interface ForensicEvidence {
  extracted_urls: string[];
  qr_payload?: string | null;
  qr_parsed?: Record<string, unknown> | null;
  impersonated_brand?: string | null;
  phone_numbers: string[];
  upi_vpas: string[];
  urgency_signals: string[];
  raw_text?: string | null;
  apk_analysis?: ApkInspectionResult | null;
  remote_access_tools_detected?: string[];
  pii_redacted_count?: number;
  adversarial_injection_detected?: boolean;
}

export interface ThreatIntelligence {
  domain_age_days?: number | null;
  domain_registrar?: string | null;
  is_domain_suspicious: boolean;
  virustotal_malicious_count: number;
  is_blacklisted_domain: boolean;
  upi_vpa_suspicious: boolean;
  upi_vpa_reasons: string[];
  redirect_chains: string[];
}

export interface CoercionAnalysis {
  coercion_score: number;
  tactics_detected: string[];
  sentiment?: string | null;
}

export interface RiskVerdict {
  risk_score: number;
  severity: Severity;
  confidence: number;
  scam_archetype: string;
  reasoning: string[];
  actionable_advisory: string;
  safety_checklist: string[];
}

export interface AgentStep {
  step_id: string;
  agent_name: string;
  status: "pending" | "running" | "completed" | "failed";
  message: string;
  timestamp: string;
  details?: Record<string, unknown> | null;
}

export type UploadModality = "image" | "audio" | "apk" | "text" | "whatsapp" | "multimodal";

export interface UploadMetadata {
  inputType: UploadModality;
  inputLabel: string;
  fileSizeBytes?: number;
  previewThumbnail?: string | null;
}

export interface UploadHistoryItem {
  id: string;
  uploadedAt: string;
  inputType: UploadModality;
  inputLabel: string;
  fileSizeBytes?: number;
  previewThumbnail?: string | null;
  result: AnalysisResponse;
}

export interface AnalysisResponse {
  session_id: string;
  verdict: RiskVerdict;
  evidence: ForensicEvidence;
  threat_intel: ThreatIntelligence;
  coercion?: CoercionAnalysis | null;
  report_pdf_url?: string | null;
  audio_advisory_url?: string | null;
  steps: AgentStep[];
}
