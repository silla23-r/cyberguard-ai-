const DEVICE_ID_KEY = "cyberguard_device_id_v1";

function getBackendBase(): string {
  const raw = process.env.NEXT_PUBLIC_BACKEND_URL;
  return raw ? raw.replace(/\/+$/, "") : "";
}

function apiUrl(path: string): string {
  const base = getBackendBase();
  return base ? `${base}${path}` : path;
}

export function getOrCreateDeviceId(): string {
  if (typeof window === "undefined") return "";
  try {
    let existing = window.localStorage.getItem(DEVICE_ID_KEY);
    if (!existing) {
      const rand = Math.random().toString(36).slice(2, 10).toUpperCase();
      existing = `DEV-${rand}`;
      window.localStorage.setItem(DEVICE_ID_KEY, existing);
    }
    return existing;
  } catch {
    return "DEV-LOCAL";
  }
}

export interface GuardianStatusResponse {
  paired: boolean;
  device_id?: string;
  protected_label?: string;
  guardian_name?: string;
  guardian_phone?: string;
  share_raw_context?: boolean;
  is_paused?: boolean;
  push_enabled?: boolean;
}

export interface GuardianAlertRecord {
  alert_id: string;
  device_id: string;
  session_id: string;
  severity: "SAFE" | "CAUTION" | "DANGER";
  risk_score: number;
  scam_archetype: string;
  delivery_channels: string[];
  created_at: string;
  payload: {
    alert_id: string;
    protected_user_label: string;
    protected_phone?: string;
    guardian_name?: string;
    severity: string;
    risk_score: number;
    scam_archetype: string;
    modality?: string;
    raw_context?: string;
    top_reasons?: string[];
    indicators?: {
      urls?: string[];
      upi_vpas?: string[];
      phone_numbers?: string[];
      remote_tools?: string[];
      apk_package?: string | null;
      apk_permissions?: string[];
    };
    verify_url?: string | null;
    report_pdf_url?: string | null;
  };
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; i += 1) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function fetchGuardianStatus(deviceId: string): Promise<GuardianStatusResponse> {
  const resp = await fetch(apiUrl(`/api/guardian/status/${encodeURIComponent(deviceId)}`));
  if (!resp.ok) throw new Error(`Status check failed (${resp.status})`);
  return resp.json();
}

export async function requestGuardianPair(payload: {
  device_id: string;
  guardian_phone: string;
  guardian_name: string;
  protected_label: string;
  protected_phone: string;
  share_raw_context: boolean;
}): Promise<{
  status: string;
  delivered_via_twilio: boolean;
  delivery_reason?: string;
  demo_otp_preview?: string;
}> {
  const resp = await fetch(apiUrl("/api/guardian/pair/request"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Pairing request failed (${resp.status})`);
  }
  return resp.json();
}

export async function verifyGuardianOtp(deviceId: string, otpCode: string) {
  const resp = await fetch(apiUrl("/api/guardian/pair/verify"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: deviceId, otp_code: otpCode }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `OTP verification failed (${resp.status})`);
  }
  return resp.json();
}

export async function toggleGuardianPause(deviceId: string, paused: boolean) {
  const resp = await fetch(apiUrl("/api/guardian/pause"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: deviceId, paused }),
  });
  if (!resp.ok) throw new Error(`Failed to toggle pause (${resp.status})`);
  return resp.json();
}

export async function revokeGuardianPair(deviceId: string) {
  const resp = await fetch(apiUrl(`/api/guardian/pair/${encodeURIComponent(deviceId)}`), {
    method: "DELETE",
  });
  if (!resp.ok) throw new Error(`Failed to revoke pairing (${resp.status})`);
  return resp.json();
}

export async function fetchGuardianAlerts(deviceId: string): Promise<GuardianAlertRecord[]> {
  const resp = await fetch(apiUrl(`/api/guardian/alerts/${encodeURIComponent(deviceId)}`));
  if (!resp.ok) return [];
  const data = await resp.json();
  return Array.isArray(data.alerts) ? data.alerts : [];
}

export async function triggerTestGuardianAlert(deviceId: string) {
  const resp = await fetch(apiUrl(`/api/guardian/test-alert/${encodeURIComponent(deviceId)}`), {
    method: "POST",
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Test alert failed (${resp.status})`);
  }
  return resp.json();
}

export async function registerGuardianWebPush(deviceId: string): Promise<void> {
  if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window)) {
    throw new Error("Web Push notifications are not supported by this browser.");
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Notification permission was denied. Enable notifications in browser settings.");
  }

  const registration = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;

  const keyResp = await fetch(apiUrl("/api/guardian/vapid-public-key"));
  if (!keyResp.ok) throw new Error("Could not retrieve server VAPID public key.");
  const { public_key: publicKey } = await keyResp.json();

  const existingSub = await registration.pushManager.getSubscription();
  const applicationServerKey = urlBase64ToUint8Array(publicKey);
  const subscription =
    existingSub ||
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey.buffer as ArrayBuffer,
    }));

  const saveResp = await fetch(apiUrl("/api/guardian/push/subscribe"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_id: deviceId,
      subscription: subscription.toJSON(),
    }),
  });
  if (!saveResp.ok) {
    const err = await saveResp.json().catch(() => ({}));
    throw new Error(err.detail || "Could not link phone push subscription to this device.");
  }
}
