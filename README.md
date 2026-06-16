# Yield Monitor Dashboard

A dark industrial dashboard for manual PCB/hardware test yield tracking.

Built with: FastAPI · SQLite · Chart.js · Selenium · OpenAI (optional)

---

## Project Structure

```
yield-monitor/
├── app/
│   ├── main.py              # FastAPI app — routes only
│   ├── chat.py              # OpenAI + rule-based chat helpers
│   ├── db/
│   │   └── database.py      # SQLite helpers — init, insert, seed, stats, daily
│   └── models/
│       └── schemas.py       # Pydantic models — TestCreate, ChatRequest, Message
├── templates/
│   └── index.html           # Single-page dashboard (vanilla JS + Chart.js)
├── static/
│   └── favicon.svg
├── tests/
│   └── test_yield.py        # Selenium validation script
├── requirements.txt
├── .env                     # Local API key (never commit)
├── .gitignore
└── .replit                  # Replit run config
```

---

## Local Setup

### 1. Create virtual environment

```bash
python -m venv .venv
```

Activate (Windows):
```bash
.venv\Scripts\activate
```

Activate (macOS/Linux):
```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
uvicorn app.main:app --reload
```

Open: [http://localhost:8000](http://localhost:8000)

On first run with an empty database, the app auto-seeds realistic sample data across 3 part numbers and 7 days.

---

## API Endpoints

| Method | Path            | Description                         |
|--------|-----------------|-------------------------------------|
| GET    | `/`             | Dashboard HTML                      |
| POST   | `/tests`        | Insert manual test record           |
| GET    | `/tests`        | List all test records               |
| GET    | `/stats`        | Yield stats by part number          |
| GET    | `/stats/daily`  | Yield stats filtered by date        |
| GET    | `/daily`        | Last 7 days test volume             |
| POST   | `/chat`         | Chatbot query (with history)        |
| GET    | `/script`       | View Selenium test script source    |
| GET    | `/docs`         | Swagger UI (FastAPI auto-docs)      |

### POST /tests — Request body

```json
{
  "serial_number": "SN-001",
  "part_number": "001PN001",
  "status": true
}
```

Allowed `part_number` values: `001PN001`, `002PN002`, `003PN003`

### POST /chat — Request body

```json
{
  "question": "What is the yield for 001PN001?",
  "history": [
    { "role": "user", "content": "How many units were tested?" },
    { "role": "assistant", "content": "65 total units tested." }
  ]
}
```

`history` is optional. When provided, the full conversation context is sent to the model for multi-turn conversations.

### GET /stats — Response shape

```json
[
  { "part_number": "001PN001", "total": 20, "passed": 16, "failed": 4, "yield_percent": 80.0 }
]
```

### GET /stats/daily?date=YYYY-MM-DD — Response shape

Same shape as `/stats` but filtered to a single date.

### GET /daily — Response shape

```json
[
  { "date": "2026-06-10", "count": 4 },
  { "date": "2026-06-11", "count": 7 }
]
```

---

## Chatbot Prompts

The Yield Assistant answers questions about live data. Try these:

```
What is the yield for 001PN001?
What is the yield for 002PN002?
What is the yield for 003PN003?
Which part number has the lowest yield?
How many units were tested today?
How many total units tested?
```

Without an OpenAI key, the chatbot uses rule-based fallback and answers all of the above deterministically from the database.

---

## OpenAI Chatbot (optional)

The chatbot works without a key using rule-based fallback.

### Local — use .env file

Edit `.env` in the project root:

```
OPENAI_API_KEY=sk-...
```

The app loads this automatically on startup via `python-dotenv`.

### Replit — use Secrets

Replit sidebar → **Secrets** → add:

```
Key:   OPENAI_API_KEY
Value: sk-...
```

### Render — use Environment

Render dashboard → your service → **Environment** → add:

```
OPENAI_API_KEY=sk-...
```

> Never commit `.env` to git. It is listed in `.gitignore`.

---

## Seed Data

On first startup with an empty database, the app inserts 65 sample records spread across the last 7 days:

| Part     | Total | Passed | Failed | Yield |
|----------|-------|--------|--------|-------|
| 001PN001 | 20    | 16     | 4      | 80%   |
| 002PN002 | 25    | 23     | 2      | 92%   |
| 003PN003 | 20    | 11     | 9      | 55%   |

On Replit, this data persists on disk between restarts. Seed only runs when the table is completely empty.

---

## Selenium Test

Requires Chrome and ChromeDriver installed and on PATH.

### Run against local server

```bash
python tests/test_yield.py
```

### Run against public URL

```bash
python tests/test_yield.py https://your-public-url
```

### Expected output (PASS case)

```
Opening dashboard: http://localhost:8000
  Record 1/5 inserted (PASS): SN-T001
  Record 2/5 inserted (PASS): SN-T002
  Record 3/5 inserted (PASS): SN-T003
  Record 4/5 inserted (FAIL): SN-T004
  Record 5/5 inserted (FAIL): SN-T005

Selecting part number: 001PN001

Expected yield: 60%
Actual yield:   60%
PASS
```

The script:
1. Opens the dashboard
2. Inserts 5 records for `001PN001` (3 passed, 2 failed)
3. Clicks the `001PN001` part chip
4. Reads the `#yield-value` element
5. Asserts it equals `60%`

---

## Deployment

### Replit (recommended)

1. Create a Python Repl named `yield-monitor`
2. Upload all project files (exclude `.env` — use Secrets instead)
3. The `.replit` file sets the run command automatically
4. Click **Run** — Replit assigns a public URL
5. Optional: add `OPENAI_API_KEY` in Replit Secrets sidebar

SQLite persists on Replit disk between restarts.

### Render

1. Push project to GitHub
2. New → Web Service → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Optional: add `OPENAI_API_KEY` in Environment settings

Note: Render free tier uses ephemeral disk — SQLite resets on redeploy. Seed data re-inserts automatically on each cold start.

---

## Dashboard Features

- **Daily Testing Volume** — bar chart, last 7 days; click any bar to filter Part Numbers Tested by that date; click again to reset
- **Part Number Distribution** — donut chart; click slice or chip button to select part
- **Yield Gauge** — CSS circular gauge, color matches selected part number
- **Manual Testing** — modal form: serial number, part number dropdown, live timestamp, pass/fail checkbox
- **View Script** — popup modal showing `tests/test_yield.py` source inline
- **Yield Assistant** — multi-turn chatbot; conversation history sent with each request; rule-based or OpenAI-powered

---

## Pre-Submission Checklist

- [ ] Dashboard loads at public URL
- [ ] `/docs` shows all endpoints
- [ ] `/script` shows Selenium test script source
- [ ] Manual Test modal opens and inserts records
- [ ] Charts refresh after insert
- [ ] Clicking daily bar filters Part Numbers Tested chart
- [ ] Clicking part chip updates gauge
- [ ] Chatbot responds to yield questions
- [ ] Chatbot maintains conversation history across messages
- [ ] Selenium test prints `PASS`
