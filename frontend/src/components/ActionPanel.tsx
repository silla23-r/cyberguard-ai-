"use client";

import React from "react";
import { ShieldCheck, CheckSquare, AlertOctagon } from "lucide-react";
import { RiskVerdict } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface ActionPanelProps {
  verdict: RiskVerdict;
  currentLang?: string;
}

export const ActionPanel: React.FC<ActionPanelProps> = ({ verdict, currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <div className="bg-guard-800 rounded-2xl border border-guard-700 p-6 space-y-4">
      <h4 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-green-400" />
        <span>{t.actions.actionsHeading}</span>
      </h4>

      <ul className="space-y-2 text-sm text-slate-300">
        {verdict.safety_checklist.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2 text-slate-300">
            <CheckSquare className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <span>{item}</span>
          </li>
        ))}
      </ul>

      {/* Emergency Helplines */}
      <div className="mt-4 p-4 rounded-xl bg-guard-900 border border-guard-700 space-y-2">
        <p className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
          <AlertOctagon className="w-4 h-4" />
          <span>{t.actions.emergencyHeading}</span>
        </p>
        <p className="text-xs text-slate-400">{t.actions.emergencySub}</p>
        <div className="flex items-center justify-between text-xs font-semibold pt-1">
          <span>National Cyber Crime:</span>
          <a href="tel:1930" className="text-red-400 font-bold hover:underline">
            {t.actions.dialHelpline}
          </a>
        </div>
        <div className="flex items-center justify-between text-xs font-semibold">
          <span>National Portal:</span>
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:underline"
          >
            {t.actions.nationalPortal}
          </a>
        </div>
      </div>
    </div>
  );
};
