"use client";

import React from "react";
import { Sparkles, Image as ImageIcon, QrCode, Mic } from "lucide-react";
import { getTranslation } from "@/lib/translations";

interface HeroSectionProps {
  currentLang?: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <section className="text-center space-y-4 pt-4">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
        <Sparkles className="w-3.5 h-3.5" />
        <span>{t.hero.badge}</span>
      </div>
      <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
        {t.hero.title1}
        <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
          {t.hero.titleHighlight}
        </span>
        {t.hero.title2}
      </h2>
      <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
        {t.hero.desc}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs text-slate-300">
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <ImageIcon className="w-3.5 h-3.5 text-blue-400" />
          <span>{t.hero.badgeOcr}</span>
        </span>
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <QrCode className="w-3.5 h-3.5 text-green-400" />
          <span>{t.hero.badgeQr}</span>
        </span>
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <Mic className="w-3.5 h-3.5 text-purple-400" />
          <span>{t.hero.badgeAudio}</span>
        </span>
      </div>
    </section>
  );
};
