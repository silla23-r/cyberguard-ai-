"use client";

import React, { useState, useRef } from "react";
import { Image as ImageIcon, Mic, FileText, UploadCloud, FileCheck, Scan, Loader2 } from "lucide-react";

interface UploadZoneProps {
  onAnalyze: (formData: FormData) => void;
  isLoading: boolean;
  selectedLang: string;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onAnalyze, isLoading, selectedLang }) => {
  const [activeTab, setActiveTab] = useState<"image" | "audio" | "text">("image");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [textInput, setTextInput] = useState("");

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

  return (
    <section className="bg-guard-800 rounded-2xl border border-guard-700 shadow-xl p-6 sm:p-8 space-y-6">
      {/* Tabs */}
      <div className="grid grid-cols-3 gap-3 p-1.5 bg-guard-900 rounded-xl border border-guard-700">
        <button
          onClick={() => setActiveTab("image")}
          className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm transition ${
            activeTab === "image" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <ImageIcon className="w-4 h-4" />
          <span>Screenshot / QR</span>
        </button>
        <button
          onClick={() => setActiveTab("audio")}
          className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm transition ${
            activeTab === "audio" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>Call Recording</span>
        </button>
        <button
          onClick={() => setActiveTab("text")}
          className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg font-medium text-sm transition ${
            activeTab === "text" ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Pasted Message</span>
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
              <p className="font-semibold text-slate-200">Click to upload screenshot or drag and drop</p>
              <p className="text-xs text-slate-400 mt-1">WhatsApp message, suspicious SMS, Bank email, or payment QR code (PNG, JPG)</p>
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
              <p className="font-semibold text-slate-200">Upload Call Audio / Voice Note</p>
              <p className="text-xs text-slate-400 mt-1">Recordings of suspected police / courier / KYC extortion calls (MP3, WAV, M4A)</p>
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
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Paste Suspicious Message / SMS / Link</label>
          <textarea
            rows={4}
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Dear Customer, your electricity power will be disconnected tonight at 9:30 PM due to unpaid bill. Immediately contact officer at +919876543210 or pay to bescom@okaxis"
            className="w-full bg-guard-900 border border-guard-600 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
          />
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={handleSubmit}
        disabled={isLoading}
        className="w-full py-4 px-6 rounded-xl font-bold text-base bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition duration-200 cursor-pointer disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>ANALYZING THREAT TELEMETRY...</span>
          </>
        ) : (
          <>
            <Scan className="w-5 h-5" />
            <span>SCAN & ANALYZE WITH CYBERGUARD AI</span>
          </>
        )}
      </button>
    </section>
  );
};

