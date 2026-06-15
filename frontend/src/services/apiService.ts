import type {
  FingerprintPayload,
  ApiSubmitResponse,
  ApiError,
} from "../types";

export async function submitFingerprint(
  payload: FingerprintPayload
): Promise<ApiSubmitResponse> {
  const response = await fetch("/api/fingerprints", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      error: `HTTP ${response.status}: ${response.statusText}`,
    }));

    throw new Error(error.error ?? "Erro ao enviar a coleta.");
  }

  return response.json() as Promise<ApiSubmitResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch("/health");
    return response.ok;
  } catch {
    return false;
  }
}