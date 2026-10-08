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
  created_at: string;
}

export async function getAdminSummary(): Promise<AdminSummary> {
  const response = await apiFetch("/admin/summary");
  return response.json();
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await apiFetch("/admin/users");
  return response.json();
}
