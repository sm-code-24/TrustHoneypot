import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Shield,
  Brain,
  Radio,
  ChevronRight,
  Lock,
  Github,
  Sparkles,
  Fingerprint,
  Database,
} from "lucide-react";

const CYCLE_WORDS = [
  { text: "Engage", gradient: "from-blue-400 to-cyan-300" },
  { text: "Extract", gradient: "from-purple-400 to-pink-300" },
  { text: "Detect", gradient: "from-emerald-400 to-teal-300" },
  { text: "Protect", gradient: "from-amber-400 to-orange-300" },
];

const FEATURES = [
  {
    icon: Shield,
    title: "Multi-Layer Detection",
    desc: "Pattern analysis, behavioral scoring & India-specific scam taxonomy identify threats in real-time.",
    color: "from-blue-500 to-cyan-400",
  },
  {
    icon: Brain,
    title: "Adaptive AI Agent",
    desc: "Rule-based core with optional Gemini LLM rephrasing — keeps scammers engaged while extracting intel.",
    color: "from-purple-500 to-pink-400",
  },
  {
    icon: Radio,
    title: "Intelligence Extraction",
    desc: "Automatically captures UPI IDs, bank accounts, phone numbers, Aadhaar, PAN & phishing links.",
    color: "from-emerald-500 to-teal-400",
  },
  {
    icon: Database,
    title: "Threat Intelligence DB",
    desc: "MongoDB-backed pattern storage enables continuous learning from every scam interaction.",
    color: "from-amber-500 to-orange-400",
  },
];

const STATS = [
  { label: "Scam Categories", value: "18+" },
  { label: "Detection Layers", value: "5" },
  { label: "Intel Extractors", value: "8" },
  { label: "Response Pools", value: "120+" },
];

