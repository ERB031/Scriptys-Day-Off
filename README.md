# Scripty's Day Off

All-in-one film production breakdown, budgeting, and scheduling platform. Upload a Final Draft (`.fdx`) script to
automatically create scene breakdowns, generate AI-ready cost baselines, and draft a shooting schedule grouped by
shared locations and cast.

## Project Structure

```
.
├── backend/      # FastAPI service (FDX ingestion, scheduling, exports)
├── frontend/     # Next.js UI (scene grid, day builder)
├── backend/database/schema.sql          # PostgreSQL schema
├── backend/database/seed_rate_cards.sql # Baseline rate cards
└── README.md
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 14+
- Optional: OpenAI API key (for chat model `gpt-4.1-mini` cost estimating fallback)

## Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate             # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure environment variables (copy `.env.example` if you make one):

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | Async SQLAlchemy connection string | `postgresql+asyncpg://scripty:password@localhost:5432/scriptys_day_off` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:3000` |
| `OPENAI_API_KEY` | Optional. Enables GPT-4.1-mini cost estimates | — |

Initialize the database:

```bash
createdb scriptys_day_off
psql scriptys_day_off < backend/database/schema.sql
psql scriptys_day_off < backend/database/seed_rate_cards.sql
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Key API Endpoints

- `POST /ingest/script` — Upload `.fdx` screenplay, returns parsed scenes and upload id.
- `POST /ingest/calculate/eighths` — Utility to translate script snippets into 1/8th page counts.
- `GET /scenes` — Latest upload scenes (or `?upload_id=UUID`).
- `GET /schedule/days` — Auto-scheduler preview grouped by location/cast.
- `POST /schedule/auto` — Force a fresh auto-schedule for a specific upload.
- `GET /schedule/export.csv` and `GET /schedule/export.pdf` — Day budget exports (optionally `?upload_id=`).
- `GET /rate_cards` — Default rate cards loaded from the seed script.

## Frontend Setup (Next.js 14 App Router)

```bash
cd frontend
npm install
```

Create `.env.local`:

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Run the dev server:

```bash
npm run dev
```

The UI includes:

- **Upload Panel** — Select your `.fdx` file. The backend parses sluglines, cast, and calculates 1/8th page lengths.
- **Scene Grid** — Interactive table (TanStack Table) summarising scenes, lengths, cast, props, and baseline costs.
- **Day Builder** — Auto-scheduler summary with day cards, totals, and quick CSV/PDF export buttons.

## Cost Estimation Strategy

An OpenAI `gpt-4.1-mini` prompt can be enabled to refine costs when `OPENAI_API_KEY` is present. Without a key, the API
falls back to deterministic heuristics built from the seeded rate cards (crew package, logistics, and per-performer
costs scaled by pages per day).

## CSV & PDF Exports

Downloadable from the Day Builder panel. `fpdf2` generates lean PDF summaries; CSV exports embed day-level and
per-scene rows for spreadsheet workflows.

## Next Steps / Roadmap

- Prop extraction for richer breakdown metadata (currently placeholders).
- Drag-and-drop manual day editing with persistence.
- PDF ingestion fallback using the seeded rate cards.
- Inline cost overrides synced with rate cards per production.

## Development Tips

- Adjust scheduler rules in `backend/app/services/scheduler.py` (`max_pages_per_day`, etc.).
- Seed additional rate cards by extending `seed_rate_cards.sql`.
- Tailwind utilities are enabled; extend styling inside `frontend/tailwind.config.ts`.

Happy scheduling!

