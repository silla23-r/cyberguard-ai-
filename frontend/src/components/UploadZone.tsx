"use client";

import React, { useState, useRef } from "react";
import { Image as ImageIcon, Mic, FileText, UploadCloud, FileCheck, Scan, Loader2, MessageCircle, Send, ShieldAlert, ShieldCheck, UserX, Package } from "lucide-react";
import { simulateWhatsAppMessage, blockWhatsAppFraudster } from "@/lib/api";
import { getOrCreateDeviceId } from "@/lib/guardianPush";
import { AnalysisResponse, UploadMetadata, UploadModality } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface UploadZoneProps {
  onAnalyze: (formData: FormData, meta: UploadMetadata) => void;
  isLoading: boolean;
  selectedLang: string;
  onAnalysisResult?: (data: AnalysisResponse, meta: UploadMetadata) => void;
}

async function createImageThumbnail(file: File): Promise<string | null> {
  try {
    const objectUrl = URL.createObjectURL(file);
    return await new Promise((resolve) => {
      const img = new window.Image();
      img.onload = () => {
        try {
          const maxDim = 112;
          const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
          const canvas = document.createElement("canvas");
          canvas.width = Math.max(1, Math.round(img.width * scale));
          canvas.height = Math.max(1, Math.round(img.height * scale));
          const ctx = canvas.getContext("2d");
          if (!ctx) {
            resolve(null);
            return;
          }
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          resolve(canvas.toDataURL("image/jpeg", 0.65));
        } catch {
          resolve(null);
        } finally {
          URL.revokeObjectURL(objectUrl);
        }
      };
      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        resolve(null);
      };
      img.src = objectUrl;
    });
  } catch {
    return null;
  }
}

const WA_PRESETS = {
  kyc: "URGENT: Your SBI YONO Account will be blocked today due to pending KYC verification. Please click here immediately to update PAN card: http://sbi-kyc-verify-portal.in/login or call officer at +919876543210",
  electricity: "Dear Consumer, Electricity power will be disconnected tonight at 9:30 PM from electricity office because your previous month bill was not updated. Please immediately contact our officer at +919876543210 or pay to bescom@okaxis",
  arrest: "CBI OFFICER R.K. SHARMA: A parcel sent to Cambodia under your Aadhaar number contains 5 fake passports and 150 grams of MDMA. Supreme Court has issued an arrest warrant. Do not disconnect this video call or local police will reach your house in 15 minutes.",
  apk: "TRAFFIC NOTICE: Pending e-Challan Rs. 2,000 against vehicle DL-09. Download and open RTO_eChallan_Pay.apk immediately and allow Install Unknown Apps, or share your AnyDesk code with inspector at +919876543210."
};

