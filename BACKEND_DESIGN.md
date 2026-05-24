# Backend System Design

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vercel)                        │
│              React + TypeScript + TanStack Query                │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTPS  (VITE_API_URL)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (Render)                            │
│                   FastAPI  •  Python 3.12                       │
│                                                                 │
│  ┌─────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  API Layer  │   │ Service Layer│   │  Background Tasks  │   │
│  │  (routers)  │──▶│  (Protocols) │   │  (FastAPI BG Tasks)│   │
│  └─────────────┘   └──────────────┘   └────────────────────┘   │
│          │                │                      │              │
│          └────────────────┴──────────────────────┘             │
│                           │                                     │
│                    SQLAlchemy (async)                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL (Render managed)                    │
│   products · jobs · listing_issues · competitor_prices          │
│   alerts · enhanced_titles                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## All Endpoints

### Video Upload
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload-video` | Upload a product video → spawns a background job |

### Products & CSV
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload-products-csv` | Bulk upload products from CSV → spawns a background job |
| `GET`  | `/products` | List all products (filters: `?severity=` `?category=` `?alert=`) |
| `GET`  | `/products/{sku_id}` | Product detail with issues, competitor prices, enhanced title |
| `PATCH`| `/products/{sku_id}` | Manually edit extracted data → re-runs validation |
| `GET`  | `/products/{sku_id}/issues` | All listing issues for a product |
| `POST` | `/products/{sku_id}/enhance-title` | Generate an AI-style enhanced title |

### Jobs
| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/jobs` | List all jobs |
| `GET`  | `/jobs/{job_id}` | Get single job (frontend polls this for progress) |

### Competitor Prices
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/competitor-prices/upload` | Ingest competitor prices from a CSV file |
| `POST` | `/competitor-prices/refresh` | Refresh prices for all products → spawns a background job |
| `GET`  | `/products/{sku_id}/competitor-prices` | Prices + comparison block for one product |

### Alerts & Dashboard
| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/alerts` | List alerts (filters: `?severity=` `?status=`) |
| `GET`  | `/alerts/count` | Unread alert count (used by navbar badge) |
| `POST` | `/alerts/acknowledge-all` | Mark all alerts acknowledged |
| `PATCH`| `/alerts/{alert_id}/acknowledge` | Acknowledge a single alert |
| `GET`  | `/dashboard/quality-summary` | Summary cards: scores, issue counts, weak listings |
| `GET`  | `/health` | Health check — `{ ok: true }` |

---

## Request → Response Flow

### Flow 1 — Video Upload (most complex)

```
Browser
  │
  │  POST /upload-video  (multipart, video file)
  ▼
Router (video.py)
  │  1. Save file to /tmp
  │  2. INSERT jobs row  (status=PENDING)
  │  3. background_tasks.add_task(_run_video_job, job_id)
  │  4. Return { job_id }  ← response sent immediately
  │
  ▼  [HTTP response already returned to browser]
  │
BackgroundTask (_run_video_job)
  │
  ├── mark job RUNNING  (progress=0)
  │
  ├── extraction/factory.py → extract(video_path, sku_id)
  │       │
  │       ├── [OCR path]  ffmpeg → frames → pytesseract → parse attributes
  │       │
  │       └── [mock path] MockExtractor → deterministic fake product data
  │                       (used when: EXTRACTION_PROVIDER=mock  OR  OCR fails)
  │
  ├── pipeline.process_product_row()
  │       ├── Upsert into products table
  │       ├── Run all validation rules → insert listing_issues
  │       ├── Compute quality_score
  │       └── Raise alerts if rules triggered
  │
  ├── update progress → 90
  │
  └── mark job COMPLETED  (progress=100)

Browser (polling GET /jobs/{job_id} every 2s)
  └── sees COMPLETED → navigates to product detail page
```

---

### Flow 2 — CSV Upload

```
Browser
  │  POST /upload-products-csv  (multipart, .csv file)
  ▼
Router (products.py)
  │  1. Read CSV bytes into memory
  │  2. INSERT jobs row
  │  3. background_tasks.add_task(_run_csv_job, job_id, rows)
  │  4. Return { job_id }
  │
BackgroundTask (_run_csv_job)
  │
  ├── mark job RUNNING
  │
  ├── for each row in CSV:
  │       ├── pipeline.process_product_row()
  │       │       ├── Upsert product
  │       │       ├── Validate → listing_issues
  │       │       ├── quality_score
  │       │       └── Alerts
  │       ├── track failed rows
  │       └── update progress incrementally
  │
  └── mark COMPLETED or PARTIALLY_COMPLETED
      result_summary = { inserted, updated, failed, failed_rows: [...] }
```

---

### Flow 3 — Price Refresh

```
Browser
  │  POST /competitor-prices/refresh
  ▼
Router (competitor.py)
  │  INSERT jobs row  → return { job_id }
  │
