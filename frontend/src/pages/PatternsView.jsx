import { useState, useEffect } from "react";
import { fetchPatterns } from "../api";
import {
  GitBranch,
  Loader2,
  BarChart,
  AlertTriangle,
  Shield,
} from "lucide-react";

export default function PatternsView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatterns()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  const scamTypes = data?.scam_types || [];
  const riskDist = data?.risk_distribution || [];
  const topTactics = data?.top_tactics || [];
  const maxTypeCount = Math.max(...scamTypes.map((s) => s.count || 0), 1);
  const maxTacticCount = Math.max(...topTactics.map((t) => t.count || 0), 1);

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <GitBranch size={18} className="text-purple-400" />
        <h2
          className="text-lg font-semibold"
          style={{ color: "var(--text-heading)" }}>
          Scam Patterns
        </h2>
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {/* Scam types */}
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart size={14} className="text-blue-400" />
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Scam Type Distribution
            </h3>
          </div>
          <div className="space-y-3">
            {scamTypes.length === 0 && (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                No pattern data yet.
              </p>
            )}
            {scamTypes.map((s) => {
              const pct = ((s.count / maxTypeCount) * 100).toFixed(0);
              return (
                <div key={s._id} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span style={{ color: "var(--text-secondary)" }}>
                      {(s._id || "unknown").replace(/_/g, " ")}
                    </span>
                    <span style={{ color: "var(--text-tertiary)" }}>
                      {s.count}
                    </span>
                  </div>
                  <div
                    className="h-1.5 rounded-full overflow-hidden"
                    style={{ background: "var(--bar-track)" }}>
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk distribution */}
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={14} className="text-amber-400" />
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Risk Level Distribution
            </h3>
          </div>
          <div className="space-y-3">
            {riskDist.length === 0 && (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                No risk data yet.
              </p>
            )}
            {riskDist.map((r) => {
              const total =
                riskDist.reduce((a, b) => a + (b.count || 0), 0) || 1;
              const pct = ((r.count / total) * 100).toFixed(0);
              const barColors = {
                critical: "from-red-500 to-red-600",
                high: "from-orange-500 to-amber-500",
                medium: "from-amber-400 to-yellow-400",
                low: "from-emerald-500 to-teal-400",
                minimal: "from-slate-500 to-slate-400",
              };
              const bc = barColors[r._id] || barColors.minimal;
              return (
                <div key={r._id} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span style={{ color: "var(--text-secondary)" }}>
                      {(r._id || "unknown").toUpperCase()}
                    </span>
                    <span style={{ color: "var(--text-tertiary)" }}>
                      {pct}%
                    </span>
                  </div>
                  <div
                    className="h-1.5 rounded-full overflow-hidden"
                    style={{ background: "var(--bar-track)" }}>
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${bc} transition-all duration-700`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Top tactics */}
      <div className="glass rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={14} className="text-emerald-400" />
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Top Detected Tactics
          </h3>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          {topTactics.length === 0 && (
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              No tactic data yet.
            </p>
          )}
          {topTactics.map((t, i) => {
            const pct = ((t.count / maxTacticCount) * 100).toFixed(0);
            return (
              <div
                key={t._id || i}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg border"
                style={{
                  background: "var(--bg-tertiary)",
                  borderColor: "var(--border-primary)",
                }}>
                <span
                  className="text-xs font-mono w-5"
                  style={{ color: "var(--text-muted)" }}>
                  #{i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div
                    className="text-sm truncate"
                    style={{ color: "var(--text-secondary)" }}>
                    {(t._id || "unknown").replace(/_/g, " ")}
                  </div>
                  <div
                    className="h-1 rounded-full mt-1 overflow-hidden"
                    style={{ background: "var(--bar-track)" }}>
                    <div
                      className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
                <span className="text-xs font-medium text-emerald-400">
                  {t.count}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
