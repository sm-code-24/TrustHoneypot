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
} from "lucide-react";

function JsonPreview({ data }) {
  const [open, setOpen] = useState(false);
  if (!data) return <span className="text-slate-500">—</span>;
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300 transition-colors">
        {open ?
          <ChevronUp size={12} />
        : <ChevronDown size={12} />}
        {open ? "Hide" : "View"} payload
      </button>
      {open && (
        <pre className="mt-2 text-[10px] font-mono text-slate-400 bg-slate-800/60 rounded-lg p-3 overflow-x-auto max-h-40 whitespace-pre-wrap leading-relaxed border border-slate-700/30">
          {JSON.stringify(data, null, 2)}
        </pre>
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

  return (
    <div className="p-4 md:p-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-2">
        <Send size={18} className="text-emerald-400" />
        <h2 className="text-lg font-semibold text-white">Callback Reports</h2>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass rounded-xl p-4 text-center card-hover border border-slate-800/40">
          <div className="text-2xl font-bold text-white">
            {callbacks.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">Total</div>
        </div>
        <div className="glass rounded-xl p-4 text-center card-hover border border-emerald-500/10">
          <div className="text-2xl font-bold text-emerald-400">{sent}</div>
          <div className="text-xs text-slate-400 mt-1">Sent</div>
        </div>
        <div className="glass rounded-xl p-4 text-center card-hover border border-red-500/10">
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div className="text-xs text-slate-400 mt-1">Failed</div>
        </div>
      </div>

      {/* Callback table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800/50">
          <h3 className="text-sm font-semibold text-white">Callback History</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-400 border-b border-slate-800/40">
                <th className="text-left px-5 py-2.5 font-medium">Session</th>
                <th className="text-center px-5 py-2.5 font-medium">Status</th>
                <th className="text-left px-5 py-2.5 font-medium hidden sm:table-cell">
                  Time
                </th>
                <th className="text-left px-5 py-2.5 font-medium">Payload</th>
              </tr>
            </thead>
            <tbody>
              {callbacks.length === 0 && (
                <tr>
                  <td
                    colSpan={4}
                    className="px-5 py-8 text-center text-sm text-slate-500">
                    No callbacks sent yet. Engage a scammer to trigger
                    intelligence reporting.
                  </td>
                </tr>
              )}
              {callbacks.map((cb, i) => {
                const StatusIcon =
                  cb.status === "sent" ? CheckCircle
                  : cb.status === "failed" ? XCircle
                  : Clock;
                const statusColor =
                  cb.status === "sent" ? "text-emerald-400"
                  : cb.status === "failed" ? "text-red-400"
                  : "text-slate-400";
                return (
                  <tr
                    key={i}
                    className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-colors align-top">
                    <td className="px-5 py-2.5 font-mono text-xs text-slate-300">
                      {(cb.session_id || "").slice(0, 8)}
                    </td>
                    <td className="px-5 py-2.5 text-center">
                      <StatusIcon size={14} className={statusColor} />
                    </td>
                    <td className="px-5 py-2.5 text-xs text-slate-400 hidden sm:table-cell">
                      {cb.timestamp ?
                        new Date(cb.timestamp).toLocaleString()
                      : "—"}
                    </td>
                    <td className="px-5 py-2.5">
                      <JsonPreview data={cb.payload_summary} />
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
