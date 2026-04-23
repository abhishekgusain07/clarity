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

export async function getHealth(): Promise<{ status: string; version: string }> {
  return apiFetch("/health");
}
