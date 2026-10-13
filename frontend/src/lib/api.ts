import type {
  AskResponse,
  BackendInfo,
  Experiment,
  JobOut,
  Stats,
  SummarizeRequest,
  SummarizeResponse,
  TrialDetail,
  TrialPage,
  UploadResponse,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";

export class ApiError extends Error {
  status: number;
  detail?: string;
  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (err) {
    throw new ApiError(0, "network error — is the API running?", String(err));
  }
  if (!resp.ok) {
    let detail: string | undefined;
    let error = `request failed (${resp.status})`;
    try {
      const body = await resp.json();
      error = body.error ?? error;
      detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, error, detail);
  }
  return (await resp.json()) as T;
}

export const api = {
  stats: () => http<Stats>("/stats"),
  backends: () => http<{ backends: BackendInfo[] }>("/backends"),
  trials: (params: { q?: string; limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set("q", params.q);
    if (params.limit != null) qs.set("limit", String(params.limit));
    if (params.offset != null) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs}` : "";
    return http<TrialPage>(`/trials${suffix}`);
  },
  trial: (id: string) => http<TrialDetail>(`/trials/${encodeURIComponent(id)}`),
  summarize: (body: SummarizeRequest) =>
    http<SummarizeResponse>("/summarize", { method: "POST", body: JSON.stringify(body) }),
  experiments: () => http<Experiment[]>("/experiments"),
  ask: (body: { query: string; trial_name?: string; k?: number; backend?: string }) =>
    http<AskResponse>("/rag/ask", { method: "POST", body: JSON.stringify(body) }),
  job: (id: number) => http<JobOut>(`/jobs/${id}`),
  uploadPdf: async (file: File): Promise<UploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    let resp: Response;
    try {
      // No Content-Type header: the browser sets the multipart boundary.
      resp = await fetch(`${BASE}/uploads`, { method: "POST", body: form });
    } catch (err) {
      throw new ApiError(0, "network error — is the API running?", String(err));
    }
    if (!resp.ok) {
      let detail: string | undefined;
      let error = `upload failed (${resp.status})`;
      try {
        const body = await resp.json();
        error = body.error ?? error;
        detail = body.detail;
      } catch {
        /* non-JSON */
      }
      throw new ApiError(resp.status, error, detail);
    }
    return (await resp.json()) as UploadResponse;
  },
};
