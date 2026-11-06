"use client";

import React from "react";
import { getTranslation } from "@/lib/translations";

interface FooterProps {
  currentLang?: string;
}

export const Footer: React.FC<FooterProps> = ({ currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <footer className="border-t border-guard-700 bg-guard-800 py-6 text-center text-xs text-slate-500">
      <div className="max-w-4xl mx-auto px-4 space-y-1">
        <p>{t.footer.desc}</p>
        <p>{t.footer.legal}</p>
      </div>
    </footer>
  );
};
