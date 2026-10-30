"use client";

import React from "react";
import { Cpu, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { AgentStep } from "@/lib/types";

interface AgentTimelineProps {
  steps: AgentStep[];
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ steps }) => {
  return (
    <section className="bg-guard-800 rounded-2xl border border-guard-700 p-6 space-y-4">
      <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
        <Cpu className="w-4 h-4 text-blue-400" />
        <span>Autonomous Multi-Agent Execution Pipeline</span>
      </h3>
      <div className="space-y-3">
        {steps.map((s, idx) => (
          <div
            key={idx}
            className="flex items-start gap-3 text-xs p-2.5 rounded-lg bg-guard-900 border border-guard-700/60"
          >
            {s.status === "completed" && (
              <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
            )}
            {s.status === "running" && (
              <Loader2 className="w-4 h-4 text-blue-400 animate-spin mt-0.5 shrink-0" />
            )}
            {s.status === "failed" && (
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            )}
            <div>
              <span className="font-bold text-slate-200">{s.agent_name}:</span>
              <span className="text-slate-400 ml-1.5">{s.message}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

