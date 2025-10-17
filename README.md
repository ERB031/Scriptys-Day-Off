# Scripty's Day Off

All-in-one film production breakdown, budgeting, and scheduling platform powered by **AI**. Upload a Final Draft (`.fdx`) script to:
- 🤖 **Automatically generate scene synopses** using Google Gemini
- 🎬 **AI-powered element detection** - props, wardrobe, vehicles, stunts, and more
- 📋 **Professional breakdown sheets** with all production elements organized by department
- 💰 **Smart cost estimates** based on scene complexity
- 📅 **Auto-schedule shoots** grouped by location and cast

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
- **Google Gemini API key** (for AI-powered synopsis generation and element detection) - Get one free at [Google AI Studio](https://aistudio.google.com/app/apikey)

## Backend Setup (FastAPI)

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate             # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure environment variables (create `backend/.env`):

```env
DATABASE_URL=postgresql+asyncpg://scripty:password@localhost:5432/scriptys_day_off
CORS_ORIGINS=["http://localhost:3000"]
GOOGLE_API_KEY=your_google_gemini_api_key_here
CHAT_MODEL=gemini-1.5-flash
```

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | Async SQLAlchemy connection string | `postgresql+asyncpg://scripty:password@localhost:5432/scriptys_day_off` |
| `CORS_ORIGINS` | JSON array of allowed origins | `["http://localhost:3000"]` |
| `GOOGLE_API_KEY` | **Required** for AI features (synopsis + element detection) | — |
| `CHAT_MODEL` | Gemini model to use | `gemini-1.5-flash` |

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
- **Scene Grid** — Interactive table (TanStack Table) summarizing scenes with AI-generated synopses, lengths, cast, props, and baseline costs.
- **Breakdown Sheets** — Professional production breakdown sheets with:
  - 📝 AI-generated scene synopses (1-2 sentences)
  - 🎭 Cast members and extras
  - 🎨 Props, set dressing, wardrobe
  - 💄 Makeup & hair requirements
  - 🚗 Vehicles and animals
  - 💥 Special effects and stunts
  - 🎵 Sound FX and music cues
- **Day Builder** — Auto-scheduler summary with day cards, totals, and quick CSV/PDF export buttons.

## AI-Powered Features 🤖

### Scene Synopsis Generation
**Powered by Google Gemini 1.5 Flash**

When you upload a script, Gemini automatically generates professional 1-2 sentence synopses for each scene:
- ⚡ **Fast**: 3-5 seconds for full screenplay
- 💰 **Affordable**: ~$0.005 per screenplay (half a cent!)
- 🎯 **Quality**: Highlights dramatic beats and key characters
- 📋 **Integrated**: Appears in breakdown sheets and scene details

See [GEMINI_SYNOPSIS_FEATURE.md](GEMINI_SYNOPSIS_FEATURE.md) for details.

### Automated Element Detection
**Powered by Google Gemini 1.5 Flash**

Gemini analyzes each scene and automatically detects production elements:
- 🎬 **10 Categories**: Cast, Extras, Props, Set Dressing, Wardrobe, Makeup & Hair, Vehicles/Animals, Sound FX, Special Effects, Stunts
- ⚡ **Fast**: 5-10 seconds for full screenplay breakdown
- 💰 **Affordable**: ~$0.008 per screenplay (less than 1 cent!)
- 🔄 **Smart**: Merges AI-detected elements with parser-detected ones
- 📋 **Production-Ready**: Elements appear in breakdown sheets immediately

See [GEMINI_ELEMENT_DETECTION.md](GEMINI_ELEMENT_DETECTION.md) for details.

### Cost Estimation
Cost estimates are calculated using deterministic heuristics based on:
- Crew packages from rate cards
- Logistics costs (permits, company moves)
- Per-performer costs scaled by pages per day
- Scene complexity (page count, cast size)

## CSV & PDF Exports

Downloadable from the Day Builder panel. `fpdf2` generates lean PDF summaries; CSV exports embed day-level and
per-scene rows for spreadsheet workflows.

## Deployment

### Backend (FastAPI on Render.com)

The FastAPI backend is deployed on [Render.com](https://render.com) with the following configuration:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
start-Scripty
```

### Database (Neon Console)

PostgreSQL database is hosted on [Neon Console](https://neon.tech), a serverless Postgres platform optimized for modern applications.

**Production Environment Variables:**
```env
DATABASE_URL=postgresql+asyncpg://[username]:[password]@[neon-host]/scriptys_day_off
CORS_ORIGINS=["https://your-frontend-domain.com"]
GOOGLE_API_KEY=your_google_gemini_api_key_here
CHAT_MODEL=gemini-1.5-flash
```

**Database Initialization:**
After creating your Neon database, run the schema and seed scripts:
```bash
psql [your-neon-connection-string] < backend/database/schema.sql
psql [your-neon-connection-string] < backend/database/seed_rate_cards.sql
```

## Next Steps / Roadmap

- ✅ AI-powered scene synopsis generation (Google Gemini)
- ✅ AI-powered element detection for breakdown sheets
- ✅ Professional breakdown sheet export
- 🔄 Drag-and-drop manual day editing with persistence
- 🔄 Regenerate synopses/elements for individual scenes
- 🔄 Manual element editing in UI
- 🔄 PDF breakdown sheet export
- 🔄 Inline cost overrides synced with rate cards per production

## Development Tips

- Adjust scheduler rules in `backend/app/services/scheduler.py` (`max_pages_per_day`, etc.).
- Seed additional rate cards by extending `seed_rate_cards.sql`.
- Tailwind utilities are enabled; extend styling inside `frontend/tailwind.config.ts`.

Happy scheduling!

