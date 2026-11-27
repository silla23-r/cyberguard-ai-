"use client";

import React from "react";
import { Shield, Globe, PhoneCall, Bell } from "lucide-react";
import { LANGUAGES } from "@/lib/constants";
import { getTranslation } from "@/lib/translations";

interface HeaderProps {
  currentLang: string;
  onLangChange: (lang: string) => void;
  guardianPaired?: boolean;
  onOpenGuardian?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLang,
  onLangChange,
  guardianPaired = false,
  onOpenGuardian,
}) => {
  const t = getTranslation(currentLang);

  return (
    <header className="border-b border-zinc-200 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-lg bg-zinc-900 flex items-center justify-center shrink-0">
            <Shield className="w-4 h-4 text-white stroke-[2]" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-zinc-900 truncate">
                CyberGuard
              </h1>
              <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-600 border border-zinc-200">
                AI
              </span>
            </div>
            <p className="text-xs text-zinc-500 truncate hidden sm:block">
              {t.header.subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {onOpenGuardian && (
            <button
              type="button"
              onClick={onOpenGuardian}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-white border border-zinc-200 hover:border-zinc-400 hover:bg-zinc-50 text-zinc-800 text-xs font-medium transition cursor-pointer"
            >
              <Bell className="w-3.5 h-3.5 text-zinc-700" />
              <span className="hidden xs:inline sm:inline">Guardian</span>
              {guardianPaired && (
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" title="Guardian Protection Active" />
              )}
            </button>
          )}

          <div className="flex items-center gap-1.5 bg-white px-2.5 py-1.5 rounded-md border border-zinc-200 hover:border-zinc-300 transition">
            <Globe className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
            <select
              value={currentLang}
              onChange={(e) => onLangChange(e.target.value)}
              aria-label="Language"
              className="bg-transparent text-xs sm:text-sm text-zinc-700 font-medium outline-none cursor-pointer"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} className="bg-white text-zinc-900">
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <a
            href="tel:1930"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50 text-zinc-800 text-xs font-medium transition"
          >
            <PhoneCall className="w-3.5 h-3.5 text-red-700" />
            <span>{t.header.helpline}</span>
          </a>
        </div>
      </div>
    </header>
  );
};
