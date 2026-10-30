"use client";

import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-guard-700 bg-guard-800 py-6 text-center text-xs text-slate-500">
      <div className="max-w-4xl mx-auto px-4 space-y-1">
        <p>CyberGuard AI is an autonomous multimodal cyber-defense agent designed for public digital safety.</p>
        <p>Complies with National Cyber Crime Reporting Portal standards (1930 / cybercrime.gov.in).</p>
      </div>
    </footer>
  );
};

