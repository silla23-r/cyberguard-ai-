"use client";

import React from "react";
import { getTranslation } from "@/lib/translations";

interface FooterProps {
  currentLang?: string;
}

export const Footer: React.FC<FooterProps> = ({ currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <footer className="border-t border-zinc-200 bg-white py-6 text-xs text-zinc-500">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-center sm:text-left">
        <p>{t.footer.desc}</p>
        <p className="text-zinc-400 shrink-0">{t.footer.legal}</p>
      </div>
    </footer>
  );
};