BackgroundTask (_run_refresh_job)
  │
  ├── fetch all products from DB
  │
  ├── for each product:
  │       │
  │       ├── MockCompetitorService.get_prices(sku_id, price, product_title)
  │       │       └── pure math, no HTTP calls
  │       │           seed = MD5(sku_id) → deterministic platform + price selection
  │       │           URL  = real search URL on that platform
  │       │
  │       ├── read OLD competitor prices (to detect drops)
  │       ├── upsert competitor_prices rows
  │       ├── if price dropped significantly → raise MEDIUM alert
  │       └── if our price > 10% above lowest competitor → raise HIGH alert
  │
  └── mark COMPLETED
      result_summary = { refreshed, alerts_raised }
```

---

### Flow 4 — Synchronous Reads (no background task)

```
Browser
  GET /products/{sku_id}
       │
       ▼
  Router (products.py)
       ├── SELECT product WHERE sku_id = ?
       ├── SELECT listing_issues WHERE product_id = ?
       ├── SELECT competitor_prices WHERE product_id = ?
       │       └── compute comparison block on-the-fly:
       │           lowest / highest / avg price, gap, % diff, recommended action
       ├── SELECT enhanced_titles WHERE product_id = ?
       └── Return combined ProductOut schema (Pydantic serialised)
```

---

## Background Processing — How It Works

FastAPI's `BackgroundTasks` is used — **no Redis, no Celery, no external queue**.

```python
# Router returns immediately:
background_tasks.add_task(_run_video_job, job.id)
return {"job_id": job.id}

# FastAPI runs _run_video_job() after the response is sent,
# in the same process, on the same asyncio event loop.
```

The `jobs` table in Postgres **is** the visibility layer:

```
PENDING  →  RUNNING  →  COMPLETED
                     →  FAILED
                     →  PARTIALLY_COMPLETED
```

The frontend polls `GET /jobs/{id}` every 2 seconds and reads `status` + `progress` (0–100) to drive the progress bar. When status becomes `COMPLETED` or `FAILED`, polling stops.

**Trade-off:** If the Render server restarts mid-job, that job stays `RUNNING` forever with no auto-recovery. Acceptable for a demo; a real system would use Celery/arq with Redis for durability.

---

## Where Mock Data Is Used

| Area | Real or Mock | Detail |
|------|-------------|--------|
| **Video OCR extraction** | **REAL (default)** | `ffmpeg` extracts frames, `pytesseract` reads text, attributes parsed from OCR output |
| **OCR fallback** | Mock | If OCR fails or `EXTRACTION_PROVIDER=mock`, `MockExtractor` returns deterministic fake product data seeded by `sku_id` |
| **Competitor prices** | **Mock** | No web scraping. Prices are computed as `our_price × multiplier`, seeded by MD5(sku_id) — same product always gets same prices |
| **Competitor URLs** | **Real** | URLs are real platform search pages (e.g. `amazon.in/s?k=Nike+Air+Max+270`) — "View →" links resolve |
| **Title keywords** | Mock | Trending keywords come from a hardcoded per-category map in `keywords.py` |
| **Notifications** | Mock | In-app alerts write to the `alerts` table. No real email/SMS is sent (SMTP notifier exists but is a no-op without env vars) |
| **Validation rules** | **Real** | All 11 rules are implemented as pure functions and are fully unit-tested |
| **Quality score** | **Real** | Deterministic formula: 100 − (HIGH×20) − (MEDIUM×10) − (LOW×3), floor 0 |

---

## Service Layer — Protocol / Interface Pattern

Every external dependency sits behind a `typing.Protocol`. Routers never import a concrete implementation directly — only the factory.

```
services/
  extraction/
    extractor.py         ← Protocol: extract(video_path, sku_id) → ExtractedProduct
    ocr_extractor.py     ← REAL: ffmpeg + pytesseract
    mock_extractor.py    ← MOCK: deterministic fake data
    factory.py           ← picks impl; OCR falls back to mock on failure

  competitor/
    competitor.py        ← Protocol: get_prices(sku_id, price, title) → list[CompetitorPriceData]
    mock_competitor.py   ← MOCK: math-based prices + real search URLs
    csv_competitor.py    ← CSV parser (used for manual price upload)
    factory.py

  notifications/
    notifier.py          ← Protocol: send(alert) → None
    inapp_notifier.py    ← REAL (default): writes to alerts table
    email_notifier.py    ← SMTP: no-op if SMTP env vars missing
    factory.py
```

Swapping real ↔ mock is a config flip (`EXTRACTION_PROVIDER=mock`), not a code change.

---

## Environment Variables

| Variable | Used For | Default |
|----------|----------|---------|
| `DATABASE_URL` | Postgres connection | required |
| `CORS_ORIGIN` | Allowed frontend origin | `http://localhost:5173` |
| `EXTRACTION_PROVIDER` | `ocr` or `mock` | `ocr` |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASS` | Email notifications | optional (no-op if missing) |
| `CORS_EXTRA_ORIGINS` | Comma-separated extra CORS origins (Vercel previews) | optional |
