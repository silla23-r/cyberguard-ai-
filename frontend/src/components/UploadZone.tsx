"use client";

import React, { useState, useRef } from "react";
import { Image as ImageIcon, Mic, FileText, UploadCloud, FileCheck, Scan, Loader2, MessageCircle, Send, ShieldAlert, ShieldCheck, UserX } from "lucide-react";
import { simulateWhatsAppMessage, blockWhatsAppFraudster } from "@/lib/api";
import { AnalysisResponse } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface UploadZoneProps {
  onAnalyze: (formData: FormData) => void;
  isLoading: boolean;
  selectedLang: string;
  onAnalysisResult?: (data: AnalysisResponse) => void;
}

const WA_PRESETS = {
  kyc: "URGENT: Your SBI YONO Account will be blocked today due to pending KYC verification. Please click here immediately to update PAN card: http://sbi-kyc-verify-portal.in/login or call officer at +919876543210",
  electricity: "Dear Consumer, Electricity power will be disconnected tonight at 9:30 PM from electricity office because your previous month bill was not updated. Please immediately contact our officer at +919876543210 or pay to bescom@okaxis",
  arrest: "CBI OFFICER R.K. SHARMA: A parcel sent to Cambodia under your Aadhaar number contains 5 fake passports and 150 grams of MDMA. Supreme Court has issued an arrest warrant. Do not disconnect this video call or local police will reach your house in 15 minutes."
};

