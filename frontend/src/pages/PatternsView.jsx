import { useState, useEffect } from "react";
import { fetchPatterns, fetchPatternCorrelation } from "../api";
import {
  GitBranch,
  Loader2,
  BarChart,
  AlertTriangle,
  Shield,
  Fingerprint,
  TrendingUp,
  Hash,
  RefreshCw,
} from "lucide-react";

export default function PatternsView() {
  const [data, setData] = useState(null);
  const [correlation, setCorrelation] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetchPatterns().catch(() => null),
      fetchPatternCorrelation().catch(() => null),
    ])
      .then(([p, c]) => {
        setData(p);
        setCorrelation(c);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
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

  const patterns = correlation?.patterns || [];
  const corrStats = correlation?.stats || {};

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch size={18} className="text-purple-400" />
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Scam Patterns & Correlations
          </h2>
        </div>
        <button
          onClick={loadData}
          className="p-2 rounded-lg transition-colors hover:bg-blue-500/10"
          style={{ color: "var(--text-tertiary)" }}
          title="Refresh">
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Correlation Stats */}
      {corrStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div
            className="glass rounded-xl p-4 border border-purple-500/20 card-hover"
            style={{ background: "var(--bg-card)" }}>
            <div className="flex items-center justify-between mb-2">
              <Fingerprint size={16} className="text-purple-500" />
              <span
                className="text-2xl font-bold"
                style={{ color: "var(--text-heading)" }}>
                {corrStats.total_patterns || 0}
              </span>
            </div>
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}>
              Total Patterns
            </span>
          </div>
          <div
            className="glass rounded-xl p-4 border border-red-500/20 card-hover"
            style={{ background: "var(--bg-card)" }}>
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle size={16} className="text-red-500" />
              <span
                className="text-2xl font-bold"
                style={{ color: "var(--text-heading)" }}>
                {corrStats.recurring_patterns || 0}
              </span>
            </div>
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}>
              Recurring Patterns
            </span>
          </div>
          <div
            className="glass rounded-xl p-4 border border-amber-500/20 card-hover"
            style={{ background: "var(--bg-card)" }}>
            <div className="flex items-center justify-between mb-2">
              <TrendingUp size={16} className="text-amber-500" />
              <span
                className="text-2xl font-bold"
                style={{ color: "var(--text-heading)" }}>
                {((corrStats.avg_similarity || 0) * 100).toFixed(0)}%
              </span>
            </div>
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}>
              Avg Similarity
            </span>
          </div>
          <div
            className="glass rounded-xl p-4 border border-blue-500/20 card-hover"
            style={{ background: "var(--bg-card)" }}>
            <div className="flex items-center justify-between mb-2">
              <Hash size={16} className="text-blue-500" />
              <span
                className="text-2xl font-bold"
                style={{ color: "var(--text-heading)" }}>
                {corrStats.unique_scam_types || scamTypes.length}
              </span>
            </div>
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}>
              Scam Types
            </span>
          </div>
        </div>
      )}

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

      {/* Pattern Correlation Section */}
      {patterns.length > 0 && (
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Fingerprint size={14} className="text-purple-400" />
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Pattern Correlations
            </h3>
          </div>
          <p className="text-xs mb-4" style={{ color: "var(--text-muted)" }}>
            Repeated tactics and fingerprints detected across multiple sessions.
          </p>
          <div className="space-y-2">
            {patterns.slice(0, 10).map((p, i) => (
              <div
                key={i}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg border"
                style={{
                  background: "var(--bg-tertiary)",
                  borderColor: "var(--border-primary)",
                }}>
                <span
                  className="text-xs font-mono w-5 text-right"
                  style={{ color: "var(--text-muted)" }}>
                  #{i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className="text-xs font-medium truncate"
                      style={{ color: "var(--text-secondary)" }}>
                      {(p.scam_type || "unknown").replace(/_/g, " ")}
                    </span>
                    {p.occurrence_count > 1 && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-500/10 text-red-400 border border-red-500/10">
                        {p.occurrence_count}x recurring
                      </span>
                    )}
                  </div>
                  {p.similarity_score != null && (
                    <div
                      className="h-1 rounded-full mt-1.5 overflow-hidden"
                      style={{ background: "var(--bar-track)" }}>
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-700"
                        style={{
                          width: `${(p.similarity_score * 100).toFixed(0)}%`,
                        }}
                      />
                    </div>
                  )}
                </div>
                <span className="text-[10px] font-mono text-purple-400 whitespace-nowrap">
                  {p.similarity_score != null ?
                    `${(p.similarity_score * 100).toFixed(0)}% sim`
                  : ""}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

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
