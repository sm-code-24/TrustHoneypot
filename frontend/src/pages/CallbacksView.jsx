import { useState, useEffect } from "react";
import { fetchCallbacks } from "../api";
import {
  Send,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  ChevronUp,
  Hash,
  Phone,
  CreditCard,
  Link2,
  Mail,
} from "lucide-react";

const FRAUD_COLORS = {
  "PAYMENT FRAUD": "text-red-400 bg-red-500/10 border-red-500/20",
  "KYC PHISHING": "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "LOTTERY SCAM": "text-purple-400 bg-purple-500/10 border-purple-500/20",
  "JOB SCAM": "text-orange-400 bg-orange-500/10 border-orange-500/20",
  IMPERSONATION: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  "GENERIC SCAM": "text-slate-400 bg-slate-500/10 border-slate-500/20",
};

function FraudBadge({ label }) {
  const cls = FRAUD_COLORS[label] || FRAUD_COLORS["GENERIC SCAM"];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${cls}`}>
      {label}
    </span>
  );
}

function IntelBadge({ icon: Icon, label, items, color }) {
  if (!items || items.length === 0) return null;
  const colorMap = {
    blue: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    red: "text-red-400 bg-red-500/10 border-red-500/20",
  };
  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md border text-[10px] font-medium ${colorMap[color] || colorMap.blue}`}>
      <Icon size={11} />
      <span>
        {label}: {items.length}
      </span>
    </div>
  );
}