export const UploadZone: React.FC<UploadZoneProps> = ({ onAnalyze, isLoading, selectedLang, onAnalysisResult }) => {
  const t = getTranslation(selectedLang);
  const [activeTab, setActiveTab] = useState<"image" | "audio" | "text" | "whatsapp">("image");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState("");

  // WhatsApp Simulator State
  const [waInput, setWaInput] = useState("");
  const [waSending, setWaSending] = useState(false);
  const [waChat, setWaChat] = useState<{ userText: string; botReply: string; isDanger: boolean } | null>(null);
  const [isBlocked, setIsBlocked] = useState(false);
  const [blocking, setBlocking] = useState(false);

  const handleBlockFraudster = async () => {
    if (!waChat) return;
    setBlocking(true);
    try {
      await blockWhatsAppFraudster("whatsapp:+919876543210", waChat.userText);
      setIsBlocked(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Block action error: " + msg);
    } finally {
      setBlocking(false);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (!imageFile && !audioFile && !textInput.trim()) {
      alert("Please upload a screenshot, select an audio file, or paste a message.");
      return;
    }

    const formData = new FormData();
    if (imageFile) formData.append("image", imageFile);
    if (audioFile) formData.append("audio", audioFile);
    if (textInput.trim()) formData.append("text", textInput.trim());
    formData.append("language", selectedLang);

    onAnalyze(formData);
  };

  const handleWhatsAppSend = async () => {
    if (!waInput.trim()) {
      alert("Please enter or select a message to forward to the WhatsApp bot.");
      return;
    }

    setIsBlocked(false);
    setWaSending(true);
    try {
      const res = await simulateWhatsAppMessage(waInput.trim(), selectedLang);
      const isDanger = (res.verdict?.risk_score || 0) >= 40 || res.verdict?.severity === "DANGER";
      setWaChat({
        userText: waInput.trim(),
        botReply: res.whatsapp_rendered_reply || "Threat analysis completed.",
        isDanger,
      });

      if (onAnalysisResult && res.verdict) {
        onAnalysisResult({
          session_id: "WA-" + Date.now().toString(36).toUpperCase(),
          verdict: res.verdict,
          evidence: res.evidence || { extracted_urls: [], upi_vpas: [], phone_numbers: [], urgency_signals: [] },
          threat_intel: {
            is_domain_suspicious: false,
            virustotal_malicious_count: 0,
            is_blacklisted_domain: false,
            upi_vpa_suspicious: false,
            upi_vpa_reasons: [],
            redirect_chains: []
          },
          coercion: undefined,
          report_pdf_url: res.report_pdf_url,
          audio_advisory_url: res.audio_advisory_url,
          steps: res.steps || [],
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("WhatsApp bot error: " + msg);
    } finally {
      setWaSending(false);
    }
  };

  return (
    <section className="bg-guard-800 rounded-2xl border border-guard-700 shadow-xl p-6 sm:p-8 space-y-6">
      {/* Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 p-1.5 bg-guard-900 rounded-xl border border-guard-700">
        <button
          onClick={() => setActiveTab("image")}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition ${
            activeTab === "image" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <ImageIcon className="w-4 h-4" />
          <span>{t.upload.tabImage}</span>
        </button>
        <button
          onClick={() => setActiveTab("audio")}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition ${
            activeTab === "audio" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>{t.upload.tabAudio}</span>
        </button>
        <button
          onClick={() => setActiveTab("text")}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition ${
            activeTab === "text" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>{t.upload.tabText}</span>
        </button>
        <button
          onClick={() => setActiveTab("whatsapp")}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition border ${
            activeTab === "whatsapp"
              ? "bg-emerald-600 text-white shadow border-emerald-400"
              : "text-emerald-400 border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20"
          }`}
        >
          <MessageCircle className="w-4 h-4 text-emerald-400" />
          <span>{t.upload.tabWhatsapp}</span>
        </button>
      </div>

      {/* Tab 1: Image / QR */}
      {activeTab === "image" && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-guard-600 hover:border-blue-500 rounded-xl p-8 text-center cursor-pointer transition bg-guard-900/50 hover:bg-guard-900/80"
        >
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            className="hidden"
            onChange={(e) => setImageFile(e.target.files?.[0] || null)}
          />
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <UploadCloud className="w-7 h-7" />
            </div>
            <div>
              <p className="font-semibold text-slate-200">{t.upload.dropImagePrompt}</p>
              <p className="text-xs text-slate-400 mt-1">{t.upload.dropImageHint}</p>
            </div>
            {imageFile && (
              <div className="mt-3 p-2 bg-guard-800 rounded-lg border border-guard-600 text-xs text-blue-300 font-mono flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-green-400" />
                <span>{imageFile.name}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Audio */}
      {activeTab === "audio" && (
        <div
          onClick={() => audioInputRef.current?.click()}
          className="border-2 border-dashed border-guard-600 hover:border-purple-500 rounded-xl p-8 text-center cursor-pointer transition bg-guard-900/50 hover:bg-guard-900/80"
        >
          <input
            type="file"
            ref={audioInputRef}
            accept="audio/*"
            className="hidden"
            onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
          />
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Mic className="w-7 h-7" />
            </div>
            <div>
              <p className="font-semibold text-slate-200">{t.upload.dropAudioPrompt}</p>
              <p className="text-xs text-slate-400 mt-1">{t.upload.dropAudioHint}</p>
            </div>
            {audioFile && (
              <div className="mt-3 p-2 bg-guard-800 rounded-lg border border-guard-600 text-xs text-purple-300 font-mono flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-green-400" />
                <span>{audioFile.name}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Text */}
      {activeTab === "text" && (
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{t.upload.tabText}</label>
          <textarea
            rows={4}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={t.upload.pastePlaceholder}
            className="w-full bg-guard-900 border border-guard-600 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
          />
        </div>
      )}

      {/* Tab 4: WhatsApp Bot Simulator */}
      {activeTab === "whatsapp" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                <MessageCircle className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-white">{t.upload.waTitle}</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                </div>
                <p className="text-[11px] text-emerald-300/80">{t.upload.waSubtitle}</p>
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-mono hidden sm:inline-block">
              Webhook: /api/whatsapp/webhook
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">{t.upload.waPresetsLabel}</span>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.kyc)}
              className="text-xs px-2.5 py-1 rounded-full bg-guard-700 hover:bg-emerald-600/30 border border-guard-600 hover:border-emerald-500 text-slate-200 transition"
            >
              🏦 {t.upload.waPresetKyc}
            </button>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.electricity)}
              className="text-xs px-2.5 py-1 rounded-full bg-guard-700 hover:bg-emerald-600/30 border border-guard-600 hover:border-emerald-500 text-slate-200 transition"
            >
              ⚡ {t.upload.waPresetElectricity}
            </button>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.arrest)}
              className="text-xs px-2.5 py-1 rounded-full bg-guard-700 hover:bg-emerald-600/30 border border-guard-600 hover:border-emerald-500 text-slate-200 transition"
            >
              🚨 {t.upload.waPresetArrest}
            </button>
          </div>

          <div className="space-y-3">
            <textarea
              rows={3}
              value={waInput}
              onChange={(e) => setWaInput(e.target.value)}
              placeholder={t.upload.waPlaceholder}
              className="w-full bg-guard-900 border border-guard-600 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
            />
            <button
              type="button"
              onClick={handleWhatsAppSend}
              disabled={waSending}
              className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2 transition duration-200 cursor-pointer disabled:opacity-50"
            >
              {waSending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t.upload.waAnalyzingBtn}</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>{t.upload.waSendBtn}</span>
                </>
              )}
            </button>
          </div>

          {/* Simulated WhatsApp Chat Window */}
          {waChat && (
            <div className="rounded-xl bg-[#0b141a] border border-guard-700 p-4 space-y-4 max-h-[450px] overflow-y-auto">
              <div className="flex justify-center">
                <span className="text-[10px] text-slate-400 bg-guard-900 px-3 py-1 rounded-full border border-guard-700">
                  Today • End-to-End Encrypted Simulation
                </span>
              </div>

              {/* User Forwarded Message */}
              <div className="flex justify-end">
                <div className="max-w-[85%] sm:max-w-[70%] bg-[#005c4b] text-[#e9edef] p-3 rounded-2xl rounded-tr-sm shadow text-xs sm:text-sm">
                  <p className="whitespace-pre-wrap">{waChat.userText}</p>
                  <div className="text-[10px] text-emerald-200/70 text-right mt-1">✓✓ Forwarded</div>
                </div>
              </div>

              {/* Bot Reply */}
              <div className="flex justify-start">
                <div className="max-w-[95%] sm:max-w-[85%] bg-[#202c33] text-[#d1d7db] p-3.5 rounded-2xl rounded-tl-sm border border-emerald-500/30 shadow text-xs sm:text-sm">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs pb-1.5 border-b border-guard-700 mb-2">
                    <MessageCircle className="w-3.5 h-3.5" />
                    <span>CyberGuard AI Official Defender</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">Verified Bot</span>
                  </div>
                  <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-slate-200">
                    {waChat.botReply}
                  </pre>
                </div>
              </div>

              {/* 1-Tap Block Fraudster Action if High Risk */}
              {waChat.isDanger && !isBlocked && (
                <div className="p-3.5 bg-red-950/60 border border-red-500/50 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg shadow-red-950/50">
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 animate-pulse" />
                    <div>
                      <p className="text-xs font-bold text-red-300">{t.upload.waDangerBadge}</p>
                      <p className="text-[11px] text-red-200/80">Break scammer psychological pressure loop & freeze contact</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleBlockFraudster}
                    disabled={blocking}
                    className="w-full sm:w-auto px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-red-600/30 transition shrink-0 cursor-pointer disabled:opacity-50"
                  >
                    {blocking ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>{t.upload.waBlockingBtn}</span>
                      </>
                    ) : (
                      <>
                        <UserX className="w-3.5 h-3.5" />
                        <span>{t.upload.waBlockBtn}</span>
                      </>
                    )}
                  </button>
                </div>
              )}

              {isBlocked && (
                <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/50 rounded-xl flex items-center gap-2.5 text-xs text-emerald-300 font-semibold shadow-lg shadow-emerald-950/50">
                  <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
                  <span>{t.upload.waBlockedBadge}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Button for non-whatsapp tabs */}
      {activeTab !== "whatsapp" && (
        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full py-4 px-6 rounded-xl font-bold text-base bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition duration-200 cursor-pointer disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>{t.upload.scanningButton}</span>
            </>
          ) : (
            <>
              <Scan className="w-5 h-5" />
              <span>{t.upload.scanButton}</span>
            </>
          )}
        </button>
      )}
    </section>
  );
};

