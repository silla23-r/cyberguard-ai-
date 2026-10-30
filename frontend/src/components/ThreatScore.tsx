"use client";

import React from "react";
import { FileDown, Volume2 } from "lucide-react";
import { RiskVerdict } from "@/lib/types";

interface ThreatScoreProps {
  verdict: RiskVerdict;
  reportPdfUrl?: string | null;
  audioAdvisoryUrl?: string | null;
}

export const ThreatScore: React.FC<ThreatScoreProps> = ({
  verdict,
  reportPdfUrl,
  audioAdvisoryUrl,
}) => {
  const isDanger = verdict.severity === "DANGER";
  const isCaution = verdict.severity === "CAUTION";

  const getBorderColor = () => {
    if (isDanger) return "border-red-500/40 bg-red-500/10 text-red-400";
    if (isCaution) return "border-yellow-500/40 bg-yellow-500/10 text-yellow-400";
    return "border-green-500/40 bg-green-500/10 text-green-400";
  };

  const getBadgeColor = () => {
    if (isDanger) return "bg-red-500/20 text-red-400 border border-red-500/30";
    if (isCaution) return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
    return "bg-green-500/20 text-green-400 border border-green-500/30";
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl p-6 sm:p-8 border shadow-2xl flex flex-col sm:flex-row items-center gap-6 justify-between bg-guard-800 border-guard-700">
        <div className="flex items-center gap-5">
          <div
            className={`w-24 h-24 rounded-full flex flex-col items-center justify-center text-center font-black border-4 shadow-inner ${getBorderColor()}`}
          >
            <span className="text-3xl leading-none">{verdict.risk_score}</span>
            <span className="text-[10px] text-slate-300 uppercase tracking-widest mt-1">
              Risk Score
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${getBadgeColor()}`}>
                {verdict.severity}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Confidence: {Math.round(verdict.confidence * 100)}%
              </span>
            </div>
            <h3 className="text-2xl font-extrabold text-white">
              {verdict.scam_archetype.replace(/_/g, " ")}
            </h3>
            <p className="text-sm text-slate-300 max-w-xl">{verdict.actionable_advisory}</p>
          </div>
        </div>

        {reportPdfUrl && (
          <a
            href={reportPdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20 transition shrink-0"
          >
            <FileDown className="w-4 h-4" />
            <span>Download 1930 PDF</span>
          </a>
        )}
      </div>

      {audioAdvisoryUrl && (
        <div className="bg-guard-800 border border-guard-700 rounded-xl p-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
            <Volume2 className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-semibold text-slate-300">Spoken Voice Advisory (Regional Language)</p>
            <audio controls src={audioAdvisoryUrl} className="w-full mt-2 h-9 outline-none" />
          </div>
        </div>
      )}
    </div>
  );
};

