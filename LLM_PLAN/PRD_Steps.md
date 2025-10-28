# Trading Dashboard Development Plan (Based on PRD)

This file outlines the **high-level steps and sub-steps** to complete all requirements from the PRD, with **testing gates after every major step**.

---

## Epic A — Foundations (Repo, CI/CD, Railway, DB)

### A1. Monorepo & Scaffolding
- Create folder structure per PRD (`/apps/frontend`, `/apps/backend`, `/infra`, `/tests`, `/specs`, `/docs`).
- Initialize package managers and README with scope and assumptions.
- Add `.editorconfig`, `.gitignore`, commit hooks (format/lint).

### A2. Environment & Secrets
- Define required environment variables: `OPENAI_API_KEY`, `DATABASE_URL`, `APP_ENV`, `TZ=America/New_York`.
- Add `.env.example` and document setup.

### A3. Railway Project
- Create Railway services: **web-backend** (FastAPI) + **Postgres**.
- Verify DB connectivity locally and in Railway build.

### A4. CI/CD
- GitHub Actions for lint, unit tests, and deploy to Railway.
- Database migrations run automatically via Alembic.

**Test Gate:** CI build passes, Railway deploy live with healthcheck route.

---

## Epic B — Ingest & Validation (CSV templates → unified schema)

### B1. Broker Template Specs
- Define **Webull v1**, **Robinhood v1**, **Unified CSV v1** templates in `/specs/broker_templates/`.
- Include header lists, date formats, side aliases, and sample CSVs.

### B2. Ingest API
- Route `/ingest` accepts multipart upload + template ID.
- Validate headers & datatypes; reject with specific checklist on mismatch.
- Normalize rows to **Unified Trade Schema**.

### B3. Persistence & Status
- Save normalized data to `normalized_trades` table.
- Add `/ingest/status/{job_id}` for progress updates.

**Test Gate:** Parsing unit tests (valid/invalid cases) + clear checklist validation messages.

---

## Epic C — FIFO Engine & Metrics (long + short; realized P&L; EST timeframes)

### C1. Data Model & Migrations
- Create `normalized_trades`, `closed_lots`, `per_day_pnl`, `aggregates` tables.
- Add Alembic migrations.

### C2. FIFO Matching (Long & Short)
- Implement dual-queue FIFO logic per symbol (long lots + short lots).
- Compute realized P&L per matched lot.
- Persist closed-lot details and realized P&L.

### C3. Daily P&L Series (EST)
- Convert execution timestamps to EST.
- Sum daily realized P&L; fill missing dates to maintain continuous line.
- Store in `per_day_pnl` table.

### C4. Aggregates & Metrics
- Compute total P&L, trades, win rate, avg gain/loss, profit factor, best/worst symbol & weekday.

### C5. APIs
- `/metrics?timeframe=...` for summaries.
- `/chart?timeframe=...` for continuous series data (calendar EST).

**Test Gate:** Unit tests for FIFO edge cases, rounding accuracy ≤ $0.01, snapshot tests for golden CSV, API contracts passing.

---

## Epic D — Dashboard UI (continuous chart, red/green, animations, benchmarks)

### D1. Routes & State
- Pages: Landing (upload + demo) and Dashboard (metrics, chart, AI panel).

### D2. Timeframe Selector
- Controls for ALL, YTD, 6M, 3M, 1M, 1W with calendar-based filtering.

### D3. Metrics Header
- Animated metric cards with count-up effect.
- Display assumptions banner.

### D4. Continuous P&L Chart
- **Continuous line** with no gaps.
- **Color:** green ≥ 0, red < 0, gradient transition at 0.
- **Animations:** smooth transitions, draw effect on load, tooltip fade.
- Responsive layout (desktop/mobile).

### D5. Benchmarks
- Bundle SPY/DIA/QQQ demo CSVs and overlay cumulative returns.
- Fade-in/out toggle animation for benchmarks.

**Test Gate:** E2E upload → metrics → chart → timeframe toggles. Visual tests for red/green transitions + smooth animations.

---

## Epic E — AI Coach (deterministic JSON; typing animation)

### E1. JSON Contract
- Define `/specs/json_contracts/ai_coach.json` schema (summary, insights, risks, actions).

### E2. Backend AI Service
- Route `/ai/coach`:
  - Collect aggregate metrics.
  - Call OpenAI in JSON mode.
  - Retry once on invalid JSON; fallback to neutral response.

### E3. Frontend UI
- Render AI output with **typed animation** and fade effects.
- Handle empty or fallback states gracefully.

**Test Gate:** Contract validation passes; all responses valid JSON; frontend renders without breaks.

---

## Epic F — Creator Demo, Docs, and Polish

### F1. Creator Demo
- Add fixed CSV demo dataset backend-side.
- “View Creator Demo” loads this dataset directly.

### F2. Error & Empty States
- Invalid CSV → checklist panel with specific errors.
- No trades → informative empty state.

### F3. Documentation & Transparency
- Add `/docs/assumptions.md`, `/specs/broker_templates/`, `/specs/json_contracts/ai_coach.json`.
- Update README with setup + Railway deploy guide.

**Test Gate:** Full E2E success on demo dataset, accessibility checks, documentation up-to-date.

---

## Cross-Cutting Testing & Observability

### T1. Unit Tests
- FIFO long/short logic, rounding, timeframe slicing, continuous data.

### T2. API Contract Tests
- Schemas for `/ingest`, `/metrics`, `/chart`, `/ai/coach`.

### T3. E2E Tests
- Upload → Dashboard → Chart → AI insights flow.
- Invalid CSVs → proper checklist displayed.

### T4. Performance & Logging
- CSV ingest ≤ 10s for ~10k rows.
- Structured logs for FIFO, ingest, and AI; no PII.

**Final Gate:** All unit, API, and E2E tests pass before production deploy.

---

## Deployment & Version Control

- **Git Flow:** Protected `main`, required checks before merge.
- **Pipeline:** CI → lint/test → build → migrate → deploy to Railway.
- **Config:** Env vars only, no local file dependencies.

---

## Acceptance Summary

- **A:** CI + Railway verified.  
- **B:** CSV validation & normalization.  
- **C:** FIFO long/short accuracy ≤ $0.01.  
- **D:** Animated continuous red/green chart functional.  
- **E:** AI panel JSON-mode & typed animation validated.  
- **F:** Demo + Docs complete.  

---
