"use client";

import React from "react";
import { History, Image as ImageIcon, Mic, Package, FileText, MessageCircle, Layers, Trash2, X } from "lucide-react";
import { UploadHistoryItem, UploadModality } from "@/lib/types";
import { getTranslation } from "@/lib/translations";

interface UploadHistoryProps {
  items: UploadHistoryItem[];
  activeSessionId?: string | null;
  onSelect: (item: UploadHistoryItem) => void;
  onRemove: (id: string) => void;
  onClearAll: () => void;
  currentLang?: string;
}

function formatBytes(bytes?: number): string | null {
  if (!bytes || bytes <= 0) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function renderModalityIcon(type: UploadModality) {
  switch (type) {
    case "image":
      return <ImageIcon className="w-4 h-4 text-zinc-600" />;
    case "audio":
      return <Mic className="w-4 h-4 text-zinc-600" />;
    case "apk":
      return <Package className="w-4 h-4 text-zinc-600" />;
    case "whatsapp":
      return <MessageCircle className="w-4 h-4 text-zinc-600" />;
    case "multimodal":
      return <Layers className="w-4 h-4 text-zinc-600" />;
    case "text":
    default:
      return <FileText className="w-4 h-4 text-zinc-600" />;
  }
}

export const UploadHistory: React.FC<UploadHistoryProps> = ({
  items,
  activeSessionId,
  onSelect,
  onRemove,
  onClearAll,
  currentLang = "en",
}) => {
  const t = getTranslation(currentLang);

  return (
    <section className="bg-white rounded-xl border border-zinc-200 p-5 sm:p-6 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-zinc-500" />
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            {t.history.heading}
          </h3>
          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-600 border border-zinc-200 tabular-nums">
            {items.length}
          </span>
        </div>

        {items.length > 0 && (
          <button
            type="button"
            onClick={onClearAll}
            className="text-xs text-zinc-500 hover:text-zinc-900 inline-flex items-center gap-1 transition cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{t.history.clearAll}</span>
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="text-xs sm:text-sm text-zinc-500 py-3 px-4 rounded-lg bg-zinc-50 border border-zinc-200/70">
          {t.history.empty}
        </p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const verdict = item.result.verdict;
            const isSelected = activeSessionId === item.result.session_id;
            const sizeLabel = formatBytes(item.fileSizeBytes);
            const severityBadgeClass =
              verdict.severity === "DANGER"
                ? "bg-red-50 text-red-800 border border-red-200"
                : verdict.severity === "CAUTION"
                ? "bg-amber-50 text-amber-800 border border-amber-200"
                : "bg-emerald-50 text-emerald-800 border border-emerald-200";

            return (
              <div
                key={item.id}
                onClick={() => onSelect(item)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelect(item);
                  }
                }}
                className={`group flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border transition cursor-pointer ${
                  isSelected
                    ? "border-zinc-900 bg-zinc-50"
                    : "border-zinc-200 bg-white hover:border-zinc-400 hover:bg-zinc-50/60"
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {item.previewThumbnail ? (
                    <img
                      src={item.previewThumbnail}
                      alt={item.inputLabel}
                      className="w-10 h-10 rounded-md border border-zinc-200 object-cover shrink-0 bg-zinc-100"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-md bg-zinc-100 border border-zinc-200 flex items-center justify-center shrink-0">
                      {renderModalityIcon(item.inputType)}
                    </div>
                  )}

                  <div className="min-w-0 space-y-0.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <p className="text-sm font-medium text-zinc-900 truncate">
                        {item.inputLabel}
                      </p>
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-600 shrink-0">
                        {item.inputType}
                      </span>
                      {sizeLabel && (
                        <span className="text-[11px] font-mono text-zinc-400 shrink-0 hidden md:inline">
                          {sizeLabel}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-500 truncate">
                      <span>{item.uploadedAt}</span>
                      <span className="mx-1.5 text-zinc-300">·</span>
                      <span className="text-zinc-600">
                        {verdict.scam_archetype.replace(/_/g, " ")}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-2.5 shrink-0 sm:pl-0">
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded font-semibold tabular-nums ${severityBadgeClass}`}
                  >
                    {verdict.risk_score}/100 · {verdict.severity}
                  </span>

                  <span className="text-xs font-medium text-zinc-600 group-hover:text-zinc-900">
                    {t.history.viewItem}
                  </span>

                  <button
                    type="button"
                    aria-label="Remove history entry"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemove(item.id);
                    }}
                    className="p-1 rounded text-zinc-400 hover:text-zinc-900 hover:bg-zinc-200/60 transition cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
