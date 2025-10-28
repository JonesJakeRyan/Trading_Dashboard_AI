# PRODUCT REQUIREMENTS DOCUMENT (PRD): Trading Dashboard MVP (Updated)

**Purpose**  
Deliver a deployable MVP trading dashboard that lets users upload a CSV of their USD equity/ETF trades — long **and short** — to view accurate, broker-style *cumulative realized P&L* metrics, a **continuous, color-coded (green/red) animated P&L chart**, and AI-generated “coach” insights from OpenAI.  
Development will follow **SCRUM methodology**, built in **Windsurf**, deployed from **Git → Railway**.  

---

## **1. Product Goals & Success Criteria**

- **Goal 1:** Users upload a CSV and instantly see cumulative realized P&L and metrics across selectable timeframes (ALL, YTD, 6M, 3M, 1M, 1W).  
  - **Success:** ≥ 95 % parity vs broker cumulative realized P&L for supported data using FIFO matching and unified logic.  

- **Goal 2:** Deliver a **continuous, color-coded P&L line chart** (green = > 0, red = < 0) with smooth transitions and **animations wherever feasible** (chart transitions, panel fades, counters).  

- **Goal 3:** Provide **AI “Coach” insights** using deterministic JSON-mode OpenAI responses for pattern and risk observations (no trade calls).  

- **Goal 4:** Fully deployable from **Git to Railway**, version-controlled, one-click deploy.  

---

## **2. Scope**

### **In-Scope (MVP)**
- CSV upload for **USD equities/ETFs, long and short** trades.  
- Broker-template validation (Webull v1, Robinhood v1, Unified CSV v1).  
- Continuous, animated, red/green P&L chart.  
- Cumulative realized P&L metrics using **FIFO** lot matching for both long and short.  
- Benchmarks (SPY, DIA, QQQ).  
- AI insights panel (pattern + risk only).  
- Creator demo dashboard (your fixed CSV).  
- No authentication (guest mode).  
- Full unit/API/E2E test suite with test gates after every major step.

### **Out-of-Scope (Future Support)**
- Options, crypto, FX, dividends, fees, corporate actions.  
- Broker APIs / OAuth.  
- Vector DB, real-time data, multi-user auth.  
- Drawdowns, advanced analytics.

---

## **3. User Stories**

- **US-01 Upload CSV:** Upload CSV → validate template → normalize → metrics render.  
- **US-02 Metrics:** View cumulative realized P&L, win rate, profit factor, etc.  
- **US-03 Timeframes:** Toggle ALL/YTD/6M/3M/1M/1W (calendar-day, EST).  
- **US-04 Benchmarks:** Toggle SPY/DIA/QQQ overlay.  
- **US-05 Chart Coloring:** P&L line is **green** when > 0, **red** when < 0, smooth animation on load and timeframe change.  
- **US-06 Short Support:** Uploads containing short sells are accepted and accurately reflected in realized P&L.  
- **US-07 AI Insights:** Coach panel provides deterministic JSON insights with animations in text appearance.  
- **US-08 Creator Demo:** View example dashboard preloaded with fixed CSV.

---

## **4. Metrics & Calculations**

### **Headline Metrics**
- Cumulative Realized P&L  
- Total Trades (closed only)  
- Win Rate  
- Avg Gain (winners) / Avg Loss (losers)  
- Profit Factor  
- Best/Worst Symbol  
- Best/Worst Weekday  

### **Short Support Logic**
- Shorts permitted; FIFO logic mirrored for **SELL→BUY-to-cover**.  
- Maintain two queues per symbol: long lots, short lots.  
- Match close-outs against earliest opposite lots.  
- Realized P&L = (close_price – open_price) × quantity (sign aware).  
- Short positions reflected as negative quantities in cumulative lots table.  
- Chart and aggregates show cumulative realized P&L (positive = profit, negative = loss).  

---

## **5. Chart Requirements**

