"use client";

import React from "react";
import { ListChecks } from "lucide-react";
import { ForensicEvidence, RiskVerdict } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface EvidencePanelProps {
  verdict: RiskVerdict;
  evidence: ForensicEvidence;
  currentLang?: string;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ verdict, evidence, currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <div className="bg-white rounded-xl border border-zinc-200 p-5 sm:p-6 space-y-4">
      <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
        <ListChecks className="w-4 h-4 text-zinc-500" />
        <span>{t.evidence.evidenceHeading}</span>
      </h4>

      <ul className="space-y-2.5 text-sm text-zinc-700 leading-relaxed">
        {verdict.reasoning.length === 0 ? (
          <li className="text-zinc-500 italic">{t.evidence.noEvidence}</li>
        ) : (
          verdict.reasoning.map((r, idx) => (
            <li key={idx} className="flex items-start gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 mt-2 shrink-0" />
              <span>{r}</span>
            </li>
          ))
        )}
      </ul>

      {(evidence.impersonated_brand ||
        evidence.extracted_urls.length > 0 ||
        evidence.upi_vpas.length > 0 ||
        evidence.qr_payload ||
        evidence.apk_analysis ||
        (evidence.remote_access_tools_detected && evidence.remote_access_tools_detected.length > 0) ||
        (evidence.pii_redacted_count && evidence.pii_redacted_count > 0) ||
        evidence.adversarial_injection_detected) && (
        <div className="border-t border-zinc-100 pt-4 space-y-2.5">
          <p className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">
            {t.evidence.flags}
          </p>
          <div className="flex flex-wrap gap-1.5 text-xs">
            {evidence.impersonated_brand && (
              <span className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono">
                {t.evidence.detectedBrand}: {evidence.impersonated_brand}
              </span>
            )}
            {evidence.remote_access_tools_detected?.map((tool, i) => (
              <span key={`rat-${i}`} className="px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-900 font-mono">
                Remote Tool: {tool}
              </span>
            ))}
            {evidence.apk_analysis?.package_name && (
              <span className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono">
                PKG: {evidence.apk_analysis.package_name}
              </span>
            )}
            {evidence.apk_analysis?.dangerous_permissions?.map((perm, i) => (
              <span key={`perm-${i}`} className="px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-900 font-mono">
                PERM: {perm}
              </span>
            ))}
            {evidence.apk_analysis?.sha256_hash && (
              <span className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-700 font-mono">
                APK SHA256: {evidence.apk_analysis.sha256_hash.slice(0, 14)}...
              </span>
            )}
            {evidence.extracted_urls.map((u, i) => (
              <span key={i} className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono break-all">
                {t.evidence.urlAnalysis}: {u}
              </span>
            ))}
            {evidence.upi_vpas.map((v, i) => (
              <span key={i} className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono">
                {t.evidence.upiAnalysis}: {v}
              </span>
            ))}
            {evidence.qr_payload && (
              <span className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono">
                QR Code Payload Embedded
              </span>
            )}
            {evidence.pii_redacted_count && evidence.pii_redacted_count > 0 ? (
              <span className="px-2.5 py-1 rounded-md bg-zinc-100 border border-zinc-200 text-zinc-800 font-mono">
                DPDP Shield: {evidence.pii_redacted_count} PII Masked
              </span>
            ) : null}
            {evidence.adversarial_injection_detected && (
              <span className="px-2.5 py-1 rounded-md bg-red-50 border border-red-200 text-red-900 font-mono">
                Prompt Injection Blocked
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
