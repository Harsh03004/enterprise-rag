import { apiFetch } from "./client";

export interface AdminSummary {
  users: number;
  documents: number;
  processing_jobs: number;
  queries: number;
  average_query_latency_ms: number;
}

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  can_change_status: boolean;
  created_at: string;
}

export interface AnalyticsPoint {
  date: string;
  queries: number;
  failures: number;
  latency_ms: number;
  average_latency_ms: number;
}

export interface ProviderStats {
  provider: string;
  model: string;
  queries: number;
  failures: number;
  latency_ms: number;
  average_latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
}

export interface AdminAnalytics {
  days: number;
  total_queries: number;
  failed_queries: number;
  fallback_queries: number;
  cache_hits: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  verification_latency_ms: number;
  retrieved_chunks: number;
  citations: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  daily: AnalyticsPoint[];
  providers: ProviderStats[];
}

export interface EvaluationSummary {
  total?: number;
  passed?: number;
  categories?: Record<string, { total: number; passed: number; pass_rate: number }>;
  status_counts?: Record<string, number>;
  [metric: string]: unknown;
}

export interface EvaluationRunSummary {
  id: number;
  status: "completed" | "incomplete";
  dataset_name: string;
  user_id: number | null;
  document_id: number | null;
  collection_id: number | null;
  provider: string;
  model: string;
  summary: EvaluationSummary;
  case_errors: Array<Record<string, string>>;
  regression_failures: string[];
  max_regression: number | null;
  created_at: string;
}

export interface EvaluationRun extends EvaluationRunSummary {
  results: Array<Record<string, unknown>>;
}

export interface RagSettings {
  provider: "gemini" | "ollama";
  fallback_provider: "" | "gemini" | "ollama";
  ollama_model: string;
  gemini_model: string;
  retrieval_top_k: number;
  candidate_multiplier: number;
  rerank_limit: number;
  minimum_reranker_score: number;
  max_context_chars: number;
  temperature: number;
  max_output_tokens: number;
  chunk_size: number;
  chunk_overlap: number;
  input_cost_per_1k_tokens_usd: number;
  output_cost_per_1k_tokens_usd: number;
  query_cache_enabled: boolean;
  query_cache_ttl_seconds: number;
  embedding_model: string;
  embedding_dimensions: number;
}

export async function getAdminSummary(): Promise<AdminSummary> {
  const response = await apiFetch("/admin/summary");
  return response.json();
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await apiFetch("/admin/users");
  return response.json();
}

export async function updateAdminUserStatus(id: number, is_active: boolean): Promise<AdminUser> {
  const response = await apiFetch(`/admin/users/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
  return response.json();
}

export async function getAdminAnalytics(days = 30): Promise<AdminAnalytics> {
  const response = await apiFetch(`/admin/analytics?days=${days}`);
  return response.json();
}

export async function getEvaluationRuns(): Promise<EvaluationRunSummary[]> {
  const response = await apiFetch("/admin/evaluations?limit=100");
  return response.json();
}

export async function getEvaluationRun(id: number): Promise<EvaluationRun> {
  const response = await apiFetch(`/admin/evaluations/${id}`);
  return response.json();
}

export async function getRagSettings(): Promise<RagSettings> {
  const response = await apiFetch("/admin/settings/rag");
  return response.json();
}

export async function updateRagSettings(settings: Partial<RagSettings>): Promise<RagSettings> {
  const response = await apiFetch("/admin/settings/rag", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  return response.json();
}
