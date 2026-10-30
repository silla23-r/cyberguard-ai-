"use client";

import React from "react";
import { ShieldAlert, Globe, PhoneCall } from "lucide-react";
import { LANGUAGES } from "@/lib/constants";

interface HeaderProps {
  currentLang: string;
  onLangChange: (lang: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentLang, onLangChange }) => {
  return (
    <header className="border-b border-guard-700 bg-guard-800/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              CyberGuard <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">AI</span>
            </h1>
            <p className="text-xs text-slate-400">Multimodal Fraud & Scam Defense</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-guard-700/60 px-3 py-1.5 rounded-lg border border-guard-600">
            <Globe className="w-4 h-4 text-slate-400" />
            <select
              value={currentLang}
              onChange={(e) => onLangChange(e.target.value)}
              className="bg-transparent text-sm text-slate-200 outline-none cursor-pointer"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} className="bg-guard-800">
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <a
            href="tel:1930"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 text-sm font-semibold transition"
          >
            <PhoneCall className="w-4 h-4" />
            <span>1930 Helpline</span>
          </a>
        </div>
      </div>
    </header>
  );
};

