import { useState, useEffect } from "react";
import { fetchSessions, fetchSystemStatus } from "../api";
import {
  BarChart3,
  Hash,
  Phone,
  CreditCard,
  Link2,
  Mail,
  AlertTriangle,
  TrendingUp,
  Clock,
  Loader2,
} from "lucide-react";

function StatCard({ icon: Icon, label, value, color = "blue" }) {
  const colors = {
    blue: "from-blue-500/10 to-blue-600/5 border-blue-500/15 text-blue-400",
    purple:
      "from-purple-500/10 to-purple-600/5 border-purple-500/15 text-purple-400",
    emerald:
      "from-emerald-500/10 to-emerald-600/5 border-emerald-500/15 text-emerald-400",
    amber:
      "from-amber-500/10 to-amber-600/5 border-amber-500/15 text-amber-400",
    red: "from-red-500/10 to-red-600/5 border-red-500/15 text-red-400",
  };
  const c = colors[color] || colors.blue;
  return (
    <div
      className={`glass rounded-xl p-4 bg-gradient-to-br ${c} border card-hover`}>
      <div className="flex items-center justify-between mb-2">
        <Icon size={16} className="opacity-80" />
        <span
          className="text-2xl font-bold"
          style={{ color: "var(--text-heading)" }}>
          {value}
        </span>
      </div>
      <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
        {label}
      </span>
    </div>
  );
}

export default function IntelligenceView() {
  const [sessions, setSessions] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchSessions(100).catch(() => []),
      fetchSystemStatus().catch(() => null),
    ])
      .then(([s, st]) => {
        setSessions(Array.isArray(s) ? s : []);
        setStatus(st);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  // Aggregate from session data
  const totalSessions = sessions.length;
  const scamSessions = sessions.filter((s) => s.scam_confirmed).length;
  const totalIntel = sessions.reduce((acc, s) => {
    const ic = s.intelligence_counts || {};
    return acc + Object.values(ic).reduce((a, b) => a + (b || 0), 0);
  }, 0);
  const avgMessages =
    totalSessions ?
      Math.round(
        sessions.reduce((a, s) => a + (s.message_count || 0), 0) /
          totalSessions,
      )
    : 0;

  // Intelligence type breakdown
  const intelByType = {};
  sessions.forEach((s) => {
    Object.entries(s.intelligence_counts || {}).forEach(([k, v]) => {
      intelByType[k] = (intelByType[k] || 0) + (v || 0);
    });
  });

  const intelIcons = {
    upiIds: Hash,
    phoneNumbers: Phone,
    bankAccounts: CreditCard,
    phishingLinks: Link2,
    emails: Mail,
  };

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <BarChart3 size={18} className="text-blue-400" />
        <h2
          className="text-lg font-semibold"
          style={{ color: "var(--text-heading)" }}>
          Intelligence Overview
        </h2>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          icon={TrendingUp}
          label="Total Sessions"
          value={totalSessions}
          color="blue"
        />
        <StatCard
          icon={AlertTriangle}
          label="Scams Detected"
          value={scamSessions}
          color="red"
        />
        <StatCard
          icon={Hash}
          label="Intel Extracted"
          value={totalIntel}
          color="emerald"
        />
        <StatCard
          icon={Clock}
          label="Avg Messages"
          value={avgMessages}
          color="amber"
        />
      </div>

      {/* Intel by type */}
      <div className="glass rounded-xl p-5">
        <h3
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--text-heading)" }}>
          Intelligence by Type
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Object.entries(intelByType).map(([key, count]) => {
            const Icon = intelIcons[key] || Hash;
            return (
              <div
                key={key}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg border"
                style={{
                  background: "var(--bg-tertiary)",
                  borderColor: "var(--border-primary)",
                }}>
                <Icon size={14} className="text-blue-400" />
                <div>
                  <div
                    className="text-sm font-medium"
                    style={{ color: "var(--text-heading)" }}>
                    {count}
                  </div>
                  <div
                    className="text-[11px]"
                    style={{ color: "var(--text-tertiary)" }}>
                    {key.replace(/([A-Z])/g, " $1").trim()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent sessions table */}
      <div className="glass rounded-xl overflow-hidden">
        <div
          className="px-5 py-3 border-b"
          style={{ borderColor: "var(--border-primary)" }}>
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Recent Sessions
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr
                className="text-xs border-b"
                style={{
                  color: "var(--text-tertiary)",
                  borderColor: "var(--border-primary)",
                }}>
                <th className="text-left px-5 py-2.5 font-medium">Session</th>
                <th className="text-left px-5 py-2.5 font-medium">Scam Type</th>
                <th className="text-center px-5 py-2.5 font-medium">Msgs</th>
                <th className="text-center px-5 py-2.5 font-medium">Risk</th>
                <th className="text-center px-5 py-2.5 font-medium hidden sm:table-cell">
                  Intel
                </th>
              </tr>
            </thead>
            <tbody>
              {sessions.slice(0, 15).map((s) => {
                const intelCount = Object.values(
                  s.intelligence_counts || {},
                ).reduce((a, b) => a + b, 0);
                const riskColors = {
                  critical: "text-red-400 bg-red-500/10",
                  high: "text-orange-400 bg-orange-500/10",
                  medium: "text-amber-400 bg-amber-500/10",
                  low: "text-emerald-400 bg-emerald-500/10",
                };
                const rc =
                  riskColors[s.risk_level] || "text-slate-400 bg-slate-800/40";
                return (
                  <tr
                    key={s.session_id}
                    className="border-b transition-colors"
                    style={{ borderColor: "var(--border-primary)" }}>
                    <td
                      className="px-5 py-2.5 font-mono text-xs"
                      style={{ color: "var(--text-secondary)" }}>
                      {(s.session_id || "").slice(0, 8)}
                    </td>
                    <td
                      className="px-5 py-2.5 text-xs"
                      style={{ color: "var(--text-secondary)" }}>
                      {(s.scam_type || "unknown").replace(/_/g, " ")}
                    </td>
                    <td
                      className="px-5 py-2.5 text-center text-xs"
                      style={{ color: "var(--text-secondary)" }}>
                      {s.message_count || 0}
                    </td>
                    <td className="px-5 py-2.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium ${rc}`}>
                        {(s.risk_level || "–").toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-2.5 text-center text-xs text-blue-400 font-medium hidden sm:table-cell">
                      {intelCount}
                    </td>
                  </tr>
                );
              })}
              {sessions.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-8 text-center text-sm text-slate-500">
                    No sessions recorded yet. Start a session from the Session
                    tab.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
