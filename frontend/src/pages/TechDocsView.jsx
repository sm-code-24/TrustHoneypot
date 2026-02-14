import {
  Shield,
  Brain,
  Radio,
  Database,
  Lock,
  Zap,
  Server,
  Code2,
  Layers,
  ArrowRight,
  Cpu,
  Globe,
  FileSearch,
  AlertTriangle,
} from "lucide-react";

const TECH_STACK = [
  {
    category: "Backend",
    icon: Server,
    color: "from-blue-500 to-cyan-400",
    items: [
      {
        name: "FastAPI",
        desc: "High-performance async Python web framework for the REST API",
      },
      {
        name: "Python 3.11+",
        desc: "Core language with type hints, async/await, and dataclasses",
      },
      { name: "Uvicorn", desc: "ASGI server running the FastAPI application" },
      {
        name: "Pydantic v2",
        desc: "Request/response validation and serialization",
      },
    ],
  },
  {
    category: "AI / LLM",
    icon: Brain,
    color: "from-purple-500 to-pink-400",
    items: [
      {
        name: "Groq Llama 3.3 70B Versatile",
        desc: "Ultra-fast inference for bilingual (EN/HI) reply rephrasing with 14,400 free requests/day",
      },
      {
        name: "httpx AsyncClient",
        desc: "Direct REST API calls with IPv4 forced, circuit breaker, and production-grade timeouts",
      },
      {
        name: "Rule-Based Engine",
        desc: "Primary detection authority — LLM never overrides rules",
      },
      {
        name: "260+ Response Templates",
        desc: "Bilingual (English + Hindi) category-specific templates across 15+ pools",
      },
    ],
  },
  {
    category: "Frontend",
    icon: Code2,
    color: "from-emerald-500 to-teal-400",
    items: [
      {
        name: "React 18",
        desc: "Component-based UI with hooks and concurrent features",
      },
      {
        name: "Vite 6",
        desc: "Lightning-fast build tool with HMR for development",
      },
      {
        name: "Tailwind CSS 3",
        desc: "Utility-first CSS with custom glassmorphism design system",
      },
      {
        name: "Lucide React",
        desc: "Consistent, lightweight SVG icon library",
      },
    ],
  },
  {
    category: "Database & Infra",
    icon: Database,
    color: "from-amber-500 to-orange-400",
    items: [
      {
        name: "MongoDB Atlas",
        desc: "Cloud-hosted NoSQL for session summaries and threat patterns",
      },
      { name: "PyMongo", desc: "Python driver for MongoDB operations" },
      {
        name: "Railway",
        desc: "Backend API hosting with auto-deploy from GitHub",
      },
      {
        name: "Vercel",
        desc: "Frontend hosting with edge CDN and preview deployments",
      },
    ],
  },
];

const ARCH_FLOW = [
  { label: "Scammer Message", icon: AlertTriangle, color: "text-red-400" },
  { label: "5-Layer Detector", icon: Layers, color: "text-blue-400" },
  { label: "Intel Extractor", icon: FileSearch, color: "text-emerald-400" },
  { label: "AI Agent Response", icon: Cpu, color: "text-purple-400" },
  { label: "Threat Database", icon: Database, color: "text-amber-400" },
];

const DETECTION_LAYERS = [
  {
    name: "Pattern Matching",
    desc: "Regex-based detection of known scam phrases, urgency patterns, and impersonation keywords across 18+ categories including UPI fraud, KYC scams, lottery, tech support, and more.",
  },
  {
    name: "Behavioral Scoring",
    desc: "Multi-signal scoring engine that tracks urgency escalation, personal info requests, financial pressure, and trust manipulation tactics. Score thresholds determine threat level.",
  },
  {
    name: "India-Specific Taxonomy",
    desc: "Purpose-built scam taxonomy covering Aadhaar fraud, PAN verification scams, digital arrest, customs impersonation, and other India-prevalent fraud types.",
  },
  {
    name: "Context Analysis",
    desc: "Session-level analysis that detects turn-by-turn escalation, topic switching, and multi-stage scam progression for accurate classification.",
  },
  {
    name: "Intelligence Correlation",
    desc: "Cross-references extracted intelligence (UPI, phone, bank details) against session history to identify repeat offenders and linked scam operations.",
  },
];

const EXTRACTORS = [
  "UPI IDs (name@bank format)",
  "Bank Account + IFSC pairs",
  "Phone Numbers (Indian format)",
  "Aadhaar Numbers (12-digit)",
  "PAN Card Numbers",
  "Phishing URLs & Domains",
  "Email Addresses",
  "Crypto Wallet Addresses",
];

