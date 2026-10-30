"use client";

import React from "react";
import { Sparkles, Image as ImageIcon, QrCode, Mic } from "lucide-react";

export const HeroSection: React.FC = () => {
  return (
    <section className="text-center space-y-4 pt-4">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Protecting Citizens Against Financial Extortion</span>
      </div>
      <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
        Never Fall for a{" "}
        <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
          Digital Arrest or UPI Scam
        </span>{" "}
        Again.
      </h2>
      <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
        Upload a suspicious screenshot, scan a payment QR code, or upload a threatening call recording.
        Our multi-agent AI verifies registries in real time and compiles an official cybercrime report.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3 pt-2 text-xs text-slate-300">
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <ImageIcon className="w-3.5 h-3.5 text-blue-400" />
          <span>Screenshot OCR</span>
        </span>
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <QrCode className="w-3.5 h-3.5 text-green-400" />
          <span>UPI Collect QR Decoder</span>
        </span>
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-guard-800 border border-guard-700">
          <Mic className="w-3.5 h-3.5 text-purple-400" />
          <span>Call Threat Acoustic Analysis</span>
        </span>
      </div>
    </section>
  );
};

