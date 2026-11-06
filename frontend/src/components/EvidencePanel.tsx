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
    <div className="bg-guard-800 rounded-2xl border border-guard-700 p-6 space-y-4">
      <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
        <ListChecks className="w-4 h-4 text-blue-400" />
        <span>{t.evidence.evidenceHeading}</span>
      </h4>

      <ul className="space-y-2 text-sm text-slate-300">
        {verdict.reasoning.length === 0 ? (
          <li className="text-slate-400 italic">{t.evidence.noEvidence}</li>
        ) : (
          verdict.reasoning.map((r, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span>{r}</span>
            </li>
          ))
        )}
      </ul>

      <div className="border-t border-guard-700 pt-4 mt-4 space-y-2">
        <p className="text-xs font-semibold text-slate-400 uppercase">{t.evidence.flags}</p>
        <div className="flex flex-wrap gap-2 text-xs">
          {evidence.impersonated_brand && (
            <span className="px-2 py-1 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300">
              {t.evidence.detectedBrand}: {evidence.impersonated_brand}
            </span>
          )}
          {evidence.extracted_urls.map((u, i) => (
            <span key={i} className="px-2 py-1 rounded bg-blue-500/10 border border-blue-500/30 text-blue-300">
              {t.evidence.urlAnalysis}: {u}
            </span>
          ))}
          {evidence.upi_vpas.map((v, i) => (
            <span key={i} className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300">
              {t.evidence.upiAnalysis}: {v}
            </span>
          ))}
          {evidence.qr_payload && (
            <span className="px-2 py-1 rounded bg-red-500/10 border border-red-500/30 text-red-300">
              QR Code Payload Embedded
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
