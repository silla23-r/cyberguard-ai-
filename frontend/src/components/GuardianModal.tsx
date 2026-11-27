"use client";

import React, { useEffect, useState } from "react";
import {
  Bell,
  BellOff,
  CheckCircle2,
  Copy,
  FileDown,
  PhoneCall,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import {
  fetchGuardianAlerts,
  fetchGuardianStatus,
  getOrCreateDeviceId,
  GuardianAlertRecord,
  GuardianStatusResponse,
  registerGuardianWebPush,
  requestGuardianPair,
  revokeGuardianPair,
  toggleGuardianPause,
  triggerTestGuardianAlert,
  verifyGuardianOtp,
} from "@/lib/guardianPush";

interface GuardianModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "protect" | "guardian";
  initialTargetDeviceId?: string;
  onStatusChange?: (status: GuardianStatusResponse) => void;
}

export const GuardianModal: React.FC<GuardianModalProps> = ({
  isOpen,
  onClose,
  initialTab = "protect",
  initialTargetDeviceId = "",
  onStatusChange,
}) => {
  const [tab, setTab] = useState<"protect" | "guardian">(initialTab);
  const [ownDeviceId, setOwnDeviceId] = useState("");
  const [status, setStatus] = useState<GuardianStatusResponse>({ paired: false });

  // Protect This Device form state
  const [protectedLabel, setProtectedLabel] = useState("Mom");
  const [protectedPhone, setProtectedPhone] = useState("");
  const [guardianName, setGuardianName] = useState("Family Guardian");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [shareRawContext, setShareRawContext] = useState(true);
  const [consentChecked, setConsentChecked] = useState(false);

  // OTP state
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [demoOtpHint, setDemoOtpHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Guardian Phone view state
  const [targetDeviceId, setTargetDeviceId] = useState(initialTargetDeviceId);
  const [alerts, setAlerts] = useState<GuardianAlertRecord[]>([]);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const id = getOrCreateDeviceId();
    setOwnDeviceId(id);
    if (!targetDeviceId && !initialTargetDeviceId) {
      setTargetDeviceId(id);
    } else if (initialTargetDeviceId) {
      setTargetDeviceId(initialTargetDeviceId);
    }
    setTab(initialTab);
    setErrorMsg(null);
    setFeedback(null);

    if (id) {
      fetchGuardianStatus(id)
        .then((res) => {
          setStatus(res);
          onStatusChange?.(res);
        })
        .catch(() => {});
    }
  }, [isOpen, initialTab, initialTargetDeviceId]);

  const refreshAlerts = async (devId: string) => {
    if (!devId.trim()) return;
    const list = await fetchGuardianAlerts(devId.trim());
    setAlerts(list);
  };

  useEffect(() => {
    if (isOpen && tab === "guardian" && targetDeviceId.trim()) {
      refreshAlerts(targetDeviceId.trim());
    }
  }, [isOpen, tab, targetDeviceId]);

  if (!isOpen) return null;

  const copyText = (key: string, value: string) => {
    navigator.clipboard?.writeText(value);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1800);
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFeedback(null);
    if (!guardianPhone.trim()) {
      setErrorMsg("Enter Guardian's WhatsApp or SMS phone number (with country code, e.g. +91...).");
      return;
    }
    if (!consentChecked) {
      setErrorMsg("Please check the consent box to authorize Guardian alerts.");
      return;
    }
    setBusy(true);
    try {
      const res = await requestGuardianPair({
        device_id: ownDeviceId,
        guardian_phone: guardianPhone.trim(),
        guardian_name: guardianName.trim() || "Family Guardian",
        protected_label: protectedLabel.trim() || "Mom",
        protected_phone: protectedPhone.trim(),
        share_raw_context: shareRawContext,
      });
      setOtpRequested(true);
      setDemoOtpHint(res.demo_otp_preview || null);
      setFeedback(
        res.delivered_via_twilio
          ? "6-digit Consent OTP sent to Guardian via WhatsApp/SMS."
          : (res.delivery_reason || "SMS/WhatsApp gateway unavailable — use the Consent Code below to verify.")
      );
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFeedback(null);
    setBusy(true);
    try {
      await verifyGuardianOtp(ownDeviceId, otpInput.trim());
      const fresh = await fetchGuardianStatus(ownDeviceId);
      setStatus(fresh);
      onStatusChange?.(fresh);
      setOtpRequested(false);
      setOtpInput("");
      setDemoOtpHint(null);
      setFeedback("Guardian protection verified and active.");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleTogglePause = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const nextPaused = !status.is_paused;
      await toggleGuardianPause(ownDeviceId, nextPaused);
      const fresh = await fetchGuardianStatus(ownDeviceId);
      setStatus(fresh);
      onStatusChange?.(fresh);
      setFeedback(nextPaused ? "Guardian alerts paused." : "Guardian alerts resumed.");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleRevoke = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      await revokeGuardianPair(ownDeviceId);
      const empty: GuardianStatusResponse = { paired: false };
      setStatus(empty);
      onStatusChange?.(empty);
      setAlerts([]);
      setFeedback("Guardian link permanently revoked and deleted.");
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleSendTestAlert = async () => {
    setBusy(true);
    setErrorMsg(null);
    try {
      const res = await triggerTestGuardianAlert(ownDeviceId);
      setFeedback(`Test alert sent (${res.channels.join(", ")}). Check the Guardian Alerts tab.`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const handleSubscribeGuardianPhone = async () => {
    setBusy(true);
    setErrorMsg(null);
    setFeedback(null);
    try {
      await registerGuardianWebPush(targetDeviceId.trim());
      setPushSubscribed(true);
      setFeedback(`This phone is now subscribed to instant Web Push alerts for ${targetDeviceId}.`);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const guardianShareUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/?guardian_device=${encodeURIComponent(ownDeviceId)}`
      : `/?guardian_device=${ownDeviceId}`;

  return (
    <div className="fixed inset-0 z-50 bg-zinc-950/40 backdrop-blur-[1px] flex items-center justify-center p-4">
      <div className="bg-white border border-zinc-200 rounded-xl w-full max-w-xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-zinc-200 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 flex items-center justify-center text-white shrink-0">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-900">Family Guardian Protection</h3>
              <p className="text-xs text-zinc-500">Real-time scam notifications with mutual consent</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="p-1.5 rounded-md text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Segmented Tabs */}
        <div className="px-5 pt-4">
          <div className="grid grid-cols-2 gap-1 p-1 bg-zinc-100 rounded-lg border border-zinc-200/80">
            <button
              type="button"
              onClick={() => setTab("protect")}
              className={`py-2 px-3 rounded-md text-xs font-medium transition cursor-pointer ${
                tab === "protect"
                  ? "bg-white text-zinc-900 shadow-sm border border-zinc-200/80"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Protect This Device (Mom)
            </button>
            <button
              type="button"
              onClick={() => setTab("guardian")}
              className={`py-2 px-3 rounded-md text-xs font-medium transition cursor-pointer ${
                tab === "guardian"
                  ? "bg-white text-zinc-900 shadow-sm border border-zinc-200/80"
                  : "text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Guardian Phone & Alerts
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-sm">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-900">
              {errorMsg}
            </div>
          )}
          {feedback && (
            <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-300 text-xs text-zinc-900">
              {feedback}
            </div>
          )}

          {/* TAB 1: PROTECT THIS DEVICE */}
          {tab === "protect" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-50 border border-zinc-200">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
                    Device Pairing ID
                  </p>
                  <p className="text-xs font-mono font-semibold text-zinc-900 mt-0.5">
                    {ownDeviceId}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => copyText("dev", ownDeviceId)}
                  className="text-xs px-2.5 py-1.5 rounded-md bg-white border border-zinc-200 hover:border-zinc-400 text-zinc-700 inline-flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" />
                  <span>{copiedKey === "dev" ? "Copied" : "Copy ID"}</span>
                </button>
              </div>

              {status.paired ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-lg border border-zinc-200 bg-white space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-900 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                        {status.is_paused ? "Guardian Alerts Paused" : "Guardian Protection Active"}
                      </span>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                        {status.push_enabled ? "Push Connected" : "SMS/WhatsApp Ready"}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-600 space-y-1 pt-1 border-t border-zinc-100">
                      <p>
                        Protected Label: <span className="font-medium text-zinc-900">{status.protected_label}</span>
                      </p>
                      <p>
                        Guardian: <span className="font-medium text-zinc-900">{status.guardian_name}</span> ({status.guardian_phone})
                      </p>
                      <p>
                        Raw Message Context:{" "}
                        <span className="font-medium text-zinc-900">
                          {status.share_raw_context ? "Shared (Consent Verified)" : "Redacted Only"}
                        </span>
                      </p>
                    </div>
                  </div>

                  {/* Shareable link for Guardian's Phone */}
                  <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200 space-y-2">
                    <p className="text-xs font-medium text-zinc-800">
                      Open this link on your Guardian phone to enable instant Web Push:
                    </p>
                    <div className="flex items-center gap-2">
                      <input
                        readOnly
                        value={guardianShareUrl}
                        className="flex-1 bg-white border border-zinc-200 rounded-md px-2.5 py-1.5 text-xs font-mono text-zinc-600 outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => copyText("url", guardianShareUrl)}
                        className="text-xs px-3 py-1.5 rounded-md bg-zinc-900 text-white font-medium shrink-0 cursor-pointer"
                      >
                        {copiedKey === "url" ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={handleSendTestAlert}
                      className="flex-1 py-2 px-3 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium inline-flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <Bell className="w-3.5 h-3.5" />
                      <span>Send Test Alert</span>
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={handleTogglePause}
                      className="py-2 px-3 rounded-lg bg-white hover:bg-zinc-50 border border-zinc-200 text-zinc-800 text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <BellOff className="w-3.5 h-3.5" />
                      <span>{status.is_paused ? "Resume" : "Pause"}</span>
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={handleRevoke}
                      className="py-2 px-3 rounded-lg bg-red-50 hover:bg-red-100 border border-red-200 text-red-900 text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Revoke</span>
                    </button>
                  </div>
                </div>
              ) : !otpRequested ? (
                <form onSubmit={handleRequestOtp} className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-zinc-700">Protected User Label</label>
                      <input
                        value={protectedLabel}
                        onChange={(e) => setProtectedLabel(e.target.value)}
                        placeholder="e.g. Mom"
                        className="w-full bg-white border border-zinc-300 rounded-md px-3 py-2 text-xs text-zinc-900 outline-none focus:border-zinc-900"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-zinc-700">Her Callback Number (Optional — for Call button)</label>
                      <input
                        value={protectedPhone}
                        onChange={(e) => setProtectedPhone(e.target.value)}
                        placeholder="+9198XXXXXXXX"
                        className="w-full bg-white border border-zinc-300 rounded-md px-3 py-2 text-xs text-zinc-900 outline-none focus:border-zinc-900"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-zinc-700">Guardian Name</label>
                      <input
                        value={guardianName}
                        onChange={(e) => setGuardianName(e.target.value)}
                        placeholder="e.g. Rohan"
                        className="w-full bg-white border border-zinc-300 rounded-md px-3 py-2 text-xs text-zinc-900 outline-none focus:border-zinc-900"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-zinc-700">Guardian Phone (Receives OTP &amp; Alerts)</label>
                      <input
                        value={guardianPhone}
                        onChange={(e) => setGuardianPhone(e.target.value)}
                        placeholder="+919876543210"
                        required
                        className="w-full bg-white border border-zinc-300 rounded-md px-3 py-2 text-xs text-zinc-900 outline-none focus:border-zinc-900"
                      />
                    </div>
                  </div>

                  <label className="flex items-start gap-2 text-xs text-zinc-600 cursor-pointer pt-1">
                    <input
                      type="checkbox"
                      checked={shareRawContext}
                      onChange={(e) => setShareRawContext(e.target.checked)}
                      className="mt-0.5 accent-zinc-900"
                    />
                    <span>Include full suspicious message context inside alerts (recommended for quick verification)</span>
                  </label>

                  <label className="flex items-start gap-2 text-xs text-zinc-700 font-medium cursor-pointer">
                    <input
                      type="checkbox"
                      checked={consentChecked}
                      onChange={(e) => setConsentChecked(e.target.checked)}
                      className="mt-0.5 accent-zinc-900"
                    />
                    <span>I explicitly authorize CyberGuard-AI to notify my Guardian on CAUTION (30+) and DANGER (65+) detections.</span>
                  </label>

                  <button
                    type="submit"
                    disabled={busy}
                    className="w-full py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium transition cursor-pointer disabled:opacity-50"
                  >
                    {busy ? "Sending Consent OTP..." : "Send 6-Digit Consent OTP"}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleVerifyOtp} className="space-y-3">
                  {demoOtpHint && (
                    <div className="p-3 rounded-lg bg-zinc-100 border border-zinc-300 text-xs text-zinc-900 space-y-1">
                      <div className="font-mono">
                        Verification OTP Code: <strong>{demoOtpHint}</strong>
                      </div>
                      <p className="text-[11px] text-zinc-600 leading-snug">
                        SMS/WhatsApp OTP was not sent because the Twilio gateway is not active. Enter this Consent Code below to activate free Web Push alerts.
                      </p>
                    </div>
                  )}
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-zinc-700">
                      Enter 6-digit Consent OTP confirmed by Guardian
                    </label>
                    <input
                      value={otpInput}
                      onChange={(e) => setOtpInput(e.target.value)}
                      maxLength={6}
                      placeholder="123456"
                      required
                      className="w-full bg-white border border-zinc-300 rounded-md px-3 py-2 text-sm font-mono tracking-widest text-zinc-900 outline-none focus:border-zinc-900"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      disabled={busy}
                      className="flex-1 py-2.5 px-4 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium cursor-pointer disabled:opacity-50"
                    >
                      {busy ? "Verifying..." : "Confirm & Activate Guardian"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setOtpRequested(false)}
                      className="py-2.5 px-3 rounded-lg bg-white border border-zinc-200 text-zinc-700 text-xs font-medium cursor-pointer"
                    >
                      Back
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* TAB 2: GUARDIAN PHONE & LIVE ALERTS */}
          {tab === "guardian" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-lg bg-zinc-50 border border-zinc-200 space-y-3">
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    value={targetDeviceId}
                    onChange={(e) => setTargetDeviceId(e.target.value)}
                    placeholder="Protected Device ID (e.g. DEV-XXXXXX)"
                    className="flex-1 bg-white border border-zinc-300 rounded-md px-3 py-2 text-xs font-mono text-zinc-900 outline-none focus:border-zinc-900"
                  />
                  <button
                    type="button"
                    disabled={busy || !targetDeviceId.trim()}
                    onClick={handleSubscribeGuardianPhone}
                    className="px-3.5 py-2 rounded-md bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-medium shrink-0 cursor-pointer disabled:opacity-50"
                  >
                    {pushSubscribed ? "Push Active" : "Enable Phone Push"}
                  </button>
                </div>
                <div className="flex items-center justify-between text-xs text-zinc-500">
                  <span>Triggers VAPID Web Push even when browser is closed.</span>
                  <button
                    type="button"
                    onClick={() => refreshAlerts(targetDeviceId)}
                    className="inline-flex items-center gap-1 text-zinc-700 hover:text-zinc-900 font-medium cursor-pointer"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>

              <div className="space-y-2.5">
                {alerts.length === 0 ? (
                  <p className="text-xs text-zinc-500 py-4 text-center border border-zinc-200 rounded-lg bg-zinc-50">
                    No Guardian alerts recorded yet for {targetDeviceId || "this device"}.
                  </p>
                ) : (
                  alerts.map((al) => {
                    const p = al.payload;
                    const isDanger = al.severity === "DANGER";
                    return (
                      <div
                        key={al.alert_id}
                        className={`p-4 rounded-lg border space-y-2.5 ${
                          isDanger ? "bg-red-50/50 border-red-200" : "bg-white border-zinc-200"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2">
                            <ShieldAlert className={`w-4 h-4 ${isDanger ? "text-red-700" : "text-zinc-700"}`} />
                            <span className="text-xs font-semibold text-zinc-900">
                              {p.protected_user_label} — {al.scam_archetype.replace(/_/g, " ")}
                            </span>
                          </div>
                          <span
                            className={`text-[11px] font-semibold px-2 py-0.5 rounded tabular-nums ${
                              isDanger
                                ? "bg-red-100 text-red-900 border border-red-200"
                                : "bg-amber-50 text-amber-800 border border-amber-200"
                            }`}
                          >
                            {al.risk_score}/100 · {al.severity}
                          </span>
                        </div>

                        {p.raw_context && (
                          <p className="text-xs text-zinc-700 bg-white p-2.5 rounded border border-zinc-200/80 whitespace-pre-wrap">
                            {p.raw_context}
                          </p>
                        )}

                        <div className="flex flex-wrap gap-1.5 text-[11px] font-mono">
                          {al.delivery_channels.map((ch) => (
                            <span key={ch} className="px-2 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-700">
                              {ch}
                            </span>
                          ))}
                        </div>

                        <div className="flex flex-wrap items-center gap-2 pt-1">
                          {p.protected_phone && (
                            <a
                              href={`tel:${p.protected_phone}`}
                              className="px-3 py-1.5 rounded-md bg-zinc-900 text-white text-xs font-medium inline-flex items-center gap-1.5"
                            >
                              <PhoneCall className="w-3.5 h-3.5" />
                              <span>Call {p.protected_user_label}</span>
                            </a>
                          )}
                          <a
                            href="tel:1930"
                            className="px-3 py-1.5 rounded-md bg-red-700 text-white text-xs font-medium inline-flex items-center gap-1.5"
                          >
                            <PhoneCall className="w-3.5 h-3.5" />
                            <span>Dial 1930</span>
                          </a>
                          {p.report_pdf_url && (
                            <a
                              href={p.report_pdf_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1.5 rounded-md bg-white border border-zinc-200 text-zinc-800 text-xs font-medium inline-flex items-center gap-1.5"
                            >
                              <FileDown className="w-3.5 h-3.5" />
                              <span>PDF Report</span>
                            </a>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
