# TrustHoneypot v2.1 — Scam Intelligence Command Center

> **Scam Intelligence Platform — Solving Real-World Fraud**  
> Team: **200 Hustlers** (Shailav · Bhupendra · Shivam · Gungun)

An agentic honeypot that **engages scammers** with believable human-like conversations, **extracts financial intelligence** (UPI IDs, bank accounts, phone numbers, Aadhaar, PAN, phishing links), and **reports findings** to government portals — all in real-time.

**Live Demo:**

- Frontend: [https://trusthoneypot.tech](https://trusthoneypot.tech)
- Backend API: [https://trusthoneypot-api.up.railway.app](https://trusthoneypot-api.up.railway.app)

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                     React Dashboard                      │
│  Landing ─ Session ─ Intelligence ─ Patterns ─ About     │
└────────────────────────┬────────────────────────────────┘
                         │ REST / JSON
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────┐ │
│  │ Detector │  │  Agent   │  │ Extractor │  │Callback│ │
│  │ 5-layer  │  │15+ pools │  │ 8 types   │  │  Govt  │ │
│  │ scoring  │  │ rotation │  │ regex+NLP │  │ Portal │ │
│  └──────────┘  └──────┬───┘  └───────────┘  └────────┘ │
│                       │                                  │
│               ┌───────▼───────┐                          │
│               │ LLM Rephraser │                           │
│               │  Groq Llama   │  circuit breaker +       │
│               │  3.3 70B      │  auto-fallback           │
│               └───────────────┘                          │
│                                                          │
│               ┌───────────────┐                          │
│               │   MongoDB     │  (optional)              │
│               │ summaries only│  no raw chats            │
│               └───────────────┘                          │
└──────────────────────────────────────────────────────────┘
```

### Core Invariant

> **Rule-based engine = single authority.**  
> LLM enhances phrasing realism only (never overrides detection).  
> MongoDB stores session summaries for learning (never raw conversations).  
> Both are optional — system operates fully without either.

---

## Key Features

| Feature                       | Description                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| **5-Layer Detection**         | Keyword → Pattern → India-specific → Behavioral → Confidence scoring                         |
| **18+ Scam Types**            | Digital arrest, courier, KYC, UPI, lottery, investment, crypto, and more                     |
| **Bilingual (EN + HI)**       | Full Hindi/Hinglish support — detection, agent responses, and LLM rephrasing                 |
| **Adaptive Agent**            | 15+ response pools × 2 languages (260+ phrases), context-aware rotation                      |
| **Intelligence Registry**     | Track UPI IDs, bank accounts, phones, emails, links — with frequency, confidence, recurrence |
| **Pattern Correlation**       | Fingerprint scam tactics, cross-session similarity scoring, recurring threat detection       |
| **Fraud Type Classification** | Professional labels (PAYMENT FRAUD, KYC PHISHING, etc.) with color-coded badges              |
| **Excel Export**              | One-click export of intelligence registry as styled .xlsx workbook                           |
| **Structured Reasoning**      | Detection verdicts with human-readable reasons explaining classification decisions           |
| **LLM Enhancement**           | Groq Llama 3.3 70B via REST API with circuit breaker + auto-fallback (1000 req/day free)     |
| **10 Simulation Scenarios**   | Bank, UPI, lottery, KYC, digital arrest, courier, investment, job, utility scams             |
| **Live Callbacks**            | Automatic government portal reporting when sufficient intel gathered                         |
| **Dark / Light Theme**        | Full dark + light theme system with CSS custom properties & glassmorphism                    |
| **Production Ready**          | Rate limiting, request timing, session TTL cleanup, configurable CORS                        |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm

### 1. Clone & Install

```bash
git clone https://github.com/sm-code-24/trusthoneypot.git
cd trusthoneypot

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
API_KEY=your-api-key-here
CALLBACK_URL=https://your-govt-portal-endpoint
GROQ_API_KEY=your-groq-api-key          # from console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile       # default model
MONGDB_URI=mongodb+srv://...            # optional
LLM_TIMEOUT_MS=8000                      # optional
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key-here
```

| Variable         | Required | Description                                   |
| ---------------- | -------- | --------------------------------------------- |
| `API_KEY`        | Yes      | API key for auth (`x-api-key` header)         |
| `CALLBACK_URL`   | Yes      | Government portal callback endpoint           |
| `GROQ_API_KEY`   | Yes      | Groq API key (from console.groq.com)          |
| `GROQ_MODEL`     | No       | Model name (default: llama-3.3-70b-versatile) |
| `MONGODB_URI`    | No       | MongoDB Atlas connection string               |
| `LLM_TIMEOUT_MS` | No       | LLM timeout in ms (default: 8000)             |

### 3. Run Development

```bash
# Both at once (recommended)
npm run dev

# Or separately:
npm run dev:backend   # Backend on :8000
npm run dev:frontend  # Frontend on :5173
```

Open **http://localhost:5173** in your browser.

### 4. Production Build

```bash
cd frontend && npm install && npm run build   # outputs to frontend/dist/
uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir app
```

---

## API Endpoints

| Method | Path                          | Auth | Description                                         |
| ------ | ----------------------------- | ---- | --------------------------------------------------- |
| `GET`  | `/`                           | No   | Health check                                        |
| `POST` | `/honeypot`                   | Yes  | Process scam message → analysis + reply             |
| `GET`  | `/sessions`                   | Yes  | List session summaries                              |
| `GET`  | `/sessions/{id}`              | Yes  | Session detail                                      |
| `GET`  | `/sessions/{id}/analysis`     | Yes  | Structured analysis with reasoning + fraud type     |
| `GET`  | `/patterns`                   | Yes  | Scam type & tactic aggregations                     |
| `GET`  | `/callbacks`                  | Yes  | Callback history                                    |
| `GET`  | `/intelligence/registry`      | Yes  | Tracked identifiers (filterable by type/risk)       |
| `GET`  | `/intelligence/registry/{id}` | Yes  | Identifier detail — frequency, confidence, sessions |
| `GET`  | `/intelligence/patterns`      | Yes  | Pattern correlation with similarity scoring         |
| `GET`  | `/intelligence/export`        | Yes  | Export registry as styled Excel (.xlsx)             |
| `POST` | `/intelligence/backfill`      | Yes  | Re-populate registry from existing session data     |

### POST `/honeypot` — Request

```json
{
  "sessionId": "uuid-string",
  "message": { "sender": "scammer", "text": "Your account is blocked..." },
  "conversationHistory": [],
  "response_mode": "rule_based"
}
```

### POST `/honeypot` — Response

```json
{
  "status": "success",
  "reply": "What? My account? But I used ATM yesterday only!",
  "reply_source": "rule_based",
  "scam_detected": true,
  "risk_score": 72,
  "risk_level": "high",
  "confidence": 0.85,
  "scam_type": "bank_impersonation",
  "scam_stage": "engaged",
  "intelligence_counts": { "upiIds": 0, "phoneNumbers": 1, "bankAccounts": 0 },
  "callback_sent": false,
  "fraud_type": "KYC PHISHING",
  "fraud_color": "amber",
  "detection_reasons": [
    "Identity verification scam pattern",
    "Urgency pattern detected"
  ],
  "pattern_similarity": 0.0
}
```

---

## Deployment

### Backend → Railway

**Live:** [https://trusthoneypot-api.up.railway.app](https://trusthoneypot-api.up.railway.app)

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Set environment variables in Railway dashboard (`API_KEY`, `GROQ_API_KEY`, `MONGODB_URI`, etc.)
3. Nixpacks auto-detects Python via `nixpacks.toml` and deploys with `uvicorn --app-dir app`
4. Watch patterns: `app/**`, `requirements.txt`, `nixpacks.toml`, `railway.json`

### Frontend → Vercel

**Live:** [https://trusthoneypot.tech](https://trusthoneypot.tech)

1. Import `frontend/` folder to [Vercel](https://vercel.com)
2. Set `VITE_API_URL=https://trusthoneypot-api.up.railway.app` and `VITE_API_KEY` in Vercel environment variables
3. Vercel auto-detects Vite and deploys
4. Custom domain: `trusthoneypot.tech`

---

## Project Structure

```
trusthoneypot/
├── app/
│   ├── main.py          # FastAPI entry + all endpoints
│   ├── agent.py         # Honeypot agent (15+ response pools)
│   ├── detector.py      # 5-layer scam detection engine
│   ├── extractor.py     # Intelligence extraction (8 types)
│   ├── intelligence.py  # Intelligence registry + pattern correlation (v2.1)
│   ├── llm.py           # Groq Llama 3.3 70B integration (httpx)
│   ├── db.py            # MongoDB persistence + indexes
│   ├── memory.py        # In-memory session state
│   ├── callback.py      # Government portal callback reporting
│   ├── auth.py          # API key middleware
│   └── models.py        # Pydantic request/response
├── frontend/
│   ├── src/pages/       # React page components
│   ├── src/api.js       # API client
│   ├── vercel.json      # Vercel deployment config
│   └── package.json
├── docs/
│   └── TECHNICAL_DETAILS.md
├── requirements.txt     # Python dependencies
├── nixpacks.toml        # Railway Nixpacks config
├── railway.json         # Railway deploy config
└── README.md
```

---

## Tech Stack

| Layer      | Technology                                       |
| ---------- | ------------------------------------------------ |
| Backend    | Python 3.13, FastAPI, Pydantic v2, Uvicorn       |
| Frontend   | React 18, Vite 6, Tailwind CSS 3, React Router 6 |
| LLM        | Groq Llama 3.3 70B Versatile via REST API        |
| Database   | MongoDB Atlas (optional)                         |
| Icons      | Lucide React                                     |
| Deployment | Railway (API), Vercel (UI)                       |

---

## License

MIT — Built with purpose for real-world scam intelligence gathering.

**© 2026 200 Hustlers — TrustHoneypot**
