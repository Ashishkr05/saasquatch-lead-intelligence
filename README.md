# Scout — SaaSquatch Lead Intelligence

[![CI](https://github.com/Ashishkr05/saasquatch-lead-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/Ashishkr05/saasquatch-lead-intelligence/actions/workflows/ci.yml)

**[Live demo](https://saasquatch-lead-intelligence-1.onrender.com/)** · [API health](https://saasquatch-lead-intelligence.onrender.com/health) · [Interactive API docs](https://saasquatch-lead-intelligence.onrender.com/docs)

The API uses Render's free service tier, so the first request after inactivity can take about a minute while the service wakes up.

> Turn 1,000 sourced companies into the 20 companies worth calling first.

Scout is an acquisition-fit scoring and lead-qualification layer designed for the workflow immediately after company discovery. A searcher imports a lead list, defines an acquisition thesis, and receives a transparent outreach queue with score reasons, data-quality warnings, red flags, a rule-based acquisition rationale, and a personalized outreach angle.

The entire demo works without an API key, paid data source, or AI service.

## Why I built this

SaaSquatch already helps acquisition entrepreneurs discover companies and organize outreach. The five-hour opportunity is therefore not to build another scraper—it is to improve the next decision: **which companies deserve a searcher's limited outreach time?**

More rows do not necessarily create more value. A searcher needs the right company, the right owner, and enough context to start a credible conversation. Scout turns a raw list into a prioritized, reviewable pipeline while keeping the searcher's acquisition thesis—not a black-box model—in control.

The core product loop is deliberately small:

```text
Source → Import → Score → Verify → Shortlist → Contact
```

## Reference analysis and product choice

I reviewed SaaSquatch's public product site and launch demo to understand the existing workflow rather than reproduce it. The public experience already communicates a broad sourcing and activation platform:

- company search and filtering by location and industry;
- employee-count, owner, revenue, contact, and LinkedIn enrichment;
- saving and exporting leads;
- email generation, LinkedIn messaging, and validators;
- AI company scoring.

Those capabilities make discovery and enrichment the product's clear strengths. They also change the opportunity for this challenge: another generic score would be redundant. The focused enhancement is an **acquisition-specific decision layer** where the buyer controls the thesis, every point is traceable, unknown data is separated from negative evidence, and the result moves directly into a review/shortlist/reject workflow.

The five-hour scope therefore contains two tightly connected features:

1. Explainable acquisition-fit scoring against a user-defined thesis.
2. A deterministic acquisition rationale and owner-outreach brief generated only from known fields.

This is the quality-first approach: improve prioritization between discovery and outreach instead of expanding scraper count. The product hypothesis is that better prioritization increases useful owner conversations per hour, which is more valuable than maximizing raw rows.

## Demo workflow

1. Open the seeded lead queue and review companies ranked by fit.
2. Select a company to inspect every scoring rule, positive signal, data gap, and red flag.
3. Edit the active acquisition thesis; every lead is rescored immediately.
4. Move leads between `Shortlisted`, `In review`, and `Rejected`.
5. Import `sample-import.csv` to see validation and deduplication.
6. Export shortlisted leads as a sales-ready CSV.

## Features

- Acquisition thesis for industries, locations, employee range, operating history, exclusions, and institutional-backing preference
- Deterministic 0–100 acquisition-fit scoring
- Full point-by-point score breakdown—no hidden model judgment
- Missing-data warnings that distinguish “unknown” from “bad fit”
- Red flags for thesis mismatch, size, geography, age, exclusions, and institutional backing
- Rule-based acquisition rationale and personalized owner outreach opener
- Shortlist, review, and reject workflow
- CSV import with required-field validation and two-level deduplication
- CSV export with scores, reasons, risks, rationale, and outreach copy
- Seeded synthetic dataset for a zero-configuration demo
- Visible source provenance on every lead and in exported CSVs
- Responsive, keyboard-accessible interface
- Responsible-data-use reminder in the product
- Automated scoring tests

## Quick start with Docker

Prerequisites: Docker Desktop with Docker Compose.

```bash
cd saasquatch-lead-intelligence
cp .env.example .env
docker compose up --build
```

Then open:

- Application: [http://localhost:8080](http://localhost:8080)
- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

No environment variable needs a secret. `OPENAI_API_KEY` is reserved as a future extension point and is unused by this version.

To stop the application:

```bash
docker compose down
```

PostgreSQL data persists in the `postgres_data` Docker volume. Use `docker compose down -v` only when you intentionally want to delete local demo data.

## Local development

After installing both backend and frontend dependencies once, start the complete local application from the repository root:

```bash
python scripts/dev.py
```

This starts the API and UI together and stops both when you press `Ctrl+C`. The Vite development server proxies `/api` to FastAPI, so the browser never depends on a hard-coded backend hostname.

### Backend

Python 3.12+ is recommended.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Without `DATABASE_URL`, the backend uses a local SQLite file for convenient development. Docker and production use PostgreSQL.

### Frontend

Node.js 20+ is recommended.

```bash
cd frontend
npm install
npm run dev
```

The development UI runs at [http://localhost:5173](http://localhost:5173) and proxies `/api` to the backend on port 8000.

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│ React + TypeScript                                      │
│ Queue · Thesis editor · Lead brief · CSV workflow       │
└───────────────────────┬─────────────────────────────────┘
                        │ REST / JSON + CSV
┌───────────────────────▼─────────────────────────────────┐
│ FastAPI                                                 │
│ Validation · Filtering · Statuses · Import/export       │
├─────────────────────────────────────────────────────────┤
│ Domain services                                         │
│ Deterministic scoring · Deduplication · Rule narratives │
└───────────────────────┬─────────────────────────────────┘
                        │ SQLAlchemy
┌───────────────────────▼─────────────────────────────────┐
│ PostgreSQL                                              │
│ Leads · Thesis · Score evidence · Workflow state        │
└─────────────────────────────────────────────────────────┘
```

### Exact technologies

| Layer | Technology | Reason |
| --- | --- | --- |
| UI | React 18, TypeScript, Vite, CSS | Fast iteration, typed data contracts, small production bundle |
| API | Python, FastAPI, Pydantic | Explicit validation and automatically documented endpoints |
| Persistence | PostgreSQL 16, SQLAlchemy 2 | Reliable transactional storage and a path to production scale |
| Local orchestration | Docker Compose | One reproducible command for UI, API, and database |
| Web serving | Nginx | Efficient static asset delivery and SPA fallback |
| Tests | Pytest | Focused coverage of the highest-risk business logic |

## Explainable scoring

| Criterion | Maximum | Behavior |
| --- | ---: | --- |
| Industry match | 25 | Full credit for a thesis keyword in industry/description |
| Company size | 20 | Full credit inside the range; 8 points when near the range |
| Geography | 15 | Full credit for a selected city, state, or region |
| Operating history | 15 | 10–15 points after the minimum, increasing transparently with operating history; partial credit when close |
| Owner identified | 10 | Owner or decision-maker available |
| Contact quality | 10 | Valid email = 6 points; valid phone = 4 points |
| Data completeness | 5 | Proportional across six core profile fields |
| Excluded keyword | −25 | Applied to industry and description |
| Institutionally backed | −20 | Applied when excluded by the thesis |

Scores are clamped to 0–100. `75+` is high priority, `50–74` requires review, and `<50` is low priority. Every awarded point and penalty is returned in `score_breakdown` with a human-readable explanation.

The scoring engine lives in `backend/app/scoring.py` and has no database or network dependency, so it is simple to test and reuse.

## Rule-based intelligence and future AI

The current `RuleBasedNarrativeProvider` creates acquisition rationales and outreach angles from known company fields. It never invents revenue, owner intent, or operational facts. Output clearly asks the user to verify financial performance and owner objectives.

`NarrativeProvider` is a small protocol boundary. A future LLM implementation could be selected in `get_narrative_provider()` without changing the scoring engine or API contract. A safe production implementation should:

- send only permitted company data;
- cache by normalized domain + thesis version;
- return structured output;
- fall back to the deterministic provider on timeout or validation failure;
- keep generated claims clearly labeled and reviewable.

No AI SDK is installed and no external AI request is made in this submission.

## Data model

### `theses`

Stores the active strategy: target industries and geographies, employee bounds, minimum age, exclusions, and backing preference.

### `leads`

Stores company/contact inputs, source, workflow status, score, priority, evidence arrays, warnings, red flags, rationale, outreach angle, and timestamps. JSON columns preserve the exact score evidence shown to the evaluator.

For a larger multi-user release, thesis and lead records would gain `workspace_id`; score runs would move to an immutable `lead_score_versions` table for audit history.

## CSV contract

Only `company_name` is required. Recommended headers:

```text
company_name,domain,website,industry,location,employee_count,year_founded,
owner_name,owner_title,email,phone,description,estimated_revenue_m,
institutionally_backed,source
```

Import safeguards:

- UTF-8 CSV only, maximum 5 MB
- domain normalization (`https://`, `www.`, and URL paths removed)
- deduplication by normalized domain
- fallback deduplication by case-insensitive company + location
- invalid rows reported without failing the whole file
- numeric ranges, field lengths, founding years, and website schemes validated before insertion
- no network enrichment or scraping during import
- UTF-8 BOM on exports for reliable Excel and Windows compatibility
- spreadsheet-formula escaping on every exported text field

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service readiness and no-AI-required signal |
| `GET` | `/api/metrics` | Pipeline summary |
| `GET` | `/api/thesis` | Active acquisition thesis |
| `PUT` | `/api/thesis` | Save thesis and rescore all leads |
| `GET` | `/api/leads` | Search, filter, and sort leads |
| `GET` | `/api/leads/{id}` | Complete lead intelligence brief |
| `PATCH` | `/api/leads/{id}/status` | Shortlist, review, or reject |
| `POST` | `/api/leads/import` | Validate, deduplicate, score, and import CSV |
| `GET` | `/api/leads-export.csv` | Export a workflow segment |

FastAPI exposes request/response examples and schemas at `/docs`.

## Performance and caching strategy

This challenge does not add Redis simply to claim another technology. Current scoring is CPU-cheap and deterministic; database records already cache the computed score and narrative. Reads therefore avoid recalculating the lead queue.

At production scale:

1. Thesis updates would enqueue batched rescore jobs instead of running synchronously.
2. PostgreSQL indexes on `score`, `priority`, `status`, `domain`, `industry`, and `location` support common queue operations.
3. Imports would stream to object storage and process in background workers.
4. Redis would cache workspace metrics and future enrichment/LLM results using `domain:thesis_version` keys.
5. Cursor pagination would replace the intentionally simple demo list response.

This keeps the five-hour version honest while showing a concrete scaling path.

## Deployment

The public challenge demo uses **Render and Neon**:

- Render Static Sites builds and hosts the React application.
- Render Web Services runs FastAPI on Python 3.12 and exposes the health and API endpoints.
- Neon provides managed PostgreSQL with encrypted connections and persistent demo data.
- Render supplies HTTPS for both public services. `VITE_API_URL` connects the static build to the API, and `CORS_ORIGINS` restricts browser access to the deployed frontend.
- Both services deploy automatically from `main`; secrets remain in provider environment variables and are never committed.

The repository also includes a portable single-server deployment. Docker Compose builds Nginx, FastAPI, and PostgreSQL; health-gated startup ensures the database is ready before the API and the API before the frontend. Ports bind to host loopback so a host-level Caddy or Nginx proxy can be the only public entry point. On an Ubuntu server:

1. Install Docker Engine and the Compose plugin.
2. Clone the repository and copy `.env.example` to `.env`.
3. Replace the demo database password and configure the public CORS origin.
4. Run `docker compose up -d --build`.
5. Terminate HTTPS with Caddy or Nginx in front of `127.0.0.1:8080`.

For a production workload, I would move beyond free-tier hosting, add automated database backups and error monitoring, and use a managed PostgreSQL plan with an explicit availability and recovery policy.

## Testing

```bash
pytest

cd frontend
npm run lint
npm test
npm run build
npm audit --audit-level=high
```

Tests cover complete API workflows, metric consistency, imports, duplicate handling, invalid files and values, spreadsheet-safe exports, filter allowlists, perfect fits, exclusion penalties, operating-history differentiation, invalid/future data, contact-format language, missing-data behavior, unrestricted criteria, and deterministic repeatability.

See [SECURITY.md](SECURITY.md) for implemented safeguards and the explicit production-security boundary.

## UX decisions

- The evaluator lands directly on a useful seeded queue—no signup or empty-state setup.
- Score color is never the only signal; each band has a text label.
- A lead drawer preserves queue context while revealing deeper evidence.
- “Missing” is visually distinct from a negative fit signal.
- Thesis criteria and weights are visible before rescoring.
- Outreach copy is one click away but labeled for verification.
- Status controls remain available at the bottom of the lead brief.
- The mobile layout keeps the complete qualification workflow usable.

## Responsible use

This project uses synthetic `.example` domains and fictional contacts. It does not scrape websites, bypass CAPTCHAs, use proxies, or include private datasets. In production, users should use lawfully obtained data, respect website terms and opt-outs, limit collection to business-relevant fields, and verify generated outreach before sending it.

Seeded records are explicitly labelled `Synthetic demo`. Leads imported through the bundled `sample-import.csv` retain the `Sample CSV` source label, while user CSVs default to `CSV import` when no source is supplied.

## Five-hour tradeoffs

Deliberately excluded:

- scraper and third-party enrichment integrations;
- authentication, multi-tenancy, and billing;
- automatic email sending;
- background queues and Redis;
- unverified AI-generated company claims;
- dashboards that do not help the next outreach decision.

These exclusions preserve a polished vertical slice around the highest-value decision.

## What I would build next

The most valuable next step is an outcome feedback loop:

```text
Fit score → Outreach → Reply → Owner meeting → LOI
```

Store outcomes by criterion, then show which thesis signals actually correlate with owner engagement. Rules should remain visible and user-controlled; outcome data would recommend weight changes instead of silently changing the score.

Additional production steps would include HubSpot/Salesforce export, third-party contact verification, Alembic migrations, score version history, bulk status actions, background imports, and role-based workspaces.

## Repository map

```text
.
├── backend/
│   ├── app/                 # API, models, scoring, narratives, seed logic
│   ├── data/                # Synthetic demo leads
│   └── tests/               # Deterministic scoring tests
├── frontend/
│   └── src/                 # React application and typed API client
├── docs/                    # Concise walkthrough video script
├── docker-compose.yml
├── sample-import.csv
└── .env.example
```

## Reference

The public SaaSquatch site and launch/demo post were reviewed only to understand the existing searcher workflow, advertised scoring, and emphasis on email personalization. This project is an independent acquisition-decision extension, not a clone of SaaSquatch.

- [SaaSquatch Leads public product site](https://www.saasquatchleads.com/)
- [SaaSquatch launch/demo post](https://www.linkedin.com/posts/kevinhshong_saasquatch-zerotoone-searchfunds-activity-7343665530462945281-hOJ7)
