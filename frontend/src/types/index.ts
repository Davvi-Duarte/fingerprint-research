export type FingerprintJSResult = Record<string, unknown>;

export interface FingerprintPayload {
  participant_name: string;
  fingerprint_result: FingerprintJSResult;
}

export interface ApiSubmitResponse {
  message: string;
  id: number;
  participant_id?: string;
  session_id?: string;
  created_at: string;
}

export interface ApiError {
  error: string;
  details?: Record<string, string[]>;
}

export type SubmissionStatus = "idle" | "loading" | "success" | "error";