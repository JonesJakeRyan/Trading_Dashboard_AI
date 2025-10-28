---
trigger: always_on
---

# Workspace-specific guardrails for the Trading Dashboard MVP
# These rules override any global defaults inside Windsurf.

metadata:
  project: "Trading Dashboard MVP"
  owner: "Jake Jones"
  reference_docs:
    - "LLM_PLAN/Product_Requirement_Document.md"

rules:

  - id: no_auto_summaries
    level: hard
    applies_to: ["**/*"]
    description: >
      Do NOT create summary docs, status writeups, or extra READMEs unless the user explicitly asks.
      Only modify or create files necessary to satisfy the PRD or an explicit request.

  - id: hotfix_console_checks
    level: soft
    applies_to: ["apps/backend/**", "apps/frontend/**"]
    description: >
      When investigating a one-off error likely to be run two (2) times or fewer,
      prefer ephemeral console/REPL checks or scratch scripts that are NOT committed.
      For any fix that remains in the codebase, add/maintain proper unit/API/E2E tests per the PRD gates.

  - id: foldered_file_structure
    level: hard
    applies_to: ["**/*"]
    description: >
      Prefer organizing all new files into clearly titled folders described in the PRD
      (e.g., apps/backend/app/services, models, schemas, jobs; apps/frontend/src/components, pages, charts, animations).
      Avoid dropping new files at the root unless the PRD explicitly calls for it.

  - id: modular_over_monolith
    level: soft
    applies_to: ["apps/backend/**", "apps/frontend/**"]
    description: >
      Prefer modular code split across smaller focused files over long monolithic files,
      AS LONG AS it does not create circular dependencies or unnecessary complexity.
      Target: functions < 50 lines, files < 300 lines when practical.

  - id: prd_scope_guard
    level: hard
    applies_to: ["**/*"]
    description: >
      If a requested change conflicts with the PRD scope (e.g., adds options/fees/dividends/APIs, or alters performance definitions),
      do NOT implement directly. Instead:
        1) Create a planning comment in the PR or a docs/todo note describing the change, rationale, and impact.
        2) Ask for explicit approval in the PR description and STOP further scope work until confirmed.

  - id: structured_logging_required
    level: hard
    applies_to: ["apps/backend/**"]
    description: >
      Implement structured logs (JSON) automatically in areas with higher failure likelihood or monitoring value:
        - CSV ingest/validation/normalization
        - FIFO matching (long + short)
        - P&L series generation and timeframe slicing
        - OpenAI /ai/coach calls (latency, status, token counts; never log secrets or raw user data)
      Logs must not include secrets, API keys, or PII. Prefer INFO for success, WARN for retry/fallback, ERROR for failures.

  # Non-functional helpers that keep Windsurf aligned with the PRD (optional but recommended)
  - id: prd_alignment_check
    level: soft
    applies_to: ["**/*"]
    description: >
      Before committing, cross-check changes against:
        - Cumulative realized P&L only (FIFO; long + short; USD; EST calendar days; continuous chart; green≥0/red<0; animations)
        - No options/fees/dividends/corporate actions or broker APIs in MVP
        - OpenAI JSON-mode with schema validation + retry/fallback
      If in doubt, add a PR checklist referencing the PRD acceptance criteria.

defaults:
  prohibited_paths: []   # add any paths you want Windsurf to avoid editing
  allowed_paths:
    - "apps/**"
    - "infra/**"
    - "specs/**"
    - "docs/**"
  commit_policy:
    require_tests_green: true
    require_description: true
    checklist_reference: "Link acceptance criteria from PRD for the touched Epic."
