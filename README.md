# TrustHoneypot — Scam Intelligence Command Center

> **India AI Impact Buildathon 2025 — Problem Statement 2**  
> Team: **200 Hustlers** (Shailav · Bhupendra · Shivam · Gungun)

An agentic honeypot that **engages scammers** with believable human-like conversations, **extracts financial intelligence** (UPI IDs, bank accounts, phone numbers, Aadhaar, PAN, phishing links), and **reports findings** via automated callbacks — all in real-time.

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
│  │ 5-layer  │  │ 13 pools │  │ 8 types   │  │  GUVI  │ │
│  │ scoring  │  │ rotation │  │ regex+NLP │  │endpoint│ │
│  └──────────┘  └──────┬───┘  └───────────┘  └────────┘ │
│                       │                                  │
│               ┌───────▼───────┐                          │
│               │ LLM Rephraser │  (optional)              │
│               │ Gemini 3 Flash│  timeout → fallback      │
│               │   Preview     │                          │
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

| Feature                     | Description                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------ |
| **5-Layer Detection**       | Keyword → Pattern → India-specific → Behavioral → Confidence scoring                 |
| **18+ Scam Types**          | Digital arrest, courier, KYC, UPI, lottery, investment, crypto, and more             |
| **Adaptive Agent**          | 13 response pools (120+ phrases), intelligent rotation to avoid repetition           |
| **Intelligence Extraction** | UPI IDs, bank accounts, phones, Aadhaar, PAN, emails, phishing links, crypto wallets |
| **LLM Enhancement**         | Optional Gemini 3 Flash Preview rephrasing with 1.4s timeout + auto-fallback         |
| **Live Callbacks**          | Automatic GUVI platform reporting when sufficient intel gathered                     |
| **Dark / Light Theme**      | Full dark + light theme system with CSS custom properties & glassmorphism            |
| **Responsive Design**       | Mobile-first with hamburger menu, works on all screen sizes                          |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ & npm

### 1. Clone & Install

```bash
git clone https://github.com/your-repo/trusthoneypot.git
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
CALLBACK_URL=https://your-guvi-callback-endpoint
GEMINI_API_KEY=your-google-ai-key       # optional
GEMINI_MODEL=gemini-3-flash-preview      # optional
MONGODB_URI=mongodb+srv://...            # optional
LLM_TIMEOUT_MS=1400                      # optional
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key-here
```

| Variable         | Required | Description                                  |
| ---------------- | -------- | -------------------------------------------- |
| `API_KEY`        | Yes      | API key for auth (`x-api-key` header)        |
| `CALLBACK_URL`   | Yes      | GUVI callback endpoint                       |
| `GEMINI_API_KEY` | No       | Google AI API key (LLM phrasing)             |
| `GEMINI_MODEL`   | No       | Model name (default: gemini-3-flash-preview) |
| `MONGODB_URI`    | No       | MongoDB Atlas connection string              |
| `LLM_TIMEOUT_MS` | No       | LLM timeout in ms (default: 1400)            |

### 3. Run Development

```bash
# Terminal 1 — Backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

### 4. Production Build

```bash
cd frontend && npm run build   # outputs to frontend/dist/
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## API Endpoints

| Method | Path             | Auth | Description                             |
| ------ | ---------------- | ---- | --------------------------------------- |
| `GET`  | `/`              | No   | Health check                            |
| `POST` | `/honeypot`      | Yes  | Process scam message → analysis + reply |
| `GET`  | `/sessions`      | Yes  | List session summaries                  |
| `GET`  | `/sessions/{id}` | Yes  | Session detail                          |
| `GET`  | `/patterns`      | Yes  | Scam type & tactic aggregations         |
| `GET`  | `/callbacks`     | Yes  | Callback history                        |
| `GET`  | `/system/status` | Yes  | API, LLM, MongoDB status                |

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
  "callback_sent": false
}
```

---

## Deployment

### Backend → Railway

1. Connect your GitHub repo to [Railway](https://railway.app)
2. Set environment variables in Railway dashboard
3. Railway auto-detects `Procfile` and deploys

### Frontend → Vercel

1. Import `frontend/` folder to [Vercel](https://vercel.com)
2. Set `VITE_API_URL` to your Railway backend URL
3. Vercel auto-detects Vite and deploys

---

## Project Structure

```
trusthoneypot/
├── app/
│   ├── main.py          # FastAPI entry + all endpoints
│   ├── agent.py         # Honeypot agent (13 response pools)
│   ├── detector.py      # 5-layer scam detection engine
│   ├── extractor.py     # Intelligence extraction (8 types)
│   ├── llm.py           # Gemini Flash integration
│   ├── db.py            # MongoDB persistence
│   ├── memory.py        # In-memory session state
│   ├── callback.py      # GUVI callback reporting
│   ├── auth.py          # API key middleware
│   └── models.py        # Pydantic request/response
├── frontend/
│   ├── src/pages/       # React page components
│   ├── src/api.js       # API client
│   ├── vercel.json      # Vercel deployment config
│   └── package.json
├── docs/
│   └── TECHNICAL_DETAILS.md
├── requirements.txt
├── Procfile             # Railway / Heroku
├── railway.json         # Railway config
├── .env.example
└── README.md
```

---

## Tech Stack

| Layer      | Technology                                       |
| ---------- | ------------------------------------------------ |
| Backend    | Python 3.13, FastAPI, Pydantic v2, Uvicorn       |
| Frontend   | React 18, Vite 6, Tailwind CSS 3, React Router 6 |
| LLM        | Google Gemini 3 Flash Preview (optional)         |
| Database   | MongoDB Atlas (optional)                         |
| Icons      | Lucide React                                     |
| Deployment | Railway (API), Vercel (UI)                       |

---

## License

MIT — Built with purpose for the India AI Impact Buildathon 2025.

**© 2025 200 Hustlers — TrustHoneypot**
