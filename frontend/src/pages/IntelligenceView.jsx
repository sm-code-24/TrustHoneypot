import { useState, useEffect } from "react";
import {
  fetchIntelligenceRegistry,
  fetchIdentifierDetail,
  fetchSessions,
  downloadExport,
} from "../api";
import {
  BarChart3,
  Hash,
  Phone,
  CreditCard,
  Link2,
  Mail,
  AlertTriangle,
  TrendingUp,
  Loader2,
  X,
  Download,
  Search,
  Filter,
  Eye,
  RefreshCw,
  Shield,
} from "lucide-react";

const TYPE_META = {
  upi: {
    icon: Hash,
    label: "UPI IDs",
    color: "purple",
    border: "border-purple-500/20",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
  },
  phone: {
    icon: Phone,
    label: "Phone Numbers",
    color: "blue",
    border: "border-blue-500/20",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
  },
  bank_account: {
    icon: CreditCard,
    label: "Bank Accounts",
    color: "emerald",
    border: "border-emerald-500/20",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
  },
  link: {
    icon: Link2,
    label: "Phishing Links",
    color: "red",
    border: "border-red-500/20",
    bg: "bg-red-500/10",
    text: "text-red-400",
  },
  email: {
    icon: Mail,
    label: "Emails",
    color: "amber",
    border: "border-amber-500/20",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
  },
};

