export async function apiFetch<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api/proxy${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    const detail = Array.isArray(err.detail)
      ? err.detail.map((d: any) => d.msg).join("; ") // FastAPI validation errors are arrays
      : err.detail;
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Downloads a binary response (CSV/PDF export) and triggers a browser save. */
export async function apiDownload(endpoint: string, filename: string): Promise<void> {
  const res = await fetch(`/api/proxy${endpoint}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Download failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
