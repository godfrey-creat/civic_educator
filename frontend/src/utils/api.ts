import type { IncidentFormData } from "../types";
import { getToken } from "./auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/** helper for GET */
async function getJSON<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((opts.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

/** helper for POST */
async function postJSON<T>(
  path: string,
  body: unknown,
  opts: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((opts.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: JSON.stringify(body),
    ...opts,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

<<<<<<< HEAD
=======
/** helper for PATCH */
async function patchJSON<T>(
  path: string,
  body: unknown,
  opts: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((opts.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    ...opts,
    headers,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
export interface Citation {
  title: string;
  snippet: string;
  source_link?: string;
}

/** Chat */
export async function sendChatMessage(
  message: string,
  role: string,
  session_id?: string
) {
  return postJSON<{
    reply: string;
    citations: Citation[];
    confidence: number;
  }>("/api/chat/message", {
    message,
    role,
    session_id: session_id || crypto.randomUUID(),
  });
}

/** Create incident */
export async function createIncident(data: IncidentFormData) {
  return postJSON<{ incident_id: string; status: string; created_at: string }>(
    "/api/incidents",
    data
  );
}

/** Get incident status */
export async function getIncidentStatus(id: string) {
  return getJSON<{
    status: string;
    last_update: string;
    history: { note: string; timestamp: string }[];
  }>(`/api/incidents/${id}/status`);
}

<<<<<<< HEAD
/** Search KB */
=======
/** Search KB (staff‑only) */
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
export async function getKbDocs(query: string) {
  return getJSON<{
    results: {
      doc_id: string;
      title: string;
      snippet: string;
      score: number;
<<<<<<< HEAD
    }[];
  }>(`/api/kb/search?query=${encodeURIComponent(query)}`);
}

/** Staff: get all incidents (requires token) */
=======
      source_url?: string;
    }[];
  }>(`/api/staff/kb/search?query=${encodeURIComponent(query)}`);
}

/** Staff: get all incidents */
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
export async function getAllIncidents() {
  return getJSON<
    {
      incident_id: string;
<<<<<<< HEAD
      description: string;
      status: string;
=======
      title?: string;
      category?: string;
      priority?: string;
      description?: string;
      status: string;
      created_at?: string;
>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
      last_update: string;
    }[]
  >("/api/staff/incidents");
}

<<<<<<< HEAD
=======
/** Staff: update incident status */
export async function updateIncidentStatus(incidentId: string, status: string) {
  return patchJSON<{ incident_id: string; status: string; last_update: string }>(
    `/api/staff/incidents/${incidentId}`,
    { status }
  );
}

>>>>>>> 6e9b7e2557e0753d1a7caeffe309a05f5f14357b
/** Auth: register new user */
export async function registerUser(
  email: string,
  password: string,
  full_name = "",
  is_staff = false
) {
  return postJSON<{ access_token?: string; token_type?: string; is_staff?: boolean }>(
    "/api/auth/register",
    { email, password, full_name, is_staff }
  );
}

/** Auth: login user */
export async function loginUser(email: string, password: string) {
  return postJSON<{ access_token: string; token_type: string; is_staff?: boolean }>(
    "/api/auth/login",
    { email, password }
  );
}
