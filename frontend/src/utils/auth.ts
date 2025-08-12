const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5089/api";

export function getToken(): string | null {
  return localStorage.getItem("civic_token");
}

export function isStaff(): boolean {
  return localStorage.getItem("is_staff") === "true";
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || "Login failed");
  }
  const data = await res.json();
  localStorage.setItem("civic_token", data.token);
  localStorage.setItem("is_staff", String(data.is_staff));
}

export function logout() {
  localStorage.removeItem("civic_token");
  localStorage.removeItem("is_staff");
}