export default function TechDocsView() {
  return (
    <div className="p-4 md:p-8 space-y-10 animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 mb-3 px-4 py-1.5 rounded-full bg-blue-500/[0.08] border border-blue-500/20">
          <Code2 size={14} className="text-blue-400" />
          <span className="text-xs font-medium text-blue-300">
            Technical Documentation
          </span>
        </div>
        <h2
          className="text-2xl md:text-3xl font-bold"
          style={{ color: "var(--text-heading)" }}>
          System Architecture & Tech Stack
        </h2>
        <p
          className="mt-3 text-sm max-w-2xl mx-auto"
          style={{ color: "var(--text-tertiary)" }}>
          A comprehensive overview of how TrustHoneypot detects, engages, and
          extracts intelligence from scam operations targeting Indian citizens.
        </p>
      </div>

      {/* Architecture Flow */}
      <section className="glass rounded-2xl p-6 md:p-8 glow-border">
        <h3
          className="text-lg font-semibold mb-6 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Zap size={18} className="text-blue-400" />
          Request Flow Architecture
        </h3>
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 md:gap-0">
          {ARCH_FLOW.map((step, i) => (
            <div key={step.label} className="flex items-center gap-3">
              <div className="flex flex-col items-center text-center min-w-[100px]">
                <div
                  className="w-12 h-12 rounded-xl border flex items-center justify-center mb-2"
                  style={{
                    background: "var(--bg-tertiary)",
                    borderColor: "var(--border-primary)",
                  }}>
                  <step.icon size={20} className={step.color} />
                </div>
                <span
                  className="text-xs font-medium"
                  style={{ color: "var(--text-secondary)" }}>
                  {step.label}
                </span>
              </div>
              {i < ARCH_FLOW.length - 1 && (
                <ArrowRight
                  size={16}
                  className="text-slate-600 hidden md:block flex-shrink-0"
                />
              )}
            </div>
          ))}
        </div>
        <div
          className="mt-6 p-4 rounded-xl border"
          style={{
            background: "var(--bg-tertiary)",
            borderColor: "var(--border-primary)",
          }}>
          <p
            className="text-xs leading-relaxed"
            style={{ color: "var(--text-tertiary)" }}>
            <span
              className="font-medium"
              style={{ color: "var(--gradient-text-1)" }}>
              Flow:
            </span>{" "}
            Incoming scammer message → 5-layer detection engine classifies
            threat level & scam category → Intelligence extractor parses
            financial data (UPI, bank, Aadhaar, etc.) → AI agent generates
            contextual response using rule-based templates + Groq LLM rephrasing
            → Session summary and extracted intelligence persisted to MongoDB
            for threat pattern learning.
          </p>
        </div>
      </section>

      {/* Architecture Invariant */}
      <section className="glass rounded-2xl p-6 md:p-8 text-center">
        <Lock size={22} className="mx-auto text-blue-400 mb-3" />
        <h3
          className="text-base font-semibold mb-2"
          style={{ color: "var(--text-heading)" }}>
          Core Architectural Principle
        </h3>
        <p
          className="text-sm max-w-xl mx-auto leading-relaxed"
          style={{ color: "var(--text-tertiary)" }}>
          The rule-based engine is the{" "}
          <span
            className="font-medium"
            style={{ color: "var(--gradient-text-1)" }}>
            single authority
          </span>{" "}
          for all detection and response decisions. The Groq LLM is an optional
          enhancement that only rephrases responses for realism — it{" "}
          <span className="text-red-400 font-medium">never</span> overrides
          detection, generates scam content, or makes classification decisions.
          This ensures deterministic, auditable behavior at all times.
        </p>
      </section>

      {/* Tech Stack Grid */}
      <section>
        <h3
          className="text-lg font-semibold mb-6 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Layers size={18} className="text-purple-400" />
          Technology Stack
        </h3>
        <div className="grid md:grid-cols-2 gap-5">
          {TECH_STACK.map((cat) => (
            <div
              key={cat.category}
              className="glass rounded-2xl p-6 card-hover">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-10 h-10 rounded-xl bg-gradient-to-br ${cat.color} flex items-center justify-center shadow-lg`}>
                  <cat.icon size={18} className="text-white" />
                </div>
                <h4
                  className="text-sm font-semibold"
                  style={{ color: "var(--text-heading)" }}>
                  {cat.category}
                </h4>
              </div>
              <div className="space-y-3">
                {cat.items.map((item) => (
                  <div key={item.name} className="flex gap-2">
                    <span className="text-blue-400 mt-0.5 text-xs">▸</span>
                    <div>
                      <span
                        className="text-sm font-medium"
                        style={{ color: "var(--text-secondary)" }}>
                        {item.name}
                      </span>
                      <span
                        className="text-xs ml-1.5"
                        style={{ color: "var(--text-tertiary)" }}>
                        — {item.desc}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Detection Layers */}
      <section>
        <h3
          className="text-lg font-semibold mb-6 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Shield size={18} className="text-emerald-400" />
          5-Layer Detection Engine
        </h3>
        <div className="space-y-3">
          {DETECTION_LAYERS.map((layer, i) => (
            <div
              key={layer.name}
              className="glass rounded-xl p-5 card-hover animate-fade-in"
              style={{
                animationDelay: `${i * 80}ms`,
                animationFillMode: "both",
              }}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-400 flex items-center justify-center text-white text-xs font-bold shadow-md">
                  {i + 1}
                </div>
                <div>
                  <h4
                    className="text-sm font-semibold"
                    style={{ color: "var(--text-heading)" }}>
                    {layer.name}
                  </h4>
                  <p
                    className="text-xs mt-1 leading-relaxed"
                    style={{ color: "var(--text-tertiary)" }}>
                    {layer.desc}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Intelligence Extractors */}
      <section className="glass rounded-2xl p-6 md:p-8">
        <h3
          className="text-lg font-semibold mb-5 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Radio size={18} className="text-cyan-400" />
          Intelligence Extractors
        </h3>
        <p
          className="text-sm mb-4 leading-relaxed"
          style={{ color: "var(--text-tertiary)" }}>
          The extraction pipeline uses specialized regex patterns and contextual
          parsing to identify and capture 8 types of financial intelligence from
          scammer messages:
        </p>
        <div className="grid sm:grid-cols-2 gap-2">
          {EXTRACTORS.map((ext) => (
            <div
              key={ext}
              className="flex items-center gap-2 px-3 py-2.5 rounded-lg border"
              style={{
                background: "var(--bg-tertiary)",
                borderColor: "var(--border-primary)",
              }}>
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 flex-shrink-0" />
              <span
                className="text-xs font-medium"
                style={{ color: "var(--text-secondary)" }}>
                {ext}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* API Endpoints */}
      <section className="glass rounded-2xl p-6 md:p-8">
        <h3
          className="text-lg font-semibold mb-5 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Globe size={18} className="text-amber-400" />
          API Endpoints
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr
                className="text-left"
                style={{ borderBottom: "1px solid var(--border-primary)" }}>
                <th
                  className="pb-3 font-medium"
                  style={{ color: "var(--text-tertiary)" }}>
                  Method
                </th>
                <th
                  className="pb-3 font-medium pl-4"
                  style={{ color: "var(--text-tertiary)" }}>
                  Endpoint
                </th>
                <th
                  className="pb-3 font-medium pl-4"
                  style={{ color: "var(--text-tertiary)" }}>
                  Description
                </th>
              </tr>
            </thead>
            <tbody
              className="divide-y"
              style={{ borderColor: "var(--border-primary)" }}>
              {[
                [
                  "POST",
                  "/honeypot",
                  "Process scammer message — detect, extract intel, generate response",
                ],
                [
                  "GET",
                  "/sessions",
                  "Retrieve all session summaries with metadata",
                ],
                [
                  "GET",
                  "/sessions/{id}",
                  "Get detailed session by ID with full conversation history",
                ],
                [
                  "GET",
                  "/sessions/{id}/analysis",
                  "Structured analysis — verdict, reasoning, fraud type, pattern similarity",
                ],
                [
                  "GET",
                  "/patterns",
                  "Aggregated scam patterns and category statistics",
                ],
                ["GET", "/callbacks", "Callback history and delivery status"],
                [
                  "GET",
                  "/intelligence/registry",
                  "Tracked identifiers — filterable by type and risk level",
                ],
                [
                  "GET",
                  "/intelligence/registry/{id}",
                  "Identifier detail — frequency, confidence, associated sessions",
                ],
                [
                  "GET",
                  "/intelligence/patterns",
                  "Pattern correlation — fingerprints, similarity scoring, recurrence",
                ],
                [
                  "GET",
                  "/intelligence/export",
                  "Export intelligence registry as styled Excel (.xlsx) workbook",
                ],
                [
                  "POST",
                  "/intelligence/backfill",
                  "Re-populate intelligence & pattern registries from existing session data",
                ],
                [
                  "GET",
                  "/system/status",
                  "System health — LLM status, DB connection, uptime",
                ],
              ].map(([method, path, desc]) => (
                <tr key={path}>
                  <td className="py-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        method === "POST" ?
                          "bg-emerald-500/15 text-emerald-400"
                        : "bg-blue-500/15 text-blue-400"
                      }`}>
                      {method}
                    </span>
                  </td>
                  <td
                    className="py-2.5 pl-4 font-mono"
                    style={{ color: "var(--text-secondary)" }}>
                    {path}
                  </td>
                  <td
                    className="py-2.5 pl-4"
                    style={{ color: "var(--text-tertiary)" }}>
                    {desc}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* v2.1 Features */}
      <section className="glass rounded-2xl p-6 md:p-8">
        <h3
          className="text-lg font-semibold mb-5 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Zap size={18} className="text-purple-400" />
          v2.1 Enhancements
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            {
              title: "Intelligence Registry",
              desc: "Persistent tracking of all extracted identifiers (UPI, phone, bank, email, links) with frequency counting, confidence scoring, recurring threat detection, and privacy-preserving masking.",
            },
            {
              title: "Pattern Correlation Engine",
              desc: "Fingerprinting of scam tactics with cross-session similarity scoring. Identifies linked operations and repeat offenders across sessions.",
            },
            {
              title: "Structured Detection Reasoning",
              desc: "Each analysis now includes human-readable detection reasons explaining why a session was classified as a specific fraud type.",
            },
            {
              title: "Fraud Type Classification",
              desc: "Sessions and callbacks display professional fraud type labels (PAYMENT FRAUD, KYC PHISHING, LOTTERY SCAM, etc.) with color-coded badges.",
            },
            {
              title: "Excel Export",
              desc: "One-click export of the intelligence registry as a styled .xlsx workbook with formatted headers, conditional formatting, and auto-sized columns.",
            },
            {
              title: "Clickable Intelligence",
              desc: "Registry identifiers are clickable — opening a detail modal showing confidence, frequency, recurrence status, associated sessions, and fraud types.",
            },
            {
              title: "Session Persistence",
              desc: "Chat sessions persist across tab navigation within the dashboard. Conversations are only cleared when starting a new session or refreshing the page.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="flex items-start gap-2 px-3 py-2.5 rounded-lg border"
              style={{
                background: "var(--bg-tertiary)",
                borderColor: "var(--border-primary)",
              }}>
              <div className="w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0 mt-1.5" />
              <div>
                <span
                  className="text-sm font-medium"
                  style={{ color: "var(--text-secondary)" }}>
                  {item.title}
                </span>
                <p
                  className="text-xs mt-0.5 leading-relaxed"
                  style={{ color: "var(--text-tertiary)" }}>
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Deployment */}
      <section className="glass rounded-2xl p-6 md:p-8">
        <h3
          className="text-lg font-semibold mb-4 flex items-center gap-2"
          style={{ color: "var(--text-heading)" }}>
          <Server size={18} className="text-pink-400" />
          Deployment Architecture
        </h3>
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            {
              title: "Backend API",
              platform: "Railway",
              details:
                "FastAPI + Uvicorn at trusthoneypot-api.up.railway.app — Nixpacks Python provider, rate limiting, request timing, session TTL cleanup.",
              color: "from-blue-500 to-cyan-400",
            },
            {
              title: "Frontend UI",
              platform: "Vercel",
              details:
                "React + Vite at trusthoneypot.tech — edge CDN, SPA rewrites, dark/light theme, bilingual UI.",
              color: "from-purple-500 to-pink-400",
            },
            {
              title: "Database",
              platform: "MongoDB Atlas",
              details:
                "M0 free tier cluster, IP whitelisting, connection string via MONGODB_URI env variable.",
              color: "from-emerald-500 to-teal-400",
            },
          ].map((dep) => (
            <div
              key={dep.title}
              className="p-4 rounded-xl border"
              style={{
                background: "var(--bg-tertiary)",
                borderColor: "var(--border-primary)",
              }}>
              <div
                className={`inline-block px-2.5 py-1 rounded-md bg-gradient-to-r ${dep.color} text-[10px] font-bold text-white mb-3`}>
                {dep.platform}
              </div>
              <h4
                className="text-sm font-semibold mb-1"
                style={{ color: "var(--text-heading)" }}>
                {dep.title}
              </h4>
              <p
                className="text-xs leading-relaxed"
                style={{ color: "var(--text-tertiary)" }}>
                {dep.details}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
