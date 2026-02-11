import { useState, useRef, useEffect, useCallback } from "react";
import { sendMessage } from "../api";
import {
  Send,
  AlertTriangle,
  ShieldCheck,
  Bot,
  User,
  Cpu,
  Sparkles,
  Loader2,
  RefreshCw,
  ChevronRight,
  Info,
  Activity,
} from "lucide-react";

/* ── tiny id helper ── */
const uid = () =>
  crypto.randomUUID?.() ?? Math.random().toString(36).slice(2, 10);

/* ── animated mode slider ── */
function ModeSlider({ mode, onChange }) {
  const isLLM = mode === "llm";
  return (
    <div className="flex items-center gap-3">
      <span
        className={`text-xs font-medium transition-colors ${!isLLM ? "text-blue-400" : ""}`}
        style={!isLLM ? undefined : { color: "var(--text-muted)" }}>
        Rule-Based
      </span>
      <button
        onClick={() => onChange(isLLM ? "rule_based" : "llm")}
        className={`relative w-14 h-7 rounded-full transition-all duration-300 focus:outline-none ${
          isLLM ?
            "bg-gradient-to-r from-purple-600 to-pink-500 shadow-lg shadow-purple-500/20"
          : "bg-gradient-to-r from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20"
        }`}
        title={isLLM ? "Switch to Rule-Based" : "Switch to LLM-Enhanced"}>
        <span
          className={`absolute top-0.5 w-6 h-6 rounded-full bg-white shadow-md flex items-center justify-center mode-slider ${
            isLLM ? "left-[30px]" : "left-0.5"
          }`}>
          {isLLM ?
            <Sparkles size={12} className="text-purple-600" />
          : <Cpu size={12} className="text-blue-600" />}
        </span>
      </button>
      <span
        className={`text-xs font-medium transition-colors ${isLLM ? "text-purple-400" : ""}`}
        style={isLLM ? undefined : { color: "var(--text-muted)" }}>
        LLM-Enhanced
      </span>
    </div>
  );
}

/* ── active mode badge ── */
function ModeBadge({ mode, source }) {
  if (mode === "llm" && source === "llm") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
        <Sparkles size={10} /> LLM
      </span>
    );
  }
  if (mode === "llm" && source === "rule_based_fallback") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <AlertTriangle size={10} /> Fallback
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
      <Cpu size={10} /> Rule
    </span>
  );
}

