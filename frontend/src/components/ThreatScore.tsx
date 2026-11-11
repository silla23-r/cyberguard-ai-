"use client";

import React from "react";
import { FileDown, Volume2 } from "lucide-react";
import { RiskVerdict } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface ThreatScoreProps {
  verdict: RiskVerdict;
  reportPdfUrl?: string | null;
  audioAdvisoryUrl?: string | null;
  currentLang?: string;
}

export const ThreatScore: React.FC<ThreatScoreProps> = ({
  verdict,
  reportPdfUrl,
  audioAdvisoryUrl,
  currentLang = "en",
}) => {
  const t = getTranslation(currentLang);
  const isDanger = verdict.severity === "DANGER";
  const isCaution = verdict.severity === "CAUTION";

  const getScoreBoxStyle = () => {
    if (isDanger) return "border-red-200 bg-red-50 text-red-900";
    if (isCaution) return "border-amber-200 bg-amber-50 text-amber-900";
    return "border-emerald-200 bg-emerald-50 text-emerald-900";
  };

  const getBadgeStyle = () => {
    if (isDanger) return "bg-red-50 text-red-800 border border-red-200";
    if (isCaution) return "bg-amber-50 text-amber-800 border border-amber-200";
    return "bg-emerald-50 text-emerald-800 border border-emerald-200";
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl p-5 sm:p-6 border border-zinc-200 bg-white flex flex-col sm:flex-row sm:items-center gap-5 justify-between">
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div
            className={`w-24 h-24 rounded-lg flex flex-col items-center justify-center text-center border shrink-0 ${getScoreBoxStyle()}`}
          >
            <span className="text-3xl font-semibold tabular-nums leading-none">
              {verdict.risk_score}
            </span>
            <span className="text-[11px] font-medium uppercase tracking-wider mt-1.5 opacity-80">
              {t.threat.riskScoreLabel}
            </span>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className={`text-[11px] px-2 py-0.5 rounded font-semibold uppercase tracking-wide ${getBadgeStyle()}`}>
                {verdict.severity}
              </span>
              <span className="text-xs text-zinc-500 font-mono tabular-nums">
                Confidence {Math.round(verdict.confidence * 100)}%
              </span>
            </div>
            <h3 className="text-xl font-semibold text-zinc-900 tracking-tight">
              {verdict.scam_archetype.replace(/_/g, " ")}
            </h3>
            <p className="text-sm text-zinc-600 max-w-xl leading-relaxed">
              {verdict.actionable_advisory}
            </p>
          </div>
        </div>

        {reportPdfUrl && (
          <a
            href={reportPdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white font-medium text-xs sm:text-sm flex items-center justify-center gap-2 transition shrink-0"
          >
            <FileDown className="w-4 h-4" />
            <span>{t.threat.downloadReport}</span>
          </a>
        )}
      </div>

      {audioAdvisoryUrl && (
        <div className="bg-white border border-zinc-200 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-zinc-100 border border-zinc-200 flex items-center justify-center text-zinc-700 shrink-0">
            <Volume2 className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-zinc-700">{t.threat.listenAdvisory}</p>
            <audio controls src={audioAdvisoryUrl} className="w-full mt-2 h-9 outline-none" />
          </div>
        </div>
      )}
    </div>
  );
};
