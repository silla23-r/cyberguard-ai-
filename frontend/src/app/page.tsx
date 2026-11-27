"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { UploadZone } from "@/components/UploadZone";
import { ThreatScore } from "@/components/ThreatScore";
import { AgentTimeline } from "@/components/AgentTimeline";
import { EvidencePanel } from "@/components/EvidencePanel";
import { ActionPanel } from "@/components/ActionPanel";
import { UploadHistory } from "@/components/UploadHistory";
import { Footer } from "@/components/Footer";
import { analyzeSubmission } from "@/lib/api";
import { AnalysisResponse, AgentStep, UploadHistoryItem, UploadMetadata } from "@/lib/types";

const HISTORY_STORAGE_KEY = "cyberguard_upload_history_v1";
const MAX_HISTORY_ITEMS = 20;

export default function Home() {
  const [currentLang, setCurrentLang] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [timelineSteps, setTimelineSteps] = useState<AgentStep[]>([]);
  const [uploadHistory, setUploadHistory] = useState<UploadHistoryItem[]>([]);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setUploadHistory(parsed);
        }
      }
    } catch {
      // Ignore storage read errors in restricted contexts
    }
  }, []);

  const persistHistory = (nextItems: UploadHistoryItem[]) => {
    setUploadHistory(nextItems);
    try {
      window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(nextItems));
    } catch {
      // Retry without thumbnails if quota exceeded
      try {
        const stripped = nextItems.map((item) => ({ ...item, previewThumbnail: null }));
        window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(stripped));
      } catch {
        // Ignore storage write failure
      }
    }
  };

  const recordHistory = (data: AnalysisResponse, meta: UploadMetadata) => {
    const entry: UploadHistoryItem = {
      id: `${data.session_id}-${Date.now()}`,
      uploadedAt: new Date().toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }),
      inputType: meta.inputType,
      inputLabel: meta.inputLabel,
      fileSizeBytes: meta.fileSizeBytes,
      previewThumbnail: meta.previewThumbnail ?? null,
      result: data,
    };
    const next = [entry, ...uploadHistory.filter((i) => i.result.session_id !== data.session_id)].slice(
      0,
      MAX_HISTORY_ITEMS
    );
    persistHistory(next);
  };

  const handleAnalyze = async (formData: FormData, meta: UploadMetadata) => {
    setIsLoading(true);
    setAnalysisResult(null);

    // Initial optimistic step
    setTimelineSteps([
      {
        step_id: "init",
        agent_name: "Supervisor Router",
        status: "running",
        message: "Ingesting multimodal telemetry and routing to forensic sub-agents...",
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    try {
      const data = await analyzeSubmission(formData);
      setAnalysisResult(data);
      setTimelineSteps(data.steps || []);
      recordHistory(data, meta);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Analysis error: " + (msg || "Failed to process request."));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistoryItem = (item: UploadHistoryItem) => {
    setAnalysisResult(item.result);
    setTimelineSteps(item.result.steps || []);
    const el = document.getElementById("verdict-section");
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const handleRemoveHistoryItem = (id: string) => {
    persistHistory(uploadHistory.filter((item) => item.id !== id));
  };

  const handleClearHistory = () => {
    persistHistory([]);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header currentLang={currentLang} onLangChange={setCurrentLang} />

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-10 space-y-6">
        <HeroSection currentLang={currentLang} />

        <UploadZone
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          selectedLang={currentLang}
          onAnalysisResult={(data, meta) => {
            setAnalysisResult(data);
            setTimelineSteps(data.steps || []);
            recordHistory(data, meta);
          }}
        />

        {timelineSteps.length > 0 && <AgentTimeline steps={timelineSteps} />}

        {analysisResult && (
          <section id="verdict-section" className="space-y-4 pt-2">
            <ThreatScore
              verdict={analysisResult.verdict}
              reportPdfUrl={analysisResult.report_pdf_url}
              audioAdvisoryUrl={analysisResult.audio_advisory_url}
              currentLang={currentLang}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <EvidencePanel
                verdict={analysisResult.verdict}
                evidence={analysisResult.evidence}
                currentLang={currentLang}
              />
              <ActionPanel verdict={analysisResult.verdict} currentLang={currentLang} />
            </div>
          </section>
        )}

        <UploadHistory
          items={uploadHistory}
          activeSessionId={analysisResult?.session_id}
          onSelect={handleSelectHistoryItem}
          onRemove={handleRemoveHistoryItem}
          onClearAll={handleClearHistory}
          currentLang={currentLang}
        />
      </main>

      <Footer currentLang={currentLang} />
    </div>
  );
}