/* ── risk indicator bar ── */
function RiskBar({ level, score }) {
  const colors = {
    minimal: "bg-slate-500",
    low: "bg-emerald-500",
    medium: "bg-amber-500",
    high: "bg-orange-500",
    critical: "bg-red-500",
  };
  const pct = Math.min((score || 0) / 100, 1) * 100;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span style={{ color: "var(--text-tertiary)" }}>Risk</span>
        <span
          className={`font-medium ${
            level === "critical" ? "text-red-400"
            : level === "high" ? "text-orange-400"
            : ""
          }`}
          style={
            level !== "critical" && level !== "high" ?
              { color: "var(--text-secondary)" }
            : undefined
          }>
          {(level || "minimal").toUpperCase()}
        </span>
      </div>
      <div
        className="h-1.5 rounded-full overflow-hidden"
        style={{ background: "var(--bar-track)" }}>
        <div
          className={`h-full rounded-full transition-all duration-500 ${colors[level] || colors.minimal}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function SessionView() {
  const [sessionId, setSessionId] = useState(uid());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("rule_based");
  const [analysis, setAnalysis] = useState(null);
  const [showPanel, setShowPanel] = useState(false);
  const chatEnd = useRef(null);

  const scrollToBottom = useCallback(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { id: uid(), sender: "scammer", text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ sender: m.sender, text: m.text }));
      const data = await sendMessage(sessionId, text, history, mode);

      const agentMsg = {
        id: uid(),
        sender: "agent",
        text: data.reply,
        ts: Date.now(),
        source: data.reply_source || "rule_based",
      };
      setMessages((prev) => [...prev, agentMsg]);
      setAnalysis(data);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          sender: "system",
          text: `Error: ${err.message}`,
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    setSessionId(uid());
    setMessages([]);
    setAnalysis(null);
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-full">
      {/* ── Chat column ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toolbar */}
        <div
          className="flex flex-wrap items-center justify-between gap-3 px-4 md:px-6 py-3 border-b"
          style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-3">
            <h2
              className="text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Session
            </h2>
            <span
              className="text-[11px] font-mono hidden sm:block"
              style={{ color: "var(--text-muted)" }}>
              {sessionId.slice(0, 8)}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <ModeSlider mode={mode} onChange={setMode} />
            <button
              onClick={handleNewSession}
              className="p-2 rounded-lg transition-colors"
              style={{ color: "var(--text-tertiary)" }}
              title="New session">
              <RefreshCw size={15} />
            </button>
            <button
              onClick={() => setShowPanel((p) => !p)}
              className="p-2 rounded-lg transition-colors lg:hidden"
              style={{ color: "var(--text-tertiary)" }}
              title="Toggle analysis">
              <Info size={15} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 space-y-3">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center border border-slate-800/60 mb-4">
                <Bot size={28} className="text-blue-400" />
              </div>
              <h3
                className="text-base font-semibold mb-1"
                style={{ color: "var(--text-heading)" }}>
                Scam Simulation Ready
              </h3>
              <p
                className="text-sm max-w-sm"
                style={{ color: "var(--text-tertiary)" }}>
                Type a scam message to begin. The honeypot agent will respond
                with realistic human-like replies while extracting intelligence.
              </p>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${m.sender === "scammer" ? "justify-end" : "justify-start"} animate-fade-in`}>
              {m.sender === "agent" && (
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center mr-2 mt-1 border border-blue-500/20">
                  <Bot size={14} className="text-blue-400" />
                </div>
              )}
              <div
                className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  m.sender === "scammer" ?
                    "bg-gradient-to-br from-red-500/15 to-red-600/10 border border-red-500/10"
                  : m.sender === "agent" ? "glass"
                  : "bg-amber-500/10 border border-amber-500/10"
                }`}
                style={{
                  color:
                    m.sender === "scammer" ? "var(--scammer-text)"
                    : m.sender === "agent" ? "var(--agent-text)"
                    : undefined,
                }}>
                {m.text}
                {m.source && (
                  <div className="mt-1.5">
                    <ModeBadge mode={mode} source={m.source} />
                  </div>
                )}
              </div>
              {m.sender === "scammer" && (
                <div className="flex-shrink-0 w-7 h-7 rounded-full bg-red-500/10 flex items-center justify-center ml-2 mt-1 border border-red-500/20">
                  <User size={14} className="text-red-400" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-blue-400 animate-fade-in">
              <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <Loader2 size={14} className="animate-spin" />
              </div>
              <span className="text-xs text-slate-400">
                Agent is analyzing...
              </span>
            </div>
          )}
          <div ref={chatEnd} />
        </div>

        {/* Input */}
        <div
          className="px-4 md:px-6 py-3 border-t"
          style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-2 glass rounded-xl px-3 py-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Type a scam message to test..."
              className="flex-1 bg-transparent text-sm outline-none"
              style={{
                color: "var(--text-primary)",
                "--tw-placeholder-color": "var(--input-placeholder)",
              }}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white disabled:opacity-40 transition-all hover:shadow-lg hover:shadow-blue-500/20">
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* ── Analysis panel ── */}
      <div
        className={`${
          showPanel ? "block" : "hidden"
        } lg:block w-full lg:w-80 border-l overflow-y-auto flex-shrink-0`}
        style={{
          borderColor: "var(--border-primary)",
          background: "var(--bg-secondary)",
        }}>
        <div className="px-4 py-4 space-y-4">
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-blue-400" />
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Session Analysis
            </h3>
          </div>

          {!analysis ?
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>
              Send a message to see analysis.
            </p>
          : <>
              {/* Risk */}
              <div className="glass rounded-xl p-3">
                <RiskBar
                  level={analysis.risk_level}
                  score={analysis.risk_score}
                />
              </div>

              {/* Detection */}
              <div className="glass rounded-xl p-3 space-y-2">
                <div className="flex items-center gap-2">
                  {analysis.scam_detected ?
                    <AlertTriangle size={14} className="text-red-400" />
                  : <ShieldCheck size={14} className="text-emerald-400" />}
                  <span
                    className="text-xs font-medium"
                    style={{ color: "var(--text-heading)" }}>
                    {analysis.scam_detected ? "Scam Detected" : "Monitoring"}
                  </span>
                </div>
                {analysis.scam_type && analysis.scam_type !== "unknown" && (
                  <div
                    className="text-xs"
                    style={{ color: "var(--text-tertiary)" }}>
                    Type:{" "}
                    <span style={{ color: "var(--text-secondary)" }}>
                      {analysis.scam_type.replace(/_/g, " ")}
                    </span>
                  </div>
                )}
                {analysis.scam_stage && (
                  <div
                    className="text-xs"
                    style={{ color: "var(--text-tertiary)" }}>
                    Stage:{" "}
                    <span style={{ color: "var(--text-secondary)" }}>
                      {analysis.scam_stage}
                    </span>
                  </div>
                )}
                {analysis.confidence != null && (
                  <div
                    className="text-xs"
                    style={{ color: "var(--text-tertiary)" }}>
                    Confidence:{" "}
                    <span style={{ color: "var(--text-secondary)" }}>
                      {(analysis.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Intelligence */}
              {analysis.intelligence_counts && (
                <div className="glass rounded-xl p-3 space-y-2">
                  <h4
                    className="text-xs font-medium"
                    style={{ color: "var(--text-heading)" }}>
                    Intel Extracted
                  </h4>
                  <div className="grid grid-cols-2 gap-1.5">
                    {Object.entries(analysis.intelligence_counts).map(
                      ([k, v]) => (
                        <div
                          key={k}
                          className="flex justify-between text-xs px-2 py-1 rounded"
                          style={{ background: "var(--bg-tertiary)" }}>
                          <span style={{ color: "var(--text-tertiary)" }}>
                            {k.replace(/([A-Z])/g, " $1").trim()}
                          </span>
                          <span
                            className={
                              v > 0 ?
                                "text-blue-400 font-medium"
                              : "text-slate-600"
                            }>
                            {v}
                          </span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}

              {/* Callback */}
              {analysis.callback_sent && (
                <div className="rounded-xl p-3 bg-emerald-500/10 border border-emerald-500/20">
                  <div className="flex items-center gap-2">
                    <Send size={12} className="text-emerald-400" />
                    <span className="text-xs font-medium text-emerald-300">
                      Callback Sent
                    </span>
                  </div>
                </div>
              )}
            </>
          }
        </div>
      </div>
    </div>
  );
}
