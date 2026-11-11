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
    <div className="bg-white rounded-xl border border-zinc-200 p-5 sm:p-6 space-y-4">
      <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-zinc-500" />
        <span>{t.actions.actionsHeading}</span>
      </h4>

      <ul className="space-y-2.5 text-sm text-zinc-700 leading-relaxed">
        {verdict.safety_checklist.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2.5">
            <CheckSquare className="w-4 h-4 text-zinc-500 shrink-0 mt-0.5" />
            <span>{item}</span>
          </li>
        ))}
      </ul>

      {/* Emergency Helplines */}
      <div className="mt-4 p-4 rounded-lg bg-zinc-50 border border-zinc-200 space-y-2">
        <p className="text-xs font-semibold text-red-800 uppercase tracking-wider flex items-center gap-1.5">
          <AlertOctagon className="w-3.5 h-3.5 text-red-700" />
          <span>{t.actions.emergencyHeading}</span>
        </p>
        <p className="text-xs text-zinc-600">{t.actions.emergencySub}</p>
        <div className="flex items-center justify-between text-xs pt-1 border-t border-zinc-200/80">
          <span className="text-zinc-600 font-medium">National Cyber Crime:</span>
          <a href="tel:1930" className="text-red-700 font-semibold hover:underline">
            {t.actions.dialHelpline}
          </a>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-600 font-medium">National Portal:</span>
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-900 font-medium underline decoration-zinc-300 hover:decoration-zinc-900"
          >
            {t.actions.nationalPortal}
          </a>
        </div>
      </div>
    </div>
  );
};
