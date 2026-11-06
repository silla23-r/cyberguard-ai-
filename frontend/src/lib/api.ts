import { AnalysisResponse } from "./types";

export async function analyzeSubmission(formData: FormData): Promise<AnalysisResponse> {
  const rawBackend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const backendBase = rawBackend ? rawBackend.replace(/\/+$/, "") : "";
  const endpoint = backendBase ? `${backendBase}/api/analyze` : "/api/analyze";

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });
  } catch (netErr: unknown) {
    const msg = netErr instanceof Error ? netErr.message : String(netErr);
    throw new Error(
      `Cannot connect to backend server (${msg}). If using Render free tier, the backend may be waking up. Please wait 30 seconds and try again.`
    );
  }

  if (!response.ok) {
    let errorMessage = "";
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
          .map((item: { msg?: string }) => item.msg || JSON.stringify(item))
          .join("; ");
      }
    } catch {
      // response was not JSON (e.g. 504 Gateway Timeout or 502 Bad Gateway)
    }

    if (response.status === 504 || response.status === 502) {
      throw new Error(
        "Render backend is currently waking up from sleep. Please wait ~45 seconds and click Analyze again!"
      );
    }

    throw new Error(
      errorMessage || `Server responded with status ${response.status} (${response.statusText || "Failed"}).`
    );
  }

  const data: AnalysisResponse = await response.json();

  // If backend returned relative URLs for PDF/Audio, prepend backend base URL
  if (backendBase) {
    if (data.report_pdf_url && data.report_pdf_url.startsWith("/")) {
      data.report_pdf_url = `${backendBase}${data.report_pdf_url}`;
    }
    if (data.audio_advisory_url && data.audio_advisory_url.startsWith("/")) {
      data.audio_advisory_url = `${backendBase}${data.audio_advisory_url}`;
    }
  }

  return data;
}

export interface WhatsAppSimulateResponse {
  simulator_status: string;
  sender: string;
  incoming_message: string;
  whatsapp_rendered_reply: string;
  verdict?: any;
  evidence?: any;
  report_pdf_url?: string | null;
  audio_advisory_url?: string | null;
  steps?: any[];
}

export async function simulateWhatsAppMessage(
  message: string,
  language: string = "en"
): Promise<WhatsAppSimulateResponse> {
  const rawBackend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const backendBase = rawBackend ? rawBackend.replace(/\/+$/, "") : "";
  const endpoint = backendBase ? `${backendBase}/api/whatsapp/simulate` : "/api/whatsapp/simulate";

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender: "whatsapp:+919876543210",
        message,
        language,
      }),
    });
  } catch (netErr: unknown) {
    const msg = netErr instanceof Error ? netErr.message : String(netErr);
    throw new Error(`Cannot connect to WhatsApp Bot endpoint (${msg}).`);
  }

  if (!response.ok) {
    throw new Error(`WhatsApp simulation failed: status ${response.status}`);
  }

  const data: WhatsAppSimulateResponse = await response.json();

  if (backendBase) {
    if (data.report_pdf_url && data.report_pdf_url.startsWith("/")) {
      data.report_pdf_url = `${backendBase}${data.report_pdf_url}`;
    }
    if (data.audio_advisory_url && data.audio_advisory_url.startsWith("/")) {
      data.audio_advisory_url = `${backendBase}${data.audio_advisory_url}`;
    }
  }

  return data;
}

export async function blockWhatsAppFraudster(sender: string, summary: string) {
  const rawBackend = process.env.NEXT_PUBLIC_BACKEND_URL;
  const backendBase = rawBackend ? rawBackend.replace(/\/+$/, "") : "";
  const endpoint = backendBase ? `${backendBase}/api/whatsapp/block` : "/api/whatsapp/block";

  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sender,
      incident_summary: summary,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to block fraudster: status ${response.status}`);
  }

  return response.json();
}
