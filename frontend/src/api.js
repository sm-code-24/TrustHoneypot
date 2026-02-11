const API_BASE = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "default-hackathon-key-2026";

const headers = () => ({
  "Content-Type": "application/json",
  "x-api-key": API_KEY,
});

export async function sendMessage(
  sessionId,
  messageText,
  conversationHistory = [],
  responseMode = "rule_based",
) {
  const res = await fetch(`${API_BASE}/honeypot`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      sessionId,
      message: { sender: "scammer", text: messageText },
      conversationHistory,
      response_mode: responseMode,
    }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchSessions(limit = 50) {
  const res = await fetch(`${API_BASE}/sessions?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchSessionDetail(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchPatterns() {
  const res = await fetch(`${API_BASE}/patterns`, { headers: headers() });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchCallbacks(limit = 50) {
  const res = await fetch(`${API_BASE}/callbacks?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchSystemStatus() {
  const res = await fetch(`${API_BASE}/system/status`, { headers: headers() });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