export const UploadZone: React.FC<UploadZoneProps> = ({ onAnalyze, isLoading, selectedLang, onAnalysisResult }) => {
  const t = getTranslation(selectedLang);
  const [activeTab, setActiveTab] = useState<"image" | "audio" | "apk" | "text" | "whatsapp">("image");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [apkFile, setApkFile] = useState<File | null>(null);
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
  const apkInputRef = useRef<HTMLInputElement>(null);
  const [loadingApkPreset, setLoadingApkPreset] = useState<string | null>(null);

  const handleSelectApkPreset = async (filename: string) => {
    setLoadingApkPreset(filename);
    try {
      const resp = await fetch(`/samples/${filename}`);
      if (!resp.ok) {
        throw new Error(`Could not load sample APK (${resp.status})`);
      }
      const blob = await resp.blob();
      const file = new File([blob], filename, {
        type: "application/vnd.android.package-archive",
      });
      setApkFile(file);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Sample APK load error: " + msg);
    } finally {
      setLoadingApkPreset(null);
    }
  };

  const handleSubmit = async () => {
    if (!imageFile && !audioFile && !apkFile && !textInput.trim()) {
      alert("Please upload a screenshot, audio file, APK file, or paste a message.");
      return;
    }

    const formData = new FormData();
    if (imageFile) formData.append("image", imageFile);
    if (audioFile) formData.append("audio", audioFile);
    if (apkFile) formData.append("apk_file", apkFile);
    if (textInput.trim()) formData.append("text", textInput.trim());
    formData.append("language", selectedLang);
    const deviceId = getOrCreateDeviceId();
    if (deviceId) formData.append("device_id", deviceId);

    const attachedNames: string[] = [];
    if (imageFile) attachedNames.push(imageFile.name);
    if (audioFile) attachedNames.push(audioFile.name);
    if (apkFile) attachedNames.push(apkFile.name);

    const modalCount =
      (imageFile ? 1 : 0) + (audioFile ? 1 : 0) + (apkFile ? 1 : 0) + (textInput.trim() ? 1 : 0);
    let inputType: UploadModality = "text";
    if (modalCount > 1) {
      inputType = "multimodal";
    } else if (apkFile) {
      inputType = "apk";
    } else if (imageFile) {
      inputType = "image";
    } else if (audioFile) {
      inputType = "audio";
    }

    const trimmedText = textInput.trim();
    const textSnippet = trimmedText.length > 72 ? trimmedText.slice(0, 72) + "..." : trimmedText;
    const inputLabel = attachedNames.length > 0 ? attachedNames.join(" + ") : textSnippet || "Submission";
    const totalBytes =
      (imageFile?.size || 0) + (audioFile?.size || 0) + (apkFile?.size || 0) || undefined;
    const previewThumbnail = imageFile ? await createImageThumbnail(imageFile) : null;

    onAnalyze(formData, {
      inputType,
      inputLabel,
      fileSizeBytes: totalBytes,
      previewThumbnail,
    });
  };

  const handleWhatsAppSend = async () => {
    if (!waInput.trim()) {
      alert("Please enter or select a message to forward to the WhatsApp bot.");
      return;
    }

    setIsBlocked(false);
    setWaSending(true);
    try {
      const res = await simulateWhatsAppMessage(
        waInput.trim(),
        selectedLang,
        getOrCreateDeviceId()
      );
      const isDanger = (res.verdict?.risk_score || 0) >= 40 || res.verdict?.severity === "DANGER";
      setWaChat({
        userText: waInput.trim(),
        botReply: res.whatsapp_rendered_reply || "Threat analysis completed.",
        isDanger,
      });

      if (onAnalysisResult && res.verdict) {
        const analysisPayload: AnalysisResponse = {
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
        };
        const msgText = waInput.trim();
        onAnalysisResult(analysisPayload, {
          inputType: "whatsapp",
          inputLabel: msgText.length > 72 ? msgText.slice(0, 72) + "..." : msgText,
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("WhatsApp bot error: " + msg);
    } finally {
      setWaSending(false);
    }
  };

  const tabClass = (active: boolean) =>
    `flex items-center justify-center gap-2 py-2 px-3 rounded-md font-medium text-xs sm:text-sm transition ${
      active
        ? "bg-white text-zinc-900 shadow-sm border border-zinc-200/80"
        : "text-zinc-600 hover:text-zinc-900 border border-transparent"
    }`;

  return (
    <section className="bg-white rounded-xl border border-zinc-200 p-5 sm:p-6 space-y-5">
      {/* Segmented Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-1 p-1 bg-zinc-100 rounded-lg border border-zinc-200/70">
        <button type="button" onClick={() => setActiveTab("image")} className={tabClass(activeTab === "image")}>
          <ImageIcon className="w-4 h-4 text-zinc-500" />
          <span>{t.upload.tabImage}</span>
        </button>
        <button type="button" onClick={() => setActiveTab("audio")} className={tabClass(activeTab === "audio")}>
          <Mic className="w-4 h-4 text-zinc-500" />
          <span>{t.upload.tabAudio}</span>
        </button>
        <button type="button" onClick={() => setActiveTab("apk")} className={tabClass(activeTab === "apk")}>
          <Package className="w-4 h-4 text-zinc-500" />
          <span>{t.upload.tabApk}</span>
        </button>
        <button type="button" onClick={() => setActiveTab("text")} className={tabClass(activeTab === "text")}>
          <FileText className="w-4 h-4 text-zinc-500" />
          <span>{t.upload.tabText}</span>
        </button>
        <button type="button" onClick={() => setActiveTab("whatsapp")} className={tabClass(activeTab === "whatsapp")}>
          <MessageCircle className="w-4 h-4 text-zinc-500" />
          <span>{t.upload.tabWhatsapp}</span>
        </button>
      </div>

      {/* Tab 1: Image / QR */}
      {activeTab === "image" && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="border border-dashed border-zinc-300 hover:border-zinc-500 rounded-lg p-8 text-center cursor-pointer transition bg-zinc-50/70 hover:bg-zinc-50"
        >
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            className="hidden"
            onChange={(e) => setImageFile(e.target.files?.[0] || null)}
          />
          <div className="flex flex-col items-center gap-3">
            <div className="w-11 h-11 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">{t.upload.dropImagePrompt}</p>
              <p className="text-xs text-zinc-500 mt-1">{t.upload.dropImageHint}</p>
            </div>
            {imageFile && (
              <div className="mt-2 px-3 py-1.5 bg-white rounded-md border border-zinc-200 text-xs text-zinc-800 font-mono flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-700" />
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
          className="border border-dashed border-zinc-300 hover:border-zinc-500 rounded-lg p-8 text-center cursor-pointer transition bg-zinc-50/70 hover:bg-zinc-50"
        >
          <input
            type="file"
            ref={audioInputRef}
            accept="audio/*"
            className="hidden"
            onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
          />
          <div className="flex flex-col items-center gap-3">
            <div className="w-11 h-11 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700">
              <Mic className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-900">{t.upload.dropAudioPrompt}</p>
              <p className="text-xs text-zinc-500 mt-1">{t.upload.dropAudioHint}</p>
            </div>
            {audioFile && (
              <div className="mt-2 px-3 py-1.5 bg-white rounded-md border border-zinc-200 text-xs text-zinc-800 font-mono flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-700" />
                <span>{audioFile.name}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Android APK / File */}
      {activeTab === "apk" && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-zinc-500 font-medium">{t.upload.apkPresetsLabel}</span>
            {[
              { filename: "RTO_eChallan_Pay.apk", label: t.upload.apkPresetRto },
              { filename: "SBI_YONO_KYC_Update.apk", label: t.upload.apkPresetSbi },
              { filename: "PM_Kisan_Subsidy_Form.apk", label: t.upload.apkPresetKisan },
              { filename: "FedEx_Parcel_Helper.apk", label: t.upload.apkPresetFedex },
              { filename: "legit_calculator_sample.apk", label: t.upload.apkPresetSafe },
            ].map((sample) => {
              const isSelected = apkFile?.name === sample.filename;
              const isBusy = loadingApkPreset === sample.filename;
              return (
                <button
                  key={sample.filename}
                  type="button"
                  disabled={Boolean(loadingApkPreset)}
                  onClick={() => handleSelectApkPreset(sample.filename)}
                  className={`text-xs px-2.5 py-1 rounded-md border transition cursor-pointer disabled:opacity-50 ${
                    isSelected
                      ? "bg-zinc-900 border-zinc-900 text-white"
                      : "bg-white hover:bg-zinc-50 border-zinc-200 hover:border-zinc-400 text-zinc-700"
                  }`}
                >
                  {isBusy ? `${sample.label}...` : sample.label}
                </button>
              );
            })}
          </div>

          <div
            onClick={() => apkInputRef.current?.click()}
            className="border border-dashed border-zinc-300 hover:border-zinc-500 rounded-lg p-8 text-center cursor-pointer transition bg-zinc-50/70 hover:bg-zinc-50"
          >
            <input
              type="file"
              ref={apkInputRef}
              accept=".apk,application/vnd.android.package-archive"
              className="hidden"
              onChange={(e) => setApkFile(e.target.files?.[0] || null)}
            />
            <div className="flex flex-col items-center gap-3">
              <div className="w-11 h-11 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700">
                <Package className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-zinc-900">{t.upload.dropApkPrompt}</p>
                <p className="text-xs text-zinc-500 mt-1">{t.upload.dropApkHint}</p>
              </div>
              {apkFile && (
                <div className="mt-2 px-3 py-1.5 bg-white rounded-md border border-zinc-200 text-xs text-zinc-800 font-mono flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-700" />
                  <span>{apkFile.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Text */}
      {activeTab === "text" && (
        <div className="space-y-2">
          <label className="block text-xs font-medium text-zinc-600">{t.upload.tabText}</label>
          <textarea
            rows={4}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={t.upload.pastePlaceholder}
            className="w-full bg-white border border-zinc-300 rounded-lg p-3 text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-zinc-900 transition"
          />
        </div>
      )}

      {/* Tab 5: WhatsApp Bot Simulator */}
      {activeTab === "whatsapp" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3.5 bg-zinc-50 border border-zinc-200 rounded-lg gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 shrink-0">
                <MessageCircle className="w-4 h-4" />
              </div>
              <div>
                <p className="font-medium text-sm text-zinc-900">{t.upload.waTitle}</p>
                <p className="text-xs text-zinc-500">{t.upload.waSubtitle}</p>
              </div>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-white border border-zinc-200 text-zinc-600 font-mono hidden sm:inline-block shrink-0">
              /api/whatsapp/webhook
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-zinc-500 font-medium">{t.upload.waPresetsLabel}</span>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.kyc)}
              className="text-xs px-2.5 py-1 rounded-md bg-white hover:bg-zinc-50 border border-zinc-200 hover:border-zinc-400 text-zinc-700 transition"
            >
              {t.upload.waPresetKyc}
            </button>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.electricity)}
              className="text-xs px-2.5 py-1 rounded-md bg-white hover:bg-zinc-50 border border-zinc-200 hover:border-zinc-400 text-zinc-700 transition"
            >
              {t.upload.waPresetElectricity}
            </button>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.arrest)}
              className="text-xs px-2.5 py-1 rounded-md bg-white hover:bg-zinc-50 border border-zinc-200 hover:border-zinc-400 text-zinc-700 transition"
            >
              {t.upload.waPresetArrest}
            </button>
            <button
              type="button"
              onClick={() => setWaInput(WA_PRESETS.apk)}
              className="text-xs px-2.5 py-1 rounded-md bg-white hover:bg-zinc-50 border border-zinc-200 hover:border-zinc-400 text-zinc-700 transition"
            >
              {t.upload.waPresetApk}
            </button>
          </div>

          <div className="space-y-3">
            <textarea
              rows={3}
              value={waInput}
              onChange={(e) => setWaInput(e.target.value)}
              placeholder={t.upload.waPlaceholder}
              className="w-full bg-white border border-zinc-300 rounded-lg p-3 text-sm text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-zinc-900 transition"
            />
            <button
              type="button"
              onClick={handleWhatsAppSend}
              disabled={waSending}
              className="w-full py-2.5 px-4 rounded-lg font-medium text-sm bg-zinc-900 hover:bg-zinc-800 text-white flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
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
            <div className="rounded-lg bg-zinc-50 border border-zinc-200 p-4 space-y-4 max-h-[450px] overflow-y-auto">
              <div className="flex justify-center">
                <span className="text-[11px] text-zinc-500 bg-white px-2.5 py-0.5 rounded-md border border-zinc-200">
                  Simulated Forward
                </span>
              </div>

              {/* User Forwarded Message */}
              <div className="flex justify-end">
                <div className="max-w-[85%] sm:max-w-[75%] bg-zinc-900 text-zinc-100 p-3 rounded-lg rounded-tr-none text-xs sm:text-sm">
                  <p className="whitespace-pre-wrap leading-relaxed">{waChat.userText}</p>
                  <div className="text-[10px] text-zinc-400 text-right mt-1">Forwarded</div>
                </div>
              </div>

              {/* Bot Reply */}
              <div className="flex justify-start">
                <div className="max-w-[95%] sm:max-w-[85%] bg-white text-zinc-800 p-3.5 rounded-lg rounded-tl-none border border-zinc-200 text-xs sm:text-sm">
                  <div className="flex items-center gap-1.5 text-zinc-900 font-semibold text-xs pb-2 border-b border-zinc-100 mb-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-zinc-700" />
                    <span>CyberGuard AI Responder</span>
                  </div>
                  <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-zinc-700">
                    {waChat.botReply}
                  </pre>
                </div>
              </div>

              {/* 1-Tap Block Fraudster Action if High Risk */}
              {waChat.isDanger && !isBlocked && (
                <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert className="w-4 h-4 text-red-700 shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-red-900">{t.upload.waDangerBadge}</p>
                      <p className="text-[11px] text-red-700">Break scammer contact loop and log evidence</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleBlockFraudster}
                    disabled={blocking}
                    className="w-full sm:w-auto px-3.5 py-2 rounded-md bg-red-700 hover:bg-red-800 text-white font-medium text-xs flex items-center justify-center gap-1.5 transition shrink-0 cursor-pointer disabled:opacity-50"
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
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center gap-2 text-xs text-emerald-900 font-medium">
                  <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
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
          type="button"
          onClick={handleSubmit}
          disabled={isLoading}
          className="w-full py-3 px-5 rounded-lg font-medium text-sm bg-zinc-900 hover:bg-zinc-800 text-white flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{t.upload.scanningButton}</span>
            </>
          ) : (
            <>
              <Scan className="w-4 h-4" />
              <span>{t.upload.scanButton}</span>
            </>
          )}
        </button>
      )}
    </section>
  );
};