function PayloadDrawer({ data, intelligence }) {
  const [open, setOpen] = useState(false);
  if (!data && !intelligence)
    return <span style={{ color: "var(--text-muted)" }}>—</span>;
  const intelEntries = [
    { key: "upiIds", icon: Hash, label: "UPI", color: "purple" },
    { key: "phoneNumbers", icon: Phone, label: "Phone", color: "blue" },
    { key: "bankAccounts", icon: CreditCard, label: "Bank", color: "emerald" },
    { key: "phishingLinks", icon: Link2, label: "Links", color: "red" },
    { key: "emails", icon: Mail, label: "Email", color: "amber" },
  ];
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-[11px] text-blue-500 hover:text-blue-600 transition-colors">
        {open ?
          <ChevronUp size={12} />
        : <ChevronDown size={12} />}
        {open ? "Hide" : "View"} payload
      </button>
      {open && (
        <div
          className="mt-2 rounded-lg p-3 border space-y-3"
          style={{
            background: "var(--bg-tertiary)",
            borderColor: "var(--border-primary)",
          }}>
          {intelligence && (
            <div className="space-y-1.5">
              <span
                className="text-[10px] font-semibold"
                style={{ color: "var(--text-heading)" }}>
                Intel Gathered
              </span>
              <div className="flex flex-wrap gap-1.5">
                {intelEntries.map(({ key, icon, label, color }) => (
                  <IntelBadge
                    key={key}
                    icon={icon}
                    label={label}
                    items={intelligence[key]}
                    color={color}
                  />
                ))}
              </div>
              <div className="space-y-0.5 mt-1">
                {intelEntries.map(({ key, label }) => {
                  const items = intelligence[key] || [];
                  if (items.length === 0) return null;
                  return (
                    <div
                      key={key}
                      className="text-[10px]"
                      style={{ color: "var(--text-tertiary)" }}>
                      <span
                        className="font-medium"
                        style={{ color: "var(--text-secondary)" }}>
                        {label}:
                      </span>{" "}
                      {items.join(", ")}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {data && (
            <div>
              <span
                className="text-[10px] font-semibold"
                style={{ color: "var(--text-heading)" }}>
                Raw Payload
              </span>
              <pre
                className="mt-1 text-[10px] font-mono rounded-lg p-2 overflow-x-auto max-h-32 whitespace-pre-wrap leading-relaxed border"
                style={{
                  color: "var(--text-secondary)",
                  background: "var(--bg-primary)",
                  borderColor: "var(--border-primary)",
                }}>
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function CallbacksView() {
  const [callbacks, setCallbacks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCallbacks(100)
      .then((d) => setCallbacks(Array.isArray(d) ? d : []))
      .catch(() => setCallbacks([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  const sent = callbacks.filter((c) => c.status === "sent").length;
  const failed = callbacks.filter((c) => c.status === "failed").length;
  const recorded = callbacks.filter((c) => c.status === "no_endpoint").length;

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <Send size={18} className="text-emerald-400" />
        <h2
          className="text-lg font-semibold"
          style={{ color: "var(--text-heading)" }}>
          Callback Reports
        </h2>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div
          className="glass rounded-xl p-4 text-center card-hover border"
          style={{ borderColor: "var(--border-primary)" }}>
          <div
            className="text-2xl font-bold"
            style={{ color: "var(--text-heading)" }}>
            {callbacks.length}
          </div>
          <div
            className="text-xs mt-1"
            style={{ color: "var(--text-tertiary)" }}>
            Total
          </div>
        </div>
        <div className="glass rounded-xl p-4 text-center card-hover border border-emerald-500/10">
          <div className="text-2xl font-bold text-emerald-400">{sent}</div>
          <div
            className="text-xs mt-1"
            style={{ color: "var(--text-tertiary)" }}>
            Sent
          </div>
        </div>
        <div className="glass rounded-xl p-4 text-center card-hover border border-amber-500/10">
          <div className="text-2xl font-bold text-amber-400">{recorded}</div>
          <div
            className="text-xs mt-1"
            style={{ color: "var(--text-tertiary)" }}>
            Recorded
          </div>
        </div>
        <div className="glass rounded-xl p-4 text-center card-hover border border-red-500/10">
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div
            className="text-xs mt-1"
            style={{ color: "var(--text-tertiary)" }}>
            Failed
          </div>
        </div>
      </div>
      <div className="glass rounded-xl overflow-hidden">
        <div
          className="px-5 py-3 border-b"
          style={{ borderColor: "var(--border-primary)" }}>
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-heading)" }}>
            Callback History
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
                <th
                  className="text-left px-3 py-3 font-semibold"
                  style={{ width: "11%" }}>
                  Session
                </th>
                <th
                  className="text-center px-2 py-3 font-semibold"
                  style={{ width: "7%" }}>
                  Status
                </th>
                <th
                  className="text-left px-3 py-3 font-semibold"
                  style={{ width: "23%" }}>
                  Fraud Type
                </th>
                <th
                  className="text-left px-3 py-3 font-semibold hidden sm:table-cell"
                  style={{ width: "24%" }}>
                  Time
                </th>
                <th
                  className="text-left px-3 py-3 font-semibold"
                  style={{ width: "35%" }}>
                  Payload
                </th>
              </tr>
            </thead>
            <tbody>
              {callbacks.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-5 py-8 text-center text-sm"
                    style={{ color: "var(--text-muted)" }}>
                    No callbacks sent yet. Engage a scammer to trigger
                    intelligence reporting.
                  </td>
                </tr>
              )}
              {callbacks.map((cb, i) => {
                const StatusIcon =
                  cb.status === "sent" ? CheckCircle
                  : cb.status === "failed" ? XCircle
                  : cb.status === "no_endpoint" ? CheckCircle
                  : Clock;
                const statusColor =
                  cb.status === "sent" ? "text-emerald-500"
                  : cb.status === "failed" ? "text-red-500"
                  : cb.status === "no_endpoint" ? "text-amber-500"
                  : "";
                return (
                  <tr
                    key={i}
                    className="border-b transition-colors hover:bg-opacity-50"
                    style={{
                      borderColor: "var(--border-primary)",
                    }}>
                    <td
                      className="px-3 py-3.5 font-mono text-xs align-middle"
                      style={{ color: "var(--text-secondary)" }}>
                      {(cb.session_id || "").slice(0, 8)}
                    </td>
                    <td className="px-2 py-3.5 align-middle">
                      <div className="flex items-center justify-center">
                        <StatusIcon
                          size={16}
                          className={statusColor}
                          style={
                            !statusColor ?
                              { color: "var(--text-muted)" }
                            : undefined
                          }
                        />
                      </div>
                    </td>
                    <td className="px-3 py-3.5 align-middle">
                      <FraudBadge label={cb.fraud_type || "GENERIC SCAM"} />
                    </td>
                    <td
                      className="px-3 py-3.5 text-xs hidden sm:table-cell align-middle"
                      style={{ color: "var(--text-tertiary)" }}>
                      {cb.timestamp ?
                        new Date(cb.timestamp).toLocaleString("en-IN", {
                          timeZone: "Asia/Kolkata",
                          dateStyle: "medium",
                          timeStyle: "short",
                        })
                      : "—"}
                    </td>
                    <td className="px-3 py-3.5 align-middle">
                      <PayloadDrawer
                        data={cb.payload_summary}
                        intelligence={cb.intelligence}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
