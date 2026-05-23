# CLAUDE.md — Product Intelligence Dashboard

> Persistent context for Claude Code. Read this fully before writing or editing any code. This file is the single source of truth for scope, architecture, and working conventions. When in doubt, re-read it.

---

## 0. What this project is

A deployed, end-to-end **Product Intelligence Dashboard for e-commerce sellers** (we are a seller on **Flipkart**). A seller uploads a product **video** (primary) or a product **CSV** (fallback), the system extracts product data, validates listing quality, optionally enhances the title, compares our price against competitor prices, and raises severity-classified alerts. Long operations run as tracked **jobs**.

This is a **recruiter-facing take-home assignment** (48–72h). The reviewer will open the deployed app, read the README, and may run it locally. The goal is a **complete, reliable, well-explained product flow** — not perfect AI accuracy.

---

## 1. THE GOLDEN RULE: complete the loop, then add bonuses

The single biggest scoring lever is **end-to-end completion (25%)**. The assignment explicitly says *"Mocked or simulated integrations are acceptable"* and *"We value a complete, reliable, well-explained product flow more than a partially working integration with fragile external dependencies."*

Build order is non-negotiable:

1. **Build the entire flow end-to-end first**, with every external dependency hidden behind an **interface (Protocol)**. Some impls are real (OCR — see §2), some are mocked (competitor prices, notifications). The app must work start-to-finish before any bonus work.
2. **Deploy early.** Get a hello-world frontend + backend deployed and talking in the first work session. Re-deploy continuously. A deployed-but-incomplete app scores; a complete-but-not-deployed app fails a hard deliverable.
3. **Only then add bonuses** (§10), and only at the implementation layer behind a seam. A bonus must NEVER require touching the API contract, the data model, or the UI.

**If any integration becomes flaky or threatens the demo, fall back to its mock and document it.** Reliability > realism. This applies even to OCR: the real tesseract path is the default, but it must degrade to the mock extractor if frame extraction or OCR fails, so the demo never breaks.

---

## 2. Tech stack (locked)

**Backend:** Python 3.12, **FastAPI**, **PostgreSQL** via **SQLAlchemy 2.x (async)** + **Alembic** migrations. **Pydantic v2** for request/response schemas and validation. `python-multipart` for file uploads. `pytest` + `httpx`/`pytest-asyncio` for tests. `uv` (or `pip` + `requirements.txt`) for deps — pick one and document it.
**OCR / extraction (REAL, default):** `ffmpeg` (via `imageio-ffmpeg` or system ffmpeg) for frame extraction, **`pytesseract`** + system `tesseract-ocr` for OCR, `Pillow`/`opencv-python-headless` for frame preprocessing. A deterministic **mock extractor is the mandatory fallback** when OCR is unavailable or returns nothing usable.
**Frontend:** React + TypeScript + Vite. TanStack Query for server state + job polling. One component library (shadcn/ui or Ant Design — pick one, stay consistent). Recharts for the price-history chart.
**Jobs:** FastAPI `BackgroundTasks` (or a small asyncio worker) backed by a `jobs` table (PENDING → RUNNING → COMPLETED/FAILED/PARTIALLY_COMPLETED). No external queue for the minimum version; design the runner so a real queue (Celery/RQ/arq) could replace it behind the same interface.
**Deployment:** Frontend → **Vercel**. Backend + Postgres → **Render**. The backend Docker image / Render build **must install `ffmpeg` and `tesseract-ocr`** as system packages — verify this in Slice 0, because a missing system binary is the most likely deploy-time failure.
**Repo:** Single GitHub repo, two top-level folders: `/backend` and `/frontend`. Optional root `docker-compose.yml` for local dev (bonus).

Do not introduce new frameworks, ORMs, or state libraries without asking first.

---

## 3. Architecture & the interface seams

Everything external lives behind a `typing.Protocol` interface in `backend/app/services/`. This is what makes real↔mock a config flip, not a rewrite.

```
backend/app/
  services/
    extraction/
      extractor.py            # Protocol: extract(video_path) -> ExtractedProduct
      ocr_extractor.py        # REAL DEFAULT: ffmpeg frame grab + pytesseract OCR + attribute parse
      mock_extractor.py       # deterministic fallback (also used in tests)
      factory.py              # picks impl from EXTRACTION_PROVIDER env; OCR falls back to mock on failure
    competitor/
      competitor.py           # Protocol: get_prices(product) -> list[CompetitorPrice]
      mock_competitor.py      # deterministic per-platform jitter around our price (DEFAULT)
      csv_competitor.py       # ingest uploaded competitor CSV
      factory.py
    notifications/
      notifier.py             # Protocol: send(alert) -> None
      inapp_notifier.py       # writes to alerts table (DEFAULT)
      email_notifier.py       # BONUS: SMTP; no-op + log if SMTP env missing
      factory.py
  jobs/
    runner.py                 # async runner; updates job row + progress 0..100
    pipeline.py               # extract -> validate -> enhance -> price -> alert
  validation/
    rules.py                  # pure functions, one per rule; fully unit-tested
    severity.py
  domain/
    enhance_title.py          # pure: (attributes, keywords) -> enhanced title + reason
    keywords.py               # mock trending-keyword map per category
  api/
    routes/                   # thin routers, Pydantic-validated, call services
    deps.py                   # DI: db session, service factories
  db/
    models.py                 # SQLAlchemy models
    session.py
  schemas/                    # Pydantic request/response models
  core/
    config.py                 # pydantic-settings; all env vars; safe defaults
  alembic/                    # migrations
  seed.py                     # demo data so deployed dashboard is populated on first boot
```

