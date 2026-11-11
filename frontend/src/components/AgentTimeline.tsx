"use client";

import React from "react";
import { Activity, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { AgentStep } from "@/lib/types";

interface AgentTimelineProps {
  steps: AgentStep[];
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ steps }) => {
  return (
    <section className="bg-white rounded-xl border border-zinc-200 p-5 sm:p-6 space-y-3">
      <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
        <Activity className="w-3.5 h-3.5 text-zinc-500" />
        <span>Verification Pipeline</span>
      </h3>
      <div className="space-y-2">
        {steps.map((s, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2.5 text-xs py-2.5 px-3 rounded-lg bg-zinc-50 border border-zinc-200/70"
          >
            {s.status === "completed" && (
              <CheckCircle2 className="w-4 h-4 text-emerald-700 mt-0.5 shrink-0" />
            )}
            {s.status === "running" && (
              <Loader2 className="w-4 h-4 text-zinc-700 animate-spin mt-0.5 shrink-0" />
            )}
            {s.status === "failed" && (
              <AlertCircle className="w-4 h-4 text-red-700 mt-0.5 shrink-0" />
            )}
            <div className="leading-relaxed">
              <span className="font-medium text-zinc-900">{s.agent_name}</span>
              <span className="text-zinc-600 ml-1.5">{s.message}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