export default function Landing() {
  const navigate = useNavigate();
  const year = new Date().getFullYear();
  const [wordIdx, setWordIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setWordIdx((i) => (i + 1) % CYCLE_WORDS.length);
        setVisible(true);
      }, 400);
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  const word = CYCLE_WORDS[wordIdx];

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#020617]">
      {/* Gradient mesh background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0c1527] via-[#020617] to-[#0a0a1a]" />
        <div className="absolute top-[-25%] left-[-10%] w-[700px] h-[700px] rounded-full bg-blue-600/[0.07] blur-[120px] animate-float" />
        <div className="absolute bottom-[-15%] right-[-5%] w-[600px] h-[600px] rounded-full bg-purple-600/[0.06] blur-[100px]" />
        <div
          className="absolute top-[50%] right-[15%] w-[350px] h-[350px] rounded-full bg-cyan-500/[0.04] blur-[80px] animate-float"
          style={{ animationDelay: "1.5s" }}
        />
        <div className="absolute inset-0 bg-grid opacity-30" />
      </div>

      {/* Top bar */}
      <header className="relative z-10 flex items-center justify-between px-6 py-5 md:px-12">
        <div className="flex items-center gap-2.5">
          <div className="relative w-9 h-9 flex items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <Shield size={18} className="text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            Trust<span className="text-gradient">Honeypot</span>
          </span>
        </div>
        <span className="hidden sm:block text-xs font-mono text-slate-500 tracking-wider">
          AI IMPACT BUILDATHON — PS-2
        </span>
      </header>

      {/* Hero */}
      <main className="relative z-10 flex flex-col items-center justify-center px-6 pt-12 pb-8 md:pt-20 md:pb-12 text-center">
        {/* Badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/[0.08] px-5 py-2 text-xs font-medium text-blue-300 shadow-lg shadow-blue-500/5 backdrop-blur-sm">
          <Sparkles size={12} className="animate-pulse" />
          India AI Impact Buildathon 2025
        </div>

        {/* Animated cycling word */}
        <div className="mb-4 h-16 md:h-[5.5rem] flex items-center justify-center overflow-hidden">
          <span
            className={`text-5xl md:text-7xl font-extrabold bg-gradient-to-r ${word.gradient} bg-clip-text text-transparent transition-all duration-[400ms] ease-out ${
              visible ?
                "opacity-100 translate-y-0 scale-100"
              : "opacity-0 translate-y-3 scale-95"
            }`}>
            {word.text}
          </span>
        </div>

        <h1 className="max-w-3xl text-3xl md:text-5xl font-bold tracking-tight text-white leading-tight">
          Scam Intelligence{" "}
          <span className="text-gradient">Command Center</span>
        </h1>

        <p className="mt-6 max-w-2xl text-base md:text-lg text-slate-400 leading-relaxed">
          An agentic honeypot that fools scammers with believable AI
          conversations, extracts critical financial intelligence, and shields
          Indian citizens — all in real-time.
        </p>

        {/* CTA */}
        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
          <button
            onClick={() => navigate("/dashboard/session")}
            className="group flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3.5 text-sm font-semibold text-white shadow-xl shadow-blue-600/25 transition-all hover:shadow-blue-500/40 hover:scale-[1.03] active:scale-[0.98]">
            Launch Dashboard
            <ChevronRight
              size={16}
              className="transition-transform group-hover:translate-x-0.5"
            />
          </button>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 rounded-xl border border-slate-700/50 bg-white/[0.03] backdrop-blur-sm px-6 py-3.5 text-sm font-medium text-slate-300 transition-all hover:border-slate-500 hover:text-white hover:bg-white/[0.06]">
            <Github size={15} />
            View on GitHub
          </a>
        </div>
      </main>

      {/* Punchline */}
      <section className="relative z-10 py-16 md:py-24 text-center">
        <div className="max-w-3xl mx-auto px-6">
          <p className="text-2xl md:text-4xl font-bold text-slate-300 leading-snug">
            Don't just detect scams.
          </p>
          <p className="mt-2 text-3xl md:text-5xl font-extrabold text-gradient leading-snug">
            Outsmart them.
          </p>
          <div className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500">
            <Fingerprint size={14} className="text-blue-400/60" />
            <span>
              Rule-based authority · optional Gemini LLM · zero false positives
            </span>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="relative z-10 px-6 pb-20 max-w-3xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map((s, i) => (
            <div
              key={s.label}
              className="glass rounded-2xl px-4 py-5 text-center card-hover animate-fade-in"
              style={{
                animationDelay: `${i * 100}ms`,
                animationFillMode: "both",
              }}>
              <div className="text-3xl md:text-4xl font-extrabold text-gradient">
                {s.value}
              </div>
              <div className="mt-1.5 text-xs font-medium text-slate-400">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 px-6 md:px-12 pb-20 max-w-5xl mx-auto">
        <h2 className="text-center text-sm font-semibold text-slate-400 uppercase tracking-wider mb-8">
          How It Works
        </h2>
        <div className="grid sm:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="glass rounded-2xl p-6 card-hover animate-fade-in"
              style={{
                animationDelay: `${i * 120}ms`,
                animationFillMode: "both",
              }}>
              <div
                className={`inline-flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br ${f.color} mb-4 shadow-lg`}>
                <f.icon size={20} className="text-white" />
              </div>
              <h3 className="text-base font-semibold text-white mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="relative z-10 px-6 md:px-12 pb-20 max-w-4xl mx-auto">
        <div className="glass rounded-2xl p-8 glow-border text-center">
          <Lock size={24} className="mx-auto text-blue-400 mb-4" />
          <h3 className="text-lg font-semibold text-white mb-3">
            Architecture Invariant
          </h3>
          <p className="text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
            The rule-based engine is the{" "}
            <span className="text-blue-300 font-medium">single authority</span>{" "}
            for detection and responses. LLM enhances phrasing realism only —
            never overrides detection or generates scam content. MongoDB stores
            session summaries for continuous learning.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-slate-800/30 py-6 text-center">
        <p className="text-xs text-slate-500">
          &copy; {year}{" "}
          <span className="text-slate-400 font-medium">200 Hustlers</span>
          {" — "}TrustHoneypot — Made for AI Impact Buildathon PS-2
        </p>
      </footer>
    </div>
  );
}
