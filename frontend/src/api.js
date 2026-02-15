const API_BASE = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "default-api-key-2026";

/* eslint-disable no-console */
const logErr = (tag, ...args) => console.error(`[TH:${tag}]`, ...args);

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
  const payload = {
    sessionId,
    message: { sender: "scammer", text: messageText },
    conversationHistory,
    response_mode: responseMode,
  };

  const res = await fetch(`${API_BASE}/honeypot`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errBody = await res.text().catch(() => "");
    logErr("SEND", `HTTP ${res.status} — ${errBody.slice(0, 300)}`);
    throw new Error(`API error: ${res.status} — ${errBody.slice(0, 200)}`);
  }

  return await res.json();
}

export async function fetchSessions(limit = 50) {
  const res = await fetch(`${API_BASE}/sessions?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchSessions failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  return data.sessions || [];
}

export async function fetchSessionDetail(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchSessionDetail failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  return await res.json();
}

export async function fetchPatterns() {
  const res = await fetch(`${API_BASE}/patterns`, { headers: headers() });
  if (!res.ok) {
    logErr("API", `fetchPatterns failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  return await res.json();
}

export async function fetchCallbacks(limit = 50) {
  const res = await fetch(`${API_BASE}/callbacks?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchCallbacks failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  return data.callbacks || [];
}

export async function fetchScenarios() {
  const res = await fetch(`${API_BASE}/scenarios`, { headers: headers() });
  if (!res.ok) {
    logErr("API", `fetchScenarios failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  return data.scenarios || [];
}

// Fetch a single scenario including its messages (for step-by-step simulation)
export async function fetchScenarioDetail(scenarioId) {
  const res = await fetch(
    `${API_BASE}/scenarios/${encodeURIComponent(scenarioId)}`,
    {
      headers: headers(),
    },
  );
  if (!res.ok) {
    logErr("API", `fetchScenarioDetail failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  return await res.json();
}

export async function runSimulation(scenarioId, responseMode = "rule_based") {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({
      scenario_id: scenarioId,
      response_mode: responseMode,
    }),
  });
  if (!res.ok) {
    const errBody = await res.text().catch(() => "");
    logErr("SIM", `HTTP ${res.status} — ${errBody.slice(0, 300)}`);
    throw new Error(`API error: ${res.status} — ${errBody.slice(0, 200)}`);
  }
  return await res.json();
}

// ─── Intelligence Registry (v2.2) ────────────────────────────────────────

export async function fetchIntelligenceRegistry(
  type = null,
  risk = null,
  limit = 100,
) {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  if (risk) params.set("risk", risk);
  params.set("limit", String(limit));
  const res = await fetch(`${API_BASE}/intelligence/registry?${params}`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export async function fetchIdentifierDetail(identifier) {
  const res = await fetch(
    `${API_BASE}/intelligence/registry/${encodeURIComponent(identifier)}`,
    {
      headers: headers(),
    },
  );
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export async function fetchPatternCorrelation() {
  const res = await fetch(`${API_BASE}/intelligence/patterns`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export async function fetchSessionAnalysis(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/analysis`, {
    headers: headers(),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return await res.json();
}

export function getExportUrl(
  type = null,
  risk = null,
  dateFrom = null,
  dateTo = null,
) {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  if (risk) params.set("risk", risk);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  return `${API_BASE}/intelligence/export?${params}`;
}

export async function downloadExport(
  type = null,
  risk = null,
  dateFrom = null,
  dateTo = null,
) {
  const url = getExportUrl(type, risk, dateFrom, dateTo);
  const res = await fetch(url, { headers: headers() });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `trusthoneypot_intelligence_${new Date().toISOString().slice(0, 10)}.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}
