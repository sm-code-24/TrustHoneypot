const API_BASE = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "default-hackathon-key-2026";

/* eslint-disable no-console */
const log = (tag, ...args) => console.log(`[TH:${tag}]`, ...args);
const logWarn = (tag, ...args) => console.warn(`[TH:${tag}]`, ...args);
const logErr = (tag, ...args) => console.error(`[TH:${tag}]`, ...args);

// Log config on load
log("CONFIG", "API_BASE =", API_BASE || "(empty — same origin)");
log("CONFIG", "API_KEY set =", !!API_KEY, "length =", API_KEY.length);

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
  log(
    "SEND",
    `mode=${responseMode} session=${sessionId.slice(0, 8)} histLen=${conversationHistory.length}`,
  );
  log("SEND", "payload →", JSON.stringify(payload).slice(0, 500));

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

  const data = await res.json();

  // ── Callback debug ──
  log(
    "CALLBACK",
    `sent=${data.callback_sent}  scam=${data.scam_detected}  riskScore=${data.risk_score}  riskLevel=${data.risk_level}`,
  );
  log("CALLBACK", "intelCounts →", JSON.stringify(data.intelligence_counts));
  if (!data.callback_sent) {
    const ic = data.intelligence_counts || {};
    const hasIntel =
      (ic.upiIds || 0) +
        (ic.phoneNumbers || 0) +
        (ic.bankAccounts || 0) +
        (ic.phishingLinks || 0) >
      0;
    logWarn(
      "CALLBACK",
      `NOT SENT — reasons: scam=${data.scam_detected}, hasIntel=${hasIntel}, check totalMessages>=3 on backend`,
    );
  }

  // ── LLM debug ──
  log("LLM", `requested=${responseMode}  actual_source=${data.reply_source}`);
  if (responseMode === "llm") {
    if (data.reply_source === "rule_based") {
      logWarn(
        "LLM",
        "⚠ Backend returned rule_based even though LLM was requested — LLM likely disabled on server",
      );
    } else if (data.reply_source === "rule_based_fallback") {
      logWarn(
        "LLM",
        "⚠ LLM fallback — LLM was attempted but failed (timeout/error/unsafe)",
      );
    } else if (data.reply_source === "llm") {
      log("LLM", "✓ LLM reply successfully generated");
    }
  }

  log("SEND", "response →", JSON.stringify(data).slice(0, 600));
  return data;
}

export async function fetchSessions(limit = 50) {
  log("API", "fetchSessions", { limit });
  const res = await fetch(`${API_BASE}/sessions?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchSessions failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  log("API", `fetchSessions → ${(data.sessions || []).length} sessions`);
  return data.sessions || [];
}

export async function fetchSessionDetail(sessionId) {
  log("API", "fetchSessionDetail", sessionId.slice(0, 8));
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchSessionDetail failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  log("API", "fetchSessionDetail →", JSON.stringify(data).slice(0, 300));
  return data;
}

export async function fetchPatterns() {
  log("API", "fetchPatterns");
  const res = await fetch(`${API_BASE}/patterns`, { headers: headers() });
  if (!res.ok) {
    logErr("API", `fetchPatterns failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  log("API", "fetchPatterns →", JSON.stringify(data).slice(0, 300));
  return data;
}

export async function fetchCallbacks(limit = 50) {
  log("API", "fetchCallbacks", { limit });
  const res = await fetch(`${API_BASE}/callbacks?limit=${limit}`, {
    headers: headers(),
  });
  if (!res.ok) {
    logErr("API", `fetchCallbacks failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  log("API", `fetchCallbacks → ${(data.callbacks || []).length} callbacks`);
  return data.callbacks || [];
}

export async function fetchSystemStatus() {
  log("API", "fetchSystemStatus");
  const res = await fetch(`${API_BASE}/system/status`, { headers: headers() });
  if (!res.ok) {
    logErr("API", `fetchSystemStatus failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  // Log LLM & DB status for debugging
  log("STATUS", "llm →", JSON.stringify(data.llm));
  log("STATUS", "database →", JSON.stringify(data.database));
  if (data.llm && !data.llm.available) {
    logWarn(
      "STATUS",
      "⚠ LLM NOT AVAILABLE:",
      `api_key_set=${data.llm.api_key_set}`,
      `httpx=${data.llm.httpx_installed}`,
      `model=${data.llm.model}`,
    );
  }
  if (data.database && !data.database.connected) {
    logWarn(
      "STATUS",
      "⚠ DB NOT CONNECTED:",
      `uri_set=${data.database.uri_set}`,
      `pymongo=${data.database.pymongo_installed}`,
    );
  }
  return data;
}

export async function fetchScenarios() {
  log("API", "fetchScenarios");
  const res = await fetch(`${API_BASE}/scenarios`, { headers: headers() });
  if (!res.ok) {
    logErr("API", `fetchScenarios failed: HTTP ${res.status}`);
    throw new Error(`API error: ${res.status}`);
  }
  const data = await res.json();
  log("API", `fetchScenarios → ${(data.scenarios || []).length} scenarios`);
  return data.scenarios || [];
}

export async function runSimulation(scenarioId, responseMode = "rule_based") {
  log("SIM", `scenario=${scenarioId} mode=${responseMode}`);
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
  const data = await res.json();
  log(
    "SIM",
    `result → ${(data.conversation || []).length} messages, callback=${data.final_analysis?.callback_sent}`,
  );
  return data;
}
