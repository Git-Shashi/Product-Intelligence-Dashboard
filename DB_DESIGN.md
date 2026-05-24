# Database Design

## ER Diagram

```mermaid
erDiagram
    products {
        bigint      id              PK
        varchar     sku_id          UK  "business key — duplicate upload = update"
        text        product_title
        text        description
        varchar     brand
        varchar     category
        float       price               "our Flipkart selling price"
        float       mrp                 "max retail price"
        text        image_url
        text        product_url
        boolean     availability
        varchar     color
        varchar     size
        varchar     material
        enum        source              "VIDEO | CSV | MANUAL"
        int         quality_score       "0–100, recomputed on every validation run"
        timestamptz created_at
        timestamptz updated_at
    }

    jobs {
        bigint      id              PK
        enum        type                "VIDEO_EXTRACTION | CSV_VALIDATION | PRICE_REFRESH"
        enum        status              "PENDING | RUNNING | COMPLETED | FAILED | PARTIALLY_COMPLETED"
        int         progress            "0–100, polled by frontend"
        timestamptz started_at
        timestamptz completed_at
        text        error
        json        result_summary      "per-row failures, counts, etc."
    }

    listing_issues {
        bigint      id              PK
        bigint      product_id      FK
        varchar     type                "rule name e.g. MISSING_TITLE"
        enum        severity            "HIGH | MEDIUM | LOW"
        text        message
        text        suggested_fix
        timestamptz created_at
    }

    competitor_prices {
        bigint      id              PK
        bigint      product_id      FK
        varchar     platform            "Amazon | Myntra | Ajio | Meesho | Tata Cliq"
        text        competitor_url      "real search URL on that platform"
        float       competitor_price    "mocked — computed from our price × multiplier"
        varchar     currency            "INR"
        timestamptz last_checked_at     "updated on every refresh run"
    }

    alerts {
        bigint      id              PK
        bigint      product_id      FK  "nullable — some alerts are not product-specific"
        varchar     type                "alert rule name"
        enum        severity            "HIGH | MEDIUM | LOW"
        text        message
        enum        status              "OPEN | ACKNOWLEDGED"
        timestamptz created_at
    }

    enhanced_titles {
        bigint      id              PK
        bigint      product_id      FK
        text        original_title
        json        attributes          "extracted key-value pairs from OCR/CSV"
        json        keywords            "trending keywords injected from mock map"
        text        enhanced_title
        text        reason              "human-readable explanation"
        timestamptz created_at
    }

    products ||--o{ listing_issues     : "validated into"
    products ||--o{ competitor_prices  : "priced against"
    products ||--o{ enhanced_titles    : "optimised into"
    products ||--o{ alerts             : "triggers"
```

---

## Table-by-Table Explanation

### `products` — core entity
Every listing lives here. `sku_id` is the **business key** (unique constraint). Uploading the same SKU twice updates the existing row rather than inserting a duplicate. `quality_score` is recomputed every time validation runs:

```
score = 100
       − 20 per HIGH issue
       − 10 per MEDIUM issue
       −  3 per LOW issue
       (floor = 0)
```

`source` records how the product entered the system: `VIDEO` (OCR extraction), `CSV` (bulk upload), or `MANUAL` (PATCH edit via UI).

---

### `jobs` — async task tracker
There is no external queue. Every background operation creates a `jobs` row. The frontend polls `GET /jobs/{id}` to read `status` and `progress` (0–100). `result_summary` is a JSON blob that carries per-row failure details for CSV jobs, or extraction metadata for video jobs.

Jobs are **decoupled from products** intentionally — one job processes many products, so a direct FK doesn't make sense.

---

### `listing_issues` — validation output
One row per broken rule per product. Re-running validation deletes all old issues for that product and inserts fresh ones (cascade delete on the FK). `suggested_fix` is shown inline in the UI next to each issue.

---

### `competitor_prices` — price intelligence
One row per **product × platform**. Every "Refresh Prices" run upserts these rows. `last_checked_at` is updated on every refresh, giving you a built-in time-series for the price history chart. The comparison block (lowest, highest, avg, gap, recommended action) is computed on-the-fly — not stored.

> **Note:** Prices are mocked (computed locally, no web scraping). URLs are real platform search pages so "View →" links resolve.

---

### `alerts` — notification log
Raised automatically by business rules after validation or a price refresh. `product_id` is **nullable** so a system-level alert can exist without being tied to a product. Users can acknowledge an alert (OPEN → ACKNOWLEDGED) from the UI.

---

### `enhanced_titles` — title suggestion history
Stores the full audit trail of a title enhancement run: extracted attributes, injected trending keywords, final title, and the reason string. Multiple enhancements per product are kept (not overwritten) so history is visible.

---

## Relationships at a Glance

```
products  (1) ──── (many)  listing_issues      cascade delete
products  (1) ──── (many)  competitor_prices   cascade delete
products  (1) ──── (many)  enhanced_titles     cascade delete
products  (1) ──── (many)  alerts              product_id nullable
jobs      ── standalone, no FK to products ──
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| `sku_id` unique constraint | Business deduplication — reupload same SKU → update, not duplicate row |
| Issues cascade-deleted on re-validation | Stale results must never outlive a fresh validation run |
| `competitor_prices` upserted per platform | One row per platform keeps the table small; `last_checked_at` serves as history timestamp |
| `alerts.product_id` nullable | Supports system-level alerts not tied to any specific product |
| `jobs.result_summary` as JSON | Flexible schema for per-job metadata without additional tables |
| All timestamps with timezone | Render (UTC) and local dev remain consistent |
| `jobs` decoupled from `products` | One job processes many products; a direct FK would be misleading |