**Rules for the seams:**
- A router NEVER imports a concrete impl directly — only the `factory`.
- The OCR extractor MUST wrap its work in try/except and fall back to the mock extractor (logging that it did) if ffmpeg/tesseract is missing or extraction yields nothing. The app must run with **zero API secrets configured**.
- Mocks are **deterministic** (seeded by `sku_id`) so the demo and tests are reproducible.

---

## 4. Data model (SQLAlchemy + Alembic)

Keep it normalized and obvious. Core tables:

- **products**: `id, sku_id (unique), product_title, description, brand, category, price, mrp, image_url, product_url, availability, color, size, material, source (VIDEO|CSV|MANUAL), quality_score, created_at, updated_at`. `sku_id` uniqueness is the DB-level duplicate-SKU guard.
- **jobs**: `id, type (VIDEO_EXTRACTION|CSV_VALIDATION|PRICE_REFRESH), status, progress (0–100), started_at, completed_at, error, result_summary (JSONB)`. Failed-row details go in `result_summary`.
- **listing_issues**: `id, product_id (fk), type, severity (HIGH|MEDIUM|LOW), message, suggested_fix, created_at`.
- **competitor_prices**: `id, product_id (fk), platform, competitor_url, competitor_price, currency, last_checked_at`.
- **alerts**: `id, product_id (fk, nullable), type, severity, message, status (OPEN|ACKNOWLEDGED), created_at`. This is the in-app notification log.
- **enhanced_titles**: `id, product_id (fk), original_title, attributes (JSONB), keywords (JSONB/array), enhanced_title, reason, created_at`.

All schema changes go through **Alembic migrations** (no manual SQL drift). Ship `seed.py` so the deployed DB has demo data on first boot — the reviewer should see a populated dashboard immediately.

---

## 5. API contract (do not deviate without asking)

Match the assignment's suggested endpoints so the reviewer recognizes them:

```
POST   /upload-video                          -> { job_id }            (multipart; creates VIDEO_EXTRACTION job)
POST   /upload-products-csv                   -> { job_id, inserted, skipped }
GET    /jobs                                  -> Job[]
GET    /jobs/{job_id}                         -> Job (poll for progress)
GET    /products                              -> Product[]  (filters: ?severity=&category=&alert=)
GET    /products/{sku_id}                     -> Product + issues + competitor_prices + enhanced_title
PATCH  /products/{sku_id}                     -> manual edit of extracted data (re-runs validation)
GET    /dashboard/quality-summary             -> totals, issue counts by severity, weak listings, missing-image/invalid-price counts, avg quality score
GET    /products/{sku_id}/issues              -> ListingIssue[]
POST   /products/{sku_id}/enhance-title       -> EnhancedTitle
POST   /competitor-prices/upload              -> ingest competitor CSV
POST   /competitor-prices/refresh             -> { job_id }            (creates PRICE_REFRESH job)
GET    /products/{sku_id}/competitor-prices   -> CompetitorPrice[] + comparison block
GET    /alerts                                -> Alert[]   (filters: ?severity=&status=)
POST   /alerts/rules                          -> optional, configurable thresholds
GET    /health                                -> { ok: true }
```

Conventions: JSON everywhere; FastAPI's automatic OpenAPI docs at `/docs` (this satisfies the Swagger bonus for free — keep schemas clean). Consistent error envelopes via exception handlers; proper status codes (400/404/409/422/500). CORS restricted to the frontend origin (env-driven via `CORS_ORIGIN`).

---

## 6. Business logic specifics (get these exactly right — 20% of the grade)

**Validation rules** (each a pure function in `rules.py`, each unit-tested):
| Rule | Severity |
|---|---|
| Missing title | HIGH |
| Very short title (< ~15 chars or < 3 words) | MEDIUM |
| Missing brand | MEDIUM |
| Invalid price (<=0 or non-numeric) | HIGH |
| MRP lower than selling price | HIGH |
| Missing image | HIGH |
| Broken image URL (bad format / unreachable; mockable) | MEDIUM |
| Duplicate SKU | HIGH |
| Weak description (< ~50 chars) | LOW |
| Missing important attributes (color/size/material/category) | MEDIUM |
| Out of stock | LOW |

**Quality score**: deterministic function of issues — start at 100, subtract weighted penalties (HIGH −20, MEDIUM −10, LOW −3), floor at 0. Document the formula in the README.

**Title enhancement** (only when the flag is on): original title → extracted attributes → suggested keywords (from the mock per-category trending map) → enhanced title → human-readable reason. Use the assignment's Nike example as a test fixture.

