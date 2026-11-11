"use client";

import React from "react";
import { getTranslation } from "@/lib/translations";

interface HeroSectionProps {
  currentLang?: string;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ currentLang = "en" }) => {
  const t = getTranslation(currentLang);

  return (
    <section className="space-y-2.5 pt-2">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {t.hero.badge}
      </p>
      <h2 className="text-2xl sm:text-3xl font-semibold text-zinc-900 tracking-tight leading-snug">
        {t.hero.title1}
        <span className="underline decoration-zinc-300 underline-offset-4">
          {t.hero.titleHighlight}
        </span>
        {t.hero.title2}
      </h2>
      <p className="text-zinc-600 max-w-2xl text-sm sm:text-base leading-relaxed">
        {t.hero.desc}
      </p>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 pt-1 text-xs text-zinc-500">
        <span>{t.hero.badgeOcr}</span>
        <span aria-hidden="true" className="text-zinc-300">/</span>
        <span>{t.hero.badgeQr}</span>
        <span aria-hidden="true" className="text-zinc-300">/</span>
        <span>{t.hero.badgeAudio}</span>
      </div>
    </section>
  );
};
