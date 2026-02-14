import { useState, useRef, useEffect, useCallback } from "react";
import { sendMessage, fetchScenarios, runSimulation } from "../api";
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
  Play,
  Square,
  Zap,
  Target,
  TrendingUp,
} from "lucide-react";

/* ── tiny id helper ── */
const uid = () =>
  crypto.randomUUID?.() ?? Math.random().toString(36).slice(2, 10);

/* ── animated mode slider ── */
function ModeSlider({ mode, onChange }) {
  const isLLM = mode === "llm";
  return (
    <div className="flex items-center gap-2 sm:gap-3">
      <span
        className={`text-xs font-medium transition-colors hidden sm:inline ${!isLLM ? "text-blue-400" : ""}`}
        style={!isLLM ? undefined : { color: "var(--text-muted)" }}>
        Rule
      </span>
      <button
        onClick={() => onChange(isLLM ? "rule_based" : "llm")}
        className={`relative w-12 sm:w-14 h-6 sm:h-7 rounded-full transition-all duration-300 focus:outline-none ${
          isLLM ?
            "bg-gradient-to-r from-purple-600 to-pink-500 shadow-lg shadow-purple-500/20"
          : "bg-gradient-to-r from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20"
        }`}
        title={isLLM ? "Switch to Rule-Based" : "Switch to LLM-Enhanced"}>
        <span
          className={`absolute top-0.5 w-5 sm:w-6 h-5 sm:h-6 rounded-full bg-white shadow-md flex items-center justify-center mode-slider ${
            isLLM ? "left-[26px] sm:left-[30px]" : "left-0.5"
          }`}>
          {isLLM ?
            <Sparkles size={10} className="text-purple-600 sm:hidden" />
          : <Cpu size={10} className="text-blue-600 sm:hidden" />}
          {isLLM ?
            <Sparkles size={12} className="text-purple-600 hidden sm:block" />
          : <Cpu size={12} className="text-blue-600 hidden sm:block" />}
        </span>
      </button>
      <span
        className={`text-xs font-medium transition-colors hidden sm:inline ${isLLM ? "text-purple-400" : ""}`}
        style={isLLM ? undefined : { color: "var(--text-muted)" }}>
        LLM
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

/* ── Stage Progress Indicator ── */
function StageProgress({ stageInfo }) {
  if (!stageInfo) return null;
  const progress = stageInfo.progress || 0;
  const stageColors = {
    initial_contact: "from-slate-500 to-slate-400",
    rapport_building: "from-blue-500 to-cyan-400",
    urgency_response: "from-amber-500 to-orange-400",
    scam_confirmed: "from-orange-500 to-red-400",
    information_gathering: "from-purple-500 to-pink-400",
    deep_engagement: "from-red-500 to-rose-400",
    intelligence_extraction: "from-emerald-500 to-teal-400",
    intelligence_reported: "from-green-500 to-emerald-400",
  };
  const gradient =
    stageColors[stageInfo.stage] || "from-slate-500 to-slate-400";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target size={12} className="text-blue-400" />
          <span
            className="text-xs font-medium"
            style={{ color: "var(--text-heading)" }}>
            Engagement Stage
          </span>
        </div>
        <span className="text-[10px] font-mono text-blue-400">{progress}%</span>
      </div>

      {/* Progress bar */}
      <div
        className="h-2 rounded-full overflow-hidden"
        style={{ background: "var(--bar-track)" }}>
        <div
          className={`h-full rounded-full bg-gradient-to-r ${gradient} transition-all duration-700`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage label */}
      <div className="flex items-center justify-between">
        <span
          className="text-xs font-medium"
          style={{ color: "var(--text-secondary)" }}>
          {stageInfo.label}
        </span>
        {stageInfo.agent_confidence > 0 && (
          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            Agent conf: {(stageInfo.agent_confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
        {stageInfo.description}
      </p>

      {/* Tactics seen */}
      {stageInfo.tactics_seen && stageInfo.tactics_seen.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {stageInfo.tactics_seen.map((t) => (
            <span
              key={t}
              className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-red-500/10 text-red-400 border border-red-500/10">
              {t.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Scenario Selector Dropdown ── */
function ScenarioSelector({ scenarios, onSelect, loading, disabled }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const diffColors = {
    easy: "text-emerald-400",
    medium: "text-amber-400",
    hard: "text-red-400",
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled || loading}
        className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-[11px] sm:text-xs font-medium transition-all bg-gradient-to-r from-emerald-600/80 to-teal-600/80 text-white hover:shadow-lg hover:shadow-emerald-500/20 disabled:opacity-40"
        title="Run auto-simulation with a demo scenario">
        {loading ?
          <Loader2 size={12} className="animate-spin" />
        : <Play size={12} />}
        <span className="hidden xs:inline">Simulate</span>
        <span className="xs:hidden">Sim</span>
      </button>

      {open && (
        <div
          className="fixed sm:absolute inset-x-4 sm:inset-x-auto sm:left-auto sm:right-0 top-auto sm:top-full mt-1 sm:w-72 max-h-[70vh] rounded-xl border shadow-xl z-50 overflow-hidden flex flex-col"
          style={{
            background: "var(--bg-primary)",
            borderColor: "var(--border-primary)",
          }}>
          <div
            className="px-3 py-2 border-b flex-shrink-0"
            style={{ borderColor: "var(--border-primary)" }}>
            <span
              className="text-xs font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Demo Scenarios
            </span>
          </div>
          <div className="overflow-y-auto flex-1">
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setOpen(false);
                  onSelect(s.id);
                }}
                className="w-full text-left px-3 py-2.5 hover:bg-blue-500/5 transition-colors border-b last:border-0"
                style={{ borderColor: "var(--border-primary)" }}>
                <div className="flex items-center justify-between">
                  <span
                    className="text-xs font-medium"
                    style={{ color: "var(--text-heading)" }}>
                    {s.name}
                  </span>
                  <span
                    className={`text-[10px] ${diffColors[s.difficulty] || ""}`}>
                    {s.difficulty}
                  </span>
                </div>
                <p
                  className="text-[10px] mt-0.5 line-clamp-2"
                  style={{ color: "var(--text-muted)" }}>
                  {s.description}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="text-[9px] px-1.5 py-0.5 rounded-full border"
                    style={{
                      color: "var(--text-tertiary)",
                      borderColor: "var(--border-primary)",
                    }}>
                    {s.language === "hi" ? "Hindi" : "English"}
                  </span>
                  <span
                    className="text-[9px]"
                    style={{ color: "var(--text-tertiary)" }}>
                    {s.message_count} messages
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Stage Progression Timeline (simulation mode) ── */
function StageTimeline({ stages }) {
  if (!stages || stages.length === 0) return null;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <TrendingUp size={12} className="text-emerald-400" />
        <span
          className="text-xs font-medium"
          style={{ color: "var(--text-heading)" }}>
          Stage Progression
        </span>
      </div>
      <div className="space-y-1">
        {stages.map((s, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="text-[10px] font-mono w-5 text-right"
              style={{ color: "var(--text-muted)" }}>
              {s.step}
            </span>
            <div
              className="flex-1 h-1.5 rounded-full overflow-hidden"
              style={{ background: "var(--bar-track)" }}>
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-emerald-500 transition-all duration-500"
                style={{ width: `${s.progress}%` }}
              />
            </div>
            <span
              className="text-[10px] w-20 truncate"
              style={{ color: "var(--text-tertiary)" }}>
              {s.label}
            </span>
          </div>
        ))}
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

  // Auto-simulation state
  const [scenarios, setScenarios] = useState([]);
  const [simulating, setSimulating] = useState(false);
  const [simStages, setSimStages] = useState([]);

  const scrollToBottom = useCallback(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(scrollToBottom, [messages, scrollToBottom]);

  // Load available scenarios on mount
  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() => setScenarios([]));
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading || simulating) return;

    const userMsg = { id: uid(), sender: "scammer", text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ sender: m.sender, text: m.text }));
      const data = await sendMessage(sessionId, text, history, mode);

      // If LLM was selected but the backend fell back, show a warning
      if (mode === "llm" && data.reply_source === "rule_based_fallback") {
        setMessages((prev) => [
          ...prev,
          {
            id: uid(),
            sender: "system",
            text: "LLM unavailable or failed. Fallback to rule-based reply.",
            ts: Date.now(),
          },
        ]);
      }

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

  /* ── Auto-simulation handler ── */
  const handleSimulate = async (scenarioId) => {
    if (simulating || loading) return;

    // Reset state
    handleNewSession();
    setSimulating(true);
    setSimStages([]);
    setShowPanel(false);

    try {
      const result = await runSimulation(scenarioId, mode);

      // Display messages one by one with delay for typing effect
      const conv = result.conversation || [];
      for (let i = 0; i < conv.length; i++) {
        const m = conv[i];
        await new Promise((r) =>
          setTimeout(r, m.sender === "scammer" ? 800 : 500),
        );
        setMessages((prev) => [
          ...prev,
          {
            id: uid(),
            sender: m.sender,
            text: m.text,
            ts: Date.now(),
            source: m.reply_source || undefined,
            simStep: m.step,
          },
        ]);
      }

      // Set analysis and stage progression
      if (result.final_analysis) {
        setAnalysis({
          ...result.final_analysis,
          stage_info:
            result.stage_progression?.length > 0 ?
              result.stage_progression[result.stage_progression.length - 1]
            : null,
        });
      }
      setSimStages(result.stage_progression || []);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          sender: "system",
          text: `Simulation error: ${err.message}`,
          ts: Date.now(),
        },
      ]);
    } finally {
      setSimulating(false);
    }
  };

  const handleNewSession = () => {
    setSessionId(uid());
    setMessages([]);
    setAnalysis(null);
    setSimStages([]);
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
          className="flex flex-wrap items-center justify-between gap-2 sm:gap-3 px-3 sm:px-4 md:px-6 py-2 sm:py-3 border-b"
          style={{ borderColor: "var(--border-primary)" }}>
          <div className="flex items-center gap-2 sm:gap-3">
            <h2
              className="text-xs sm:text-sm font-semibold"
              style={{ color: "var(--text-heading)" }}>
              Session
            </h2>
            <span
              className="text-[10px] sm:text-[11px] font-mono hidden sm:block"
              style={{ color: "var(--text-muted)" }}>
              {sessionId.slice(0, 8)}
            </span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ModeSlider mode={mode} onChange={setMode} />
            <ScenarioSelector
              scenarios={scenarios}
              onSelect={handleSimulate}
              loading={simulating}
              disabled={loading}
            />
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
                Type a scam message to begin, or click{" "}
                <span className="text-emerald-400 font-medium">Simulate</span>{" "}
                to run a full demo scenario automatically.
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

          {(loading || simulating) && (
            <div className="flex items-center gap-2 text-blue-400 animate-fade-in">
              <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                <Loader2 size={14} className="animate-spin" />
              </div>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {simulating ? "Simulation running..." : "Agent is analyzing..."}
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
              placeholder={
                simulating ?
                  "Simulation in progress..."
                : "Type a scam message to test..."
              }
              className="flex-1 bg-transparent text-sm outline-none"
              style={{
                color: "var(--text-primary)",
                "--tw-placeholder-color": "var(--input-placeholder)",
              }}
              disabled={loading || simulating}
            />
            <button
              onClick={handleSend}
              disabled={loading || simulating || !input.trim()}
              className="p-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white disabled:opacity-40 transition-all hover:shadow-lg hover:shadow-blue-500/20">
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* ── Analysis panel ── */}
      {/* Mobile overlay backdrop */}
      {showPanel && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setShowPanel(false)}
        />
      )}
      <div
        className={`${
          showPanel ?
            "fixed inset-y-0 right-0 z-50 w-80 max-w-[85vw]"
          : "hidden"
        } lg:relative lg:block lg:w-80 border-l overflow-y-auto flex-shrink-0`}
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
              {/* Stage Progress */}
              {analysis.stage_info && (
                <div className="glass rounded-xl p-3">
                  <StageProgress stageInfo={analysis.stage_info} />
                </div>
              )}

              {/* Risk */}
              <div className="glass rounded-xl p-3">
                <RiskBar
                  level={analysis.risk_level}
                  score={analysis.risk_score}
                />
              </div>

              {/* Detection + Fraud Type */}
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
                {/* Fraud Type Badge */}
                {analysis.fraud_type && (
                  <div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${
                        analysis.fraud_color === "red" ?
                          "text-red-400 bg-red-500/10 border-red-500/20"
                        : analysis.fraud_color === "amber" ?
                          "text-amber-400 bg-amber-500/10 border-amber-500/20"
                        : analysis.fraud_color === "purple" ?
                          "text-purple-400 bg-purple-500/10 border-purple-500/20"
                        : analysis.fraud_color === "blue" ?
                          "text-blue-400 bg-blue-500/10 border-blue-500/20"
                        : "text-slate-400 bg-slate-500/10 border-slate-500/20"
                      }`}>
                      {analysis.fraud_type}
                    </span>
                  </div>
                )}
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
                      {analysis.scam_stage.replace(/_/g, " ")}
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
                {/* Detection Reasoning */}
                {analysis.detection_reasons &&
                  analysis.detection_reasons.length > 0 && (
                    <div className="mt-2 space-y-1">
                      <span
                        className="text-[10px] font-semibold"
                        style={{ color: "var(--text-heading)" }}>
                        Detection Reasoning
                      </span>
                      <ul className="space-y-0.5">
                        {analysis.detection_reasons.map((reason, idx) => (
                          <li
                            key={idx}
                            className="flex items-start gap-1.5 text-[10px]"
                            style={{ color: "var(--text-tertiary)" }}>
                            <span className="text-blue-400 mt-0.5">▸</span>
                            <span>{reason}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                {/* Pattern Similarity */}
                {analysis.pattern_similarity != null &&
                  analysis.pattern_similarity > 0 && (
                    <div className="mt-2 space-y-1">
                      <div className="flex items-center justify-between">
                        <span
                          className="text-[10px] font-semibold"
                          style={{ color: "var(--text-heading)" }}>
                          Pattern Similarity
                        </span>
                        <span className="text-[10px] font-mono text-purple-400">
                          {(analysis.pattern_similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div
                        className="h-1 rounded-full overflow-hidden"
                        style={{ background: "var(--bar-track)" }}>
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-700"
                          style={{
                            width: `${(analysis.pattern_similarity * 100).toFixed(0)}%`,
                          }}
                        />
                      </div>
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

              {/* Stage Progression Timeline (from simulation) */}
              {simStages.length > 0 && (
                <div className="glass rounded-xl p-3">
                  <StageTimeline stages={simStages} />
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