**Alert rules** (implement all):
- HIGH if product has no title, no price, or invalid price.
- HIGH if our Flipkart price is **> 10% higher** than the lowest competitor price.
- MEDIUM if title is weak or important attributes missing.
- MEDIUM if a competitor price **drops significantly** during a refresh (read the old price before writing the new one).
- LOW for weak description or out-of-stock.

**Price comparison block**: lowest, highest, average competitor price, price gap (absolute), percentage difference vs our price, and a recommended action string (e.g. "Reduce price by INR X to match lowest competitor").

---

## 7. Jobs

`POST /upload-video`, `POST /upload-products-csv` (when large), and `POST /competitor-prices/refresh` create a Job row and return immediately with `job_id`. The runner processes asynchronously, updating `progress` and `status`. The frontend polls `GET /jobs/{id}`. Use `PARTIALLY_COMPLETED` when a CSV has some valid and some failed rows; surface failed-row reasons in `result_summary`. Always set `error` on FAILED. Wrap pipeline stages in try/except so one bad product never fails the whole job — and so an OCR failure on the video falls back to the mock extractor rather than failing the job.

---

## 8. Frontend screens (15%)

Build all of: **Upload** (video + CSV fallback + enhance-title toggle), **Jobs list / processing** (live polling, progress bar, status chips), **Quality dashboard** (summary cards + issue-by-severity counts), **Product list table** (filters: severity / category / alert status), **Product detail** (extracted data, editable fields, issues with suggested fixes, enhanced-title block, competitor price table + comparison), **Alerts history** (severity filter, acknowledge action), and a **Refresh prices** button. Clean and obviously navigable — the reviewer should never wonder where to click. Loading and error states everywhere; job polling must never hang the UI.

---

## 9. Deployment & deliverables (10%, but gating)

- Frontend on Vercel; backend + Postgres on Render. Frontend reads backend URL from `VITE_API_URL`; backend reads `DATABASE_URL`, `CORS_ORIGIN`, `EXTRACTION_PROVIDER`, and optional SMTP envs via `pydantic-settings`.
- **Backend image/build must install `ffmpeg` and `tesseract-ocr`.** On Render, use a Dockerfile that `apt-get install -y ffmpeg tesseract-ocr`. Confirm OCR works on the deployed instance in Slice 0 — do not discover this at the end.
- Seed the deployed DB so the dashboard is populated on first visit.
- README must cover: tech stack, run-locally steps (including system deps), how to use the deployed app, API docs (link to `/docs`), data model, deployment links, **assumptions**, **what is real vs mocked** (OCR real, competitor prices + notifications mocked), trade-offs/limitations, and "what I'd improve with more time". This README is a graded artifact.
- Include sample files: a sample product CSV, a sample competitor-price CSV, and a short sample product video with on-screen product text (so OCR has something real to read) plus a note on how it was made.

---

## 10. Bonus, in priority order (only after the loop is complete + deployed)

OpenAPI/Swagger is already free via FastAPI `/docs` — make sure it's clean. Then:
1. Price history chart (Recharts) — every refresh writes a CompetitorPrice row with `last_checked_at`, so history is free.
2. Dockerized local dev (`docker-compose.yml`: postgres + backend + frontend).
3. Downloadable quality report (PDF/CSV export of the dashboard).
4. Real email notification (`email_notifier.py` via SMTP; no-op without env).
5. Auth, retry-failed-jobs, scheduled refresh (cron/arq), AI-vision extraction as an alternative `EXTRACTION_PROVIDER`.

Each bonus is a clean addition behind a seam, fully removable, and must not destabilize the core loop.

---

## 11. Working conventions with me (the human)

- **Speak less, ask more before acting.** Before doing extra work beyond what I asked, get my consent. Don't silently scope-creep.
- **Flag critical files for my personal review** — anything touching the data model (SQLAlchemy models / Alembic migrations), the API contract, the Dockerfile / deployment config, or env handling. I want eyes on those before they're final.
- **Never commit secrets.** `.env` is gitignored; ship `.env.example` with placeholders only. If you ever see a real secret in a tracked file, stop and tell me.
- Commit incrementally with clear messages, in an order a reviewer can read top-to-bottom (mirrors §1).
- Production-grade by default: real error handling, validation, sensible logging, no dead code, no leftover experiments.
- Business logic = small, composable, testable pure functions (validation, scoring, enhancement, comparison, attribute-parsing from OCR text). Routers and services stay thin.
- When the assignment is genuinely ambiguous, make a reasonable assumption, **document it in the README assumptions section**, and keep moving — don't stall.

---

## 12. Definition of done (the loop)

A reviewer can: open the deployed frontend → upload the sample video (with on-screen text) with enhance-title ON → watch the job progress → see the product appear with real OCR-extracted fields (or mock fallback if OCR finds nothing) → see quality score → open product detail → see issues + suggested fixes + enhanced title + competitor prices + comparison + recommended action → hit Refresh Prices and watch alerts update → open the alerts page and see severity-classified history. All with zero API secrets configured, with the README explaining exactly what's real (OCR) vs mocked (competitor prices, notifications).

Get that working and deployed before anything in §10.