// Mirrors the backend Pydantic schemas (src/pls_ct/app/schemas.py).

export interface Stats {
  trials: number;
  documents: number;
  sections: number;
  chunks: number;
  experiments: number;
}

export interface BackendInfo {
  spec: string;
  kind: string;
  available: boolean;
  detail?: string | null;
}

export interface TrialSummary {
  protocol_id: string;
  source: string;
  document_kinds: string[];
}

export interface TrialPage {
  items: TrialSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentOut {
  kind: string;
  fmt: string;
  status: string;
  n_sections: number;
}

export interface TrialDetail {
  protocol_id: string;
  source: string;
  documents: DocumentOut[];
  report_sections: Record<string, string>;
  summary_sections: Record<string, string>;
}

export interface SummarizeRequest {
  trial_name?: string;
  context?: string;
  question?: string;
  backend: string;
  max_new_tokens?: number;
  temperature?: number;
  top_p?: number;
  api_key?: string;
}

export interface SummarizeResponse {
  text: string;
  model: string;
  input_tokens: number | null;
  output_tokens: number | null;
  latency_s: number | null;
  warnings: string[];
  run_id: string;
  provenance: Record<string, unknown> | null;
}

export interface Citation {
  trial_name: string;
  section: string;
  start: number;
  end: number;
  score: number;
}

export interface AskResponse {
  answer: string;
  sufficient: boolean;
  citations: Citation[];
}

export interface JobOut {
  id: number;
  kind: string;
  status: string;
  result: { n_chars?: number; preview?: string; warnings?: string[] } | null;
  error: string | null;
}

export interface UploadResponse {
  job_id: number;
  status: string;
}

export interface ExperimentResult {
  backend: string;
  n_scored: number;
  n_errors: number;
  aggregate: Record<string, number>;
}

export interface Experiment {
  id: number;
  created_at: string;
  split_fingerprint: string;
  n_examples: number;
  results: ExperimentResult[];
}
