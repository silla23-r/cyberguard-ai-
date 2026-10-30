"use client";

import React, { useState } from "react";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { UploadZone } from "@/components/UploadZone";
import { ThreatScore } from "@/components/ThreatScore";
import { AgentTimeline } from "@/components/AgentTimeline";
import { EvidencePanel } from "@/components/EvidencePanel";
import { ActionPanel } from "@/components/ActionPanel";
import { Footer } from "@/components/Footer";
import { analyzeSubmission } from "@/lib/api";
import { AnalysisResponse, AgentStep } from "@/lib/types";

export default function Home() {
  const [currentLang, setCurrentLang] = useState("en");
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [timelineSteps, setTimelineSteps] = useState<AgentStep[]>([]);

  const handleAnalyze = async (formData: FormData) => {
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      alert("Analysis error: " + (msg || "Failed to process request."));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header currentLang={currentLang} onLangChange={setCurrentLang} />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8 space-y-8">
        <HeroSection />

        <UploadZone
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
          selectedLang={currentLang}
        />

        {timelineSteps.length > 0 && <AgentTimeline steps={timelineSteps} />}

        {analysisResult && (
          <section className="space-y-6 pt-4">
            <ThreatScore
              verdict={analysisResult.verdict}
              reportPdfUrl={analysisResult.report_pdf_url}
              audioAdvisoryUrl={analysisResult.audio_advisory_url}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <EvidencePanel
                verdict={analysisResult.verdict}
                evidence={analysisResult.evidence}
              />
              <ActionPanel verdict={analysisResult.verdict} />
            </div>
          </section>
        )}
      </main>

      <Footer />
    </div>
  );
}

