import { AnalysisResponse } from "./types";

export async function analyzeSubmission(formData: FormData): Promise<AnalysisResponse> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let errorMessage = "Analysis request failed.";
    if (typeof errorData.detail === "string") {
      errorMessage = errorData.detail;
    } else if (Array.isArray(errorData.detail)) {
      errorMessage = errorData.detail
        .map((item: { msg?: string }) => item.msg || JSON.stringify(item))
        .join("; ");
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
