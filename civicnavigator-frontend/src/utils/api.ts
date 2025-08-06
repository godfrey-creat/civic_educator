import type { IncidentFormData } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:9756";

export async function sendChatMessage(message: string, role: string) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, role }),
  });

  if (!res.ok) throw new Error("Chat request failed");
  return await res.json();
}

export async function createIncident(data: IncidentFormData) {
  const res = await fetch(`${API_BASE_URL}/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit incident");
  return await res.json();
}

export async function getIncidentStatus(id: string) {
  const res = await fetch(`${API_BASE_URL}/incidents/${id}`);
  if (!res.ok) throw new Error("Not found");
  return await res.json();
}

export async function getKbDocs() {
  const res = await fetch(`${API_BASE_URL}/kb/search`);
  if (!res.ok) throw new Error("KB search failed");
  return await res.json();
}