- **Continuous line** (no gaps between days).  
- **Color-coded:**  
  - Green (#16a34a or similar) when cumulative P&L ≥ 0.  
  - Red (#dc2626 or similar) when < 0.  
  - Gradient transition if crossing 0.  
- **Animation:**  
  - Smooth transitions between timeframes.  
  - Animated “draw” effect on initial load.  
  - Benchmark toggles fade in/out.  
- **Tooltip:** Date + Cumulative P&L + Benchmark values.  
- **Responsive:** Works on desktop & mobile.

---

## **6. Timeframes (EST Calendar Days)**

- ALL = min→max dates.  
- YTD = Jan 1 → latest date.  
- 6M = last 182 days; 3M = 91; 1M = 30; 1W = 7.  
- Boundaries computed in EST; closing times = 16:00 EST.  
- Partial days included.

---

## **7. AI Insights (OpenAI JSON Mode)**

- **Input:** Aggregated metrics + symbol summaries.  
- **Schema:**  
  ```json
  {
    "summary": "string",
    "pattern_insights": [{"title": "...","evidence_metric": "...","why_it_matters": "..."}],
    "risk_notes": [{"title": "...","trigger_condition": "...","mitigation_tip": "..."}],
    "top_actions": [{"priority":1,"action":"..."}]
  }
  ```
- **Constraints:** No ticker advice / recommendations.  
- **Display:** Typed-out animation in UI with fade-in per bullet.  
- **Retry:** On invalid JSON, retry once then show neutral fallback.

---

## **8. Data Model & Flow**

### **Unified Trade Schema**
| Field | Type | Notes |
|--------|------|-------|
| trade_id | UUID | unique |
| symbol | TEXT uppercase |  |
| side | ENUM BUY/SELL | |
| quantity | DECIMAL | positive |
| price | DECIMAL | |
| executed_at | TIMESTAMP UTC | |
| account_id | TEXT | optional |
| notes | TEXT | optional |

### **FIFO Logic (Long & Short)**
1. Sort by executed_at.  
2. Maintain FIFO queues for each symbol.  
3. On BUY:  
   - If short queue not empty → cover shorts first using FIFO.  
   - Else → add to long queue.  
4. On SELL:  
   - If long queue not empty → close longs FIFO.  
   - Else → open short position (add to short queue).  
5. Compute realized P&L each close lot.  

---

## **9. UX / UI & Animations**

- **Landing:** File upload w/ broker template selector + “View Creator Demo.”  
- **Dashboard:**  
  - Metric cards count up with animation.  
  - Chart transitions animated.  
  - AI panel typing animation.  
  - Benchmarks fade toggle.  
  - Hover tooltips animated.  
- **Color Scheme:** Dark mode first, high contrast.  
- **Animation Guideline:** Prefer CSS or Framer Motion for smooth transitions; avoid jank.

---

## **10. Architecture & Tech Stack**

**Frontend**
- React + Vite + TypeScript + Tailwind + Framer Motion (animations) + Plotly.js (charts)  
- TanStack Query (data fetch) / React Router  

**Backend**
- FastAPI (Python 3.11+) + SQLAlchemy + Pydantic + Alembic  
- Pandas for preprocessing & FIFO calc  
- OpenAI API (JSON mode)  

**Database**
- PostgreSQL (Railway)  

**Testing**
- Pytest (calc + API)  
- Jest (frontend units)  
- Playwright (E2E)  

**Deployment**
- GitHub Actions → Railway Deploy  
- Env vars for DB URL & OpenAI key  
- No local state; CSV streamed → DB  

---

## **11. File & Folder Structure**

```
/apps
  /frontend
    /src
      /components
      /pages
      /charts
      /animations
      /styles
  /backend
    /app
      /api
      /services
      /models
      /schemas
      /jobs
      /benchmarks
/infra
/tests
/specs
/docs
```

---

## **12. Testing Plan (Gates After Each Epic)**

- **Unit:** FIFO (long + short) matching; P&L accuracy ≤ 1 cent error.  
- **API:** Schema validation / chart data continuity / AI JSON.  
- **Frontend:** Chart renders continuous line, colors toggle red/green correctly.  
- **E2E:** Upload → Metrics → Chart → AI panel pass.  
- **Animation QA:** No visual tearing > 16 ms frame lag on Railway demo.

---

## **13. SCRUM Plan (Epics → Milestones)**

| Epic | Deliverable | Test Gate |
|------|--------------|-----------|
| **A** Foundations | Repo + Railway deploy + DB schema | CI green |
| **B** Ingest & Validation | Broker templates + parser + reject checklist | Parsing tests |
| **C** FIFO Calc & Short Support | Long & short FIFO engine + metrics | Unit tests green |
| **D** Chart UI & Animations | Continuous red/green chart + timeframe toggle | Visual + E2E pass |
| **E** AI Coach | OpenAI JSON mode + typing UI | JSON contract tests |
| **F** Creator Demo & Docs | Demo dataset + assumptions page | Full E2E pass |

---

## **14. Risk & Mitigation**

| Risk | Mitigation |
|------|-------------|
| Complex short scenarios | Strict FIFO; reject partial short-overlap errors |
| Animation lag | Limit framerate / simplify transitions |
| Broker CSV variance | Template validation & clear checklist |
| AI JSON failure | Schema validate & fallback |

---

## **15. Deployment & Scalability**

- **Railway** kept as default (cheap, simple).  
- All uploads processed in-memory < 10 MB.  
- For scaling later, consider:  
  - **Render** (free tier backend), **Fly.io** (global), or **Vercel + Supabase** (TS DX).  

---

## **16. Future Features**

- Options, crypto, FX.  
- Fees/dividends/corporate actions.  
- API integrations.  
- Time-weighted returns.  
- Vector DB finance expertise.  
- Advanced drawdowns / factor analysis.  
- User auth & report export.  

---

## **17. Documentation & Transparency**

- `/docs/assumptions.md` lists:  
  - FIFO logic (long + short).  
  - USD-only.  
  - Realized P&L only.  
  - Calendar day (EST).  
  - No fees/dividends.  
- `/specs/broker_templates/` for each CSV.  
- `/specs/json_contracts/ai_coach.json` for AI schema.

---

## **18. Definition of Done**

- ≥ 95 % accuracy vs broker for realized P&L on golden CSV.  
- Continuous P&L chart red/green with animation.  
- AI panel renders deterministic JSON.  
- All tests pass in CI + deployed on Railway.