const RISK_COLORS = {
  critical: "text-red-400 bg-red-500/10 border-red-500/20",
  high: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

function StatCard({ icon: Icon, label, value, color = "blue" }) {
  const iconColors = {
    blue: "text-blue-500",
    purple: "text-purple-500",
    emerald: "text-emerald-500",
    amber: "text-amber-500",
    red: "text-red-500",
  };
  const borderColors = {
    blue: "border-blue-500/20",
    purple: "border-purple-500/20",
    emerald: "border-emerald-500/20",
    amber: "border-amber-500/20",
    red: "border-red-500/20",
  };
  return (
    <div
      className={`glass rounded-xl p-4 ${borderColors[color] || borderColors.blue} border card-hover`}
      style={{ background: "var(--bg-card)" }}>
      <div className="flex items-center justify-between mb-2">
        <Icon size={16} className={iconColors[color] || iconColors.blue} />
        <span
          className="text-2xl font-bold"
          style={{ color: "var(--text-heading)" }}>
          {value}
        </span>
      </div>
      <span
        className="text-xs font-medium"
        style={{ color: "var(--text-secondary)" }}>
        {label}
      </span>
    </div>
  );
}

function DetailModal({ identifier, detail, onClose }) {
  if (!detail) return null;
  const meta = TYPE_META[detail.type] || TYPE_META.upi;
  const Icon = meta.icon;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className="relative w-full max-w-lg rounded-2xl border p-6 space-y-4 animate-fade-in"
        style={{
          background: "var(--bg-primary)",
          borderColor: "var(--border-primary)",
        }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-lg ${meta.bg} flex items-center justify-center`}>
              <Icon size={16} className={meta.text} />
            </div>
            <div>
              <h3
                className="text-sm font-semibold"
                style={{ color: "var(--text-heading)" }}>
                Identifier Detail
              </h3>
              <span
                className="text-[10px] font-mono"
                style={{ color: "var(--text-muted)" }}>
                {detail.type?.toUpperCase()}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-red-500/10 transition-colors"
            style={{ color: "var(--text-tertiary)" }}>
            <X size={16} />
          </button>
        </div>
        <div
          className="font-mono text-sm px-3 py-2 rounded-lg border"
          style={{
            background: "var(--bg-tertiary)",
            borderColor: "var(--border-primary)",
            color: "var(--text-heading)",
          }}>
          {detail.masked_value || identifier}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div
            className="rounded-lg p-3 border"
            style={{
              background: "var(--bg-tertiary)",
              borderColor: "var(--border-primary)",
            }}>
            <div
              className="text-[10px] mb-1"
              style={{ color: "var(--text-muted)" }}>
              Times Seen
            </div>
            <div
              className="text-lg font-bold"
              style={{ color: "var(--text-heading)" }}>
              {detail.frequency || 1}
            </div>
          </div>
          <div
            className="rounded-lg p-3 border"
            style={{
              background: "var(--bg-tertiary)",
              borderColor: "var(--border-primary)",
            }}>
            <div
              className="text-[10px] mb-1"
              style={{ color: "var(--text-muted)" }}>
              Confidence
            </div>
            <div
              className="text-lg font-bold"
              style={{ color: "var(--text-heading)" }}>
              {((detail.confidence || 0) * 100).toFixed(0)}%
            </div>
          </div>
          <div
            className="rounded-lg p-3 border"
            style={{
              background: "var(--bg-tertiary)",
              borderColor: "var(--border-primary)",
            }}>
            <div
              className="text-[10px] mb-1"
              style={{ color: "var(--text-muted)" }}>
              Recurring
            </div>
            <div
              className={`text-lg font-bold ${detail.is_recurring ? "text-red-400" : "text-emerald-400"}`}>
              {detail.is_recurring ? "Yes" : "No"}
            </div>
          </div>
          <div
            className="rounded-lg p-3 border"
            style={{
              background: "var(--bg-tertiary)",
              borderColor: "var(--border-primary)",
            }}>
            <div
              className="text-[10px] mb-1"
              style={{ color: "var(--text-muted)" }}>
              Risk Level
            </div>
            <span
              className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${RISK_COLORS[detail.risk_level] || ""}`}>
              {(detail.risk_level || "unknown").toUpperCase()}
            </span>
          </div>
        </div>
        {detail.associated_sessions &&
          detail.associated_sessions.length > 0 && (
            <div>
              <h4
                className="text-xs font-semibold mb-2"
                style={{ color: "var(--text-heading)" }}>
                Associated Sessions
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {detail.associated_sessions.map((sid) => (
                  <span
                    key={sid}
                    className="px-2 py-0.5 rounded text-[10px] font-mono border"
                    style={{
                      color: "var(--text-secondary)",
                      borderColor: "var(--border-primary)",
                      background: "var(--bg-tertiary)",
                    }}>
                    {sid.slice(0, 8)}
                  </span>
                ))}
              </div>
            </div>
          )}
        {detail.fraud_types && detail.fraud_types.length > 0 && (
          <div>
            <h4
              className="text-xs font-semibold mb-2"
              style={{ color: "var(--text-heading)" }}>
              Fraud Types
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {detail.fraud_types.map((ft) => (
                <span
                  key={ft}
                  className="px-2 py-0.5 rounded text-[10px] font-bold border border-red-500/20 text-red-400 bg-red-500/10">
                  {ft}
                </span>
              ))}
            </div>
          </div>
        )}
        {detail.first_seen && (
          <div
            className="flex items-center gap-4 text-[10px]"
            style={{ color: "var(--text-muted)" }}>
            <span>
              First: {new Date(detail.first_seen).toLocaleDateString("en-IN")}
            </span>
            {detail.last_seen && (
              <span>
                Last: {new Date(detail.last_seen).toLocaleDateString("en-IN")}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IntelligenceView() {
  const [registry, setRegistry] = useState([]);
  const [stats, setStats] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState(null);
  const [riskFilter, setRiskFilter] = useState(null);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      fetchIntelligenceRegistry(typeFilter, riskFilter).catch(() => ({
        identifiers: [],
        stats: {},
      })),
      fetchSessions(100).catch(() => []),
    ])
      .then(([reg, sess]) => {
        setRegistry(reg.identifiers || []);
        setStats(reg.stats || {});
        setSessions(Array.isArray(sess) ? sess : []);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [typeFilter, riskFilter]);

  const openDetail = async (identifier) => {
    setSelectedId(identifier);
    setDetailLoading(true);
    try {
      const d = await fetchIdentifierDetail(identifier);
      setDetail(d);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadExport(typeFilter, riskFilter);
    } catch {
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  const totalSessions = sessions.length;
  const scamSessions = sessions.filter((s) => s.scam_confirmed).length;
  const totalIdentifiers = stats?.total_identifiers || registry.length;
  const recurringCount =
    stats?.recurring_count || registry.filter((r) => r.is_recurring).length;

  const filtered = registry.filter((r) => {
    if (search) {
      const q = search.toLowerCase();
      if (!(r.masked_value || r.identifier || "").toLowerCase().includes(q))
        return false;
    }
    return true;
  });

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-blue-400" />
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Intelligence Registry
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="p-2 rounded-lg transition-colors hover:bg-blue-500/10"
            style={{ color: "var(--text-tertiary)" }}
            title="Refresh">
            <RefreshCw size={14} />
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-emerald-600/80 to-teal-600/80 text-white hover:shadow-lg hover:shadow-emerald-500/20 disabled:opacity-40 transition-all">
            {exporting ?
              <Loader2 size={12} className="animate-spin" />
            : <Download size={12} />}
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
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
          icon={Shield}
          label="Identifiers Tracked"
          value={totalIdentifiers}
          color="emerald"
        />
        <StatCard
          icon={Eye}
          label="Recurring Threats"
          value={recurringCount}
          color="amber"
        />
      </div>

      {/* Type Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        <Filter size={13} style={{ color: "var(--text-muted)" }} />
        <button
          onClick={() => setTypeFilter(null)}
          className={`px-3 py-1 rounded-full text-[11px] font-medium border transition-all ${!typeFilter ? "bg-blue-500/15 text-blue-400 border-blue-500/30" : "border-transparent"}`}
          style={typeFilter ? { color: "var(--text-tertiary)" } : undefined}>
          All
        </button>
        {Object.entries(TYPE_META).map(([key, meta]) => {
          const Icon = meta.icon;
          const active = typeFilter === key;
          return (
            <button
              key={key}
              onClick={() => setTypeFilter(active ? null : key)}
              className={`flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-medium border transition-all ${active ? `${meta.bg} ${meta.text} ${meta.border}` : "border-transparent"}`}
              style={!active ? { color: "var(--text-tertiary)" } : undefined}>
              <Icon size={11} />
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* Risk Filter + Search */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5">
          {["critical", "high", "medium", "low"].map((r) => (
            <button
              key={r}
              onClick={() => setRiskFilter(riskFilter === r ? null : r)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold border transition-all ${riskFilter === r ? RISK_COLORS[r] : "border-transparent"}`}
              style={
                riskFilter !== r ? { color: "var(--text-muted)" } : undefined
              }>
              {r.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="flex-1 min-w-[200px] flex items-center gap-2 glass rounded-lg px-3 py-1.5">
          <Search size={13} style={{ color: "var(--text-muted)" }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search identifiers..."
            className="flex-1 bg-transparent text-xs outline-none"
            style={{ color: "var(--text-primary)" }}
          />
        </div>
      </div>

      {/* Registry Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div
          className="px-5 py-3 border-b flex items-center justify-between"
          style={{ borderColor: "var(--border-primary)" }}>
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Tracked Identifiers
          </h3>
          <span
            className="text-[10px] font-mono"
            style={{ color: "var(--text-muted)" }}>
            {filtered.length} results
          </span>
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
                <th className="text-left px-5 py-2.5 font-medium">Type</th>
                <th className="text-left px-5 py-2.5 font-medium">
                  Identifier
                </th>
                <th className="text-center px-5 py-2.5 font-medium">Seen</th>
                <th className="text-center px-5 py-2.5 font-medium">Risk</th>
                <th className="text-center px-5 py-2.5 font-medium hidden sm:table-cell">
                  Recurring
                </th>
                <th className="text-center px-5 py-2.5 font-medium">
                  Confidence
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-8 text-center text-sm"
                    style={{ color: "var(--text-muted)" }}>
                    No identifiers found. Engage scammers to populate the
                    intelligence registry.
                  </td>
                </tr>
              )}
              {filtered.map((r, i) => {
                const meta = TYPE_META[r.type] || TYPE_META.upi;
                const Icon = meta.icon;
                return (
                  <tr
                    key={i}
                    onClick={() => openDetail(r.identifier || r.masked_value)}
                    className="border-b transition-colors cursor-pointer hover:bg-blue-500/5"
                    style={{ borderColor: "var(--border-primary)" }}>
                    <td className="px-5 py-2.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${meta.bg} ${meta.text} ${meta.border}`}>
                        <Icon size={10} />
                        {(r.type || "").toUpperCase()}
                      </span>
                    </td>
                    <td
                      className="px-5 py-2.5 font-mono text-xs"
                      style={{ color: "var(--text-secondary)" }}>
                      {r.masked_value || r.identifier}
                    </td>
                    <td
                      className="px-5 py-2.5 text-center text-xs font-medium"
                      style={{ color: "var(--text-heading)" }}>
                      {r.frequency || 1}
                    </td>
                    <td className="px-5 py-2.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${RISK_COLORS[r.risk_level] || ""}`}>
                        {(r.risk_level || "–").toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-2.5 text-center hidden sm:table-cell">
                      {r.is_recurring ?
                        <span className="text-red-400 text-xs font-bold">
                          YES
                        </span>
                      : <span
                          style={{ color: "var(--text-muted)" }}
                          className="text-xs">
                          —
                        </span>
                      }
                    </td>
                    <td
                      className="px-5 py-2.5 text-center text-xs font-medium"
                      style={{ color: "var(--text-secondary)" }}>
                      {((r.confidence || 0) * 100).toFixed(0)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Sessions */}
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
                <th className="text-left px-5 py-2.5 font-medium">
                  Fraud Type
                </th>
                <th className="text-center px-5 py-2.5 font-medium">Msgs</th>
                <th className="text-center px-5 py-2.5 font-medium">Risk</th>
                <th className="text-center px-5 py-2.5 font-medium hidden sm:table-cell">
                  Intel
                </th>
              </tr>
            </thead>
            <tbody>
              {sessions.slice(0, 10).map((s) => {
                const intelCount = Object.values(
                  s.intelligence_counts || {},
                ).reduce((a, b) => a + b, 0);
                const rc = RISK_COLORS[s.risk_level] || "";
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
                    <td className="px-5 py-2.5">
                      <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold border border-red-500/20 text-red-400 bg-red-500/10">
                        {(s.fraud_type || s.scam_type || "unknown")
                          .replace(/_/g, " ")
                          .toUpperCase()}
                      </span>
                    </td>
                    <td
                      className="px-5 py-2.5 text-center text-xs"
                      style={{ color: "var(--text-secondary)" }}>
                      {s.message_count || 0}
                    </td>
                    <td className="px-5 py-2.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium border ${rc}`}
                        style={
                          !rc ? { color: "var(--text-tertiary)" } : undefined
                        }>
                        {(s.risk_level || "–").toUpperCase()}
                      </span>
                    </td>
                    <td className="px-5 py-2.5 text-center text-xs text-blue-500 font-medium hidden sm:table-cell">
                      {intelCount}
                    </td>
                  </tr>
                );
              })}
              {sessions.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-8 text-center text-sm"
                    style={{ color: "var(--text-muted)" }}>
                    No sessions recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedId && !detailLoading && detail && (
        <DetailModal
          identifier={selectedId}
          detail={detail}
          onClose={() => {
            setSelectedId(null);
            setDetail(null);
          }}
        />
      )}
      {selectedId && detailLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setSelectedId(null)}
          />
          <Loader2 className="relative animate-spin text-blue-400" size={32} />
        </div>
      )}
    </div>
  );
}
