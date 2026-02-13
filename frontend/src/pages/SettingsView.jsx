import { useState, useEffect } from "react";
import { fetchSystemStatus } from "../api";
import {
  Settings,
  Server,
  Brain,
  Database,
  CheckCircle,
  XCircle,
  Loader2,
  Lock,
  Shield,
  Clock,
} from "lucide-react";

function StatusCard({ icon: Icon, title, connected, detail, color = "blue" }) {
  const iconColors = {
    blue: "text-blue-500",
    purple: "text-purple-500",
    emerald: "text-emerald-500",
  };
  const borderColors = {
    blue: "border-blue-500/15",
    purple: "border-purple-500/15",
    emerald: "border-emerald-500/15",
  };
  const borderColor = connected ? borderColors[color] || borderColors.blue : "";
  const iconColor = connected ? iconColors[color] || iconColors.blue : "";
  return (
    <div
      className={`glass rounded-xl p-5 border ${borderColor} card-hover`}
      style={!connected ? { borderColor: "var(--border-primary)" } : undefined}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon
            size={16}
            className={iconColor}
            style={!connected ? { color: "var(--text-muted)" } : undefined}
          />
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            {title}
          </h3>
        </div>
        {connected ?
          <div className="flex items-center gap-1 text-emerald-500">
            <CheckCircle size={14} />
            <span className="text-[11px] font-medium">Connected</span>
          </div>
        : <div
            className="flex items-center gap-1"
            style={{ color: "var(--text-muted)" }}>
            <XCircle size={14} />
            <span className="text-[11px] font-medium">Unavailable</span>
          </div>
        }
      </div>
      {detail && (
        <div
          className="text-xs space-y-1"
          style={{ color: "var(--text-tertiary)" }}>
          {Object.entries(detail).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span>{k}</span>
              <span
                className="font-mono"
                style={{ color: "var(--text-secondary)" }}>
                {String(v)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SettingsView() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  const api = status?.api || {};
  const llm = status?.llm || {};
  const db = status?.db || {};

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <Settings size={18} style={{ color: "var(--text-secondary)" }} />
        <h2
          className="text-lg font-semibold"
          style={{ color: "var(--text-heading)" }}>
          System Status
        </h2>
      </div>

      {/* Status cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <StatusCard
          icon={Server}
          title="Core API"
          connected={api.status === "online"}
          color="blue"
          detail={{
            Version: api.version || "1.0.0",
            Endpoint: "/honeypot",
          }}
        />
        <StatusCard
          icon={Brain}
          title="LLM Service"
          connected={llm.available}
          color="purple"
          detail={{
            Model: llm.model || "llama-3.3-70b-versatile",
            Timeout: `${llm.timeout_ms || 1400}ms`,
            Mode: llm.available ? "Active" : "Fallback to rule-based",
          }}
        />
        <StatusCard
          icon={Database}
          title="MongoDB"
          connected={db.connected}
          color="emerald"
          detail={{
            Purpose: "Session summaries only",
            "Raw chats": "Never stored",
            Mode: db.connected ? "Active" : "In-memory only",
          }}
        />
      </div>

      {/* Architecture invariants */}
      <div className="glass rounded-xl p-6 glow-border">
        <div className="flex items-center gap-2 mb-4">
          <Lock size={16} className="text-blue-400" />
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Architecture Invariants
          </h3>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            {
              icon: Shield,
              title: "Rule-Based Authority",
              desc: "Detection and response logic are entirely rule-based. No LLM-generated decisions.",
            },
            {
              icon: Brain,
              title: "LLM Enhancement Only",
              desc: "Groq LLM rephrases agent replies for realism. Timeouts auto-fallback to rule-based.",
            },
            {
              icon: Database,
              title: "Minimal Persistence",
              desc: "MongoDB stores session summaries for pattern learning. No raw conversations stored.",
            },
            {
              icon: Clock,
              title: "Graceful Degradation",
              desc: "Both LLM and MongoDB are optional. System operates fully without either.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="flex gap-3 px-4 py-3 rounded-lg border"
              style={{
                background: "var(--bg-tertiary)",
                borderColor: "var(--border-primary)",
              }}>
              <item.icon
                size={16}
                className="text-blue-400 mt-0.5 flex-shrink-0"
              />
              <div>
                <div
                  className="text-xs font-medium"
                  style={{ color: "var(--text-heading)" }}>
                  {item.title}
                </div>
                <div
                  className="text-[11px] mt-0.5"
                  style={{ color: "var(--text-tertiary)" }}>
                  {item.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
