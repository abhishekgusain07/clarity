import type {
  ApproveRequest,
  CreateApplicationResponse,
  DashboardStats,
  HealthResponse,
  ListApplicationsResponse,
  OutcomeUpdate,
  OutcomeUpdateResponse,
  RunResponse,
} from "#/lib/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API ${path} failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch("/health");
}

export async function createApplication(
  jdUrl: string,
): Promise<CreateApplicationResponse> {
  return apiFetch("/applications", {
    method: "POST",
    body: JSON.stringify({ jd_url: jdUrl }),
  });
}

export async function getRun(runId: string): Promise<RunResponse> {
  return apiFetch(`/runs/${runId}`);
}

export async function approveRun(
  runId: string,
  body: ApproveRequest,
): Promise<{ run_id: string; new_state: string }> {
  return apiFetch(`/runs/${runId}/approve`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function sseUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/events`;
}

export async function listApplications(): Promise<ListApplicationsResponse> {
  return apiFetch("/applications");
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiFetch("/dashboard/stats");
}

export async function updateOutcome(
  applicationId: string,
  body: OutcomeUpdate,
): Promise<OutcomeUpdateResponse> {
  return apiFetch(`/applications/${applicationId}/outcome`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
