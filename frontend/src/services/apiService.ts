import type { FingerprintPayload, ApiSubmitResponse, ApiError } from "../types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

export async function submitFingerprint(
  payload: FingerprintPayload
): Promise<ApiSubmitResponse> {
  const response = await fetch(`${API_URL}/api/fingerprints`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const err: ApiError = await response.json().catch(() => ({
      error: `HTTP ${response.status}: ${response.statusText}`,
    }));
    throw new Error(err.error ?? "Unknown error from server.");
  }

  return response.json() as Promise<ApiSubmitResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
