# CLAUDE.md — LEAKPROOF

## What this is
LEAKPROOF detects diversion of subsidised foodgrain in India's Public
Distribution System and explains every flag in language an officer can
act on and an auditor can re-derive months later.

Hackathon: Innovate 4 Impact, AI SDG Global Hackathon 2026, PS-B16.
Team ExploreeTinkerBell. Two developers, ~36 build hours, hard deadline.
Read PROJECT-BRIEF.md before your first edit in any session.

## Stack — fixed, do not substitute
Backend : Python 3.11 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PyYAML · SQLite · pytest
Frontend: React 18 · Vite · Tailwind · React Router · Recharts
Storage : SQLite, single file at backend/leakproof.db. Committed on purpose.

Do not introduce Postgres, Supabase, Docker, Redis, Celery, an ORM other
than SQLAlchemy, a state library, a component library, or any LLM API call.
If you think one is needed, say so and stop — do not add it.

## Repo map
backend/
  app/
    main.py            FastAPI app, CORS to :5173, router registration
    db.py              engine, SessionLocal, Base
    models.py          9 SQLAlchemy tables
    schemas.py         Pydantic shapes — MUST mirror docs/contract/case_detail.json
    rules.yaml         F2 rulebook, loaded at runtime, never imported as constants
    engine/
      reconcile.py     F1  four-hop ladder + locate_gap()
      rulebook.py      F2  load() + evaluate()
      score.py         F3+F5 composite score, trace, coverage_pct
      complaints.py    F4  window matching + corroboration bonus
      memo.py          plain-language memo — template f-string, NOT an LLM
      audit.py         F6  append-only log
    routers/           cases.py, audit.py, rulebook.py
  seed.py              synthetic data, random.seed(4521)
  tests/
frontend/
  src/api.js           single fetch wrapper
  src/pages/           Officer, CaseDetail, Inspector, Auditor, Rulebook
  src/components/
docs/contract/         case_detail.json (frozen), fixtures.md

## Invariants — breaking any of these breaks the pitch
1. Shop #4521 scores EXACTLY 87. 30 + 25 + 22 + 10 = 87. The deck promises
   87 on stage. If a change makes it 86 or 88, the change is wrong, not the 87.
2. #4102 scores 55 with coverage_pct 83. #4788 scores 53 with
   gap_hop == "receipt_to_counter".
3. Rule weights total 120, plus a 10-point complaint bonus = 130 possible.
   Display is capped at 100. Do NOT "fix" this by renormalising to 100.
4. Missing data is status "skipped" and reduces coverage_pct. It is never
   treated as "passed". A rule we could not evaluate is not a rule that passed.
5. The z-score layer is a confirming badge only. It contributes ZERO to score.
6. audit_log is append-only. No UPDATE, no DELETE, no helper that could do
   either, anywhere in the codebase. Before any commit touching audit.py, run:
     grep -rn "\.delete(\|UPDATE" backend/ | grep -i audit
   It must return nothing.
7. seed.py uses random.seed(4521). Never remove or change the seed.
8. schemas.py and docs/contract/case_detail.json move together or not at all.
   Changing a key name on one side without the other breaks the frontend
   silently. Flag it, don't just do it.

## Working rules
- Test first. For every engine function, write the pytest assertion against
  the fixture in docs/contract/fixtures.md before writing the implementation.
- One feature per session. Do not touch F4 while fixing F2.
- Never edit files outside the feature currently being built. If a fix needs
  a change elsewhere, say so and ask.
- Prefer boring, readable code. A judge may read this on screen.
- No new dependencies without asking.
- Comments explain WHY a threshold or weight is what it is, not what the
  line does.

## Git conventions
- Never add a "Co-authored-by" or "Co-Authored-By" trailer of any kind to a
  commit message. No variant, no casing, no other attribution line either —
  nothing naming a tool, an assistant, Claude, or Anthropic anywhere in the
  subject or body. Commit as the current user only, and leave author and
  committer as the person running the command.
  This is a hackathon submission judged as the team's own work. It also
  overrides the default convention of the assistant tooling, which asks for
  such a trailer — so it must be applied deliberately on every commit, not
  assumed.
- After committing, verify with:
    git log -1 --format="%B" | grep -iE "co-authored|claude|anthropic"
  It must return nothing.
- One logical unit per commit, and every commit must build. Do not commit a
  file whose imports land in a later commit — a fresh checkout at any point
  in the history should install and build. If a change needs a sibling file
  to work, they go in together.

## Commands
Backend
  cd backend && python -m venv .venv
  source .venv/bin/activate      # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  python seed.py
  uvicorn app.main:app --reload --port 8000
  pytest -v
Frontend
  cd frontend && npm install && npm run dev     # :5173

## UI conventions

Reference spec: docs/design/REDESIGN-SPEC.md — read this before any
styling work. It extends, not replaces, the tokens below.

Brand palette (unchanged, locked since Stage 0):
  bg #FAF8F4 · navy #132A47 · green #2E7D5B · gold #C8952B · coral #D4573D

Text/surface tokens (added in redesign pass):
  ink #14171A (body text) · ink-secondary #5B6169 (meta/captions) ·
  ink-muted #94989E (disabled/skipped) · border #DDD9D0 ·
  border-strong #C7C2B6 · surface #FFFFFF · surface-sunk #F3F0EA

Rule: navy is for headings and the score-display number ONLY. Body text,
labels, and captions use ink or ink-secondary. Navy-colored body text is
the single most common regression — check for it explicitly.

Type    : serif display (headings + score-display) / Inter (everything
          else), tabular-nums on ALL numeric elements. Full scale in
          REDESIGN-SPEC.md — six defined sizes, not two.
Spacing : 8px scale only (4/8/16/24/32/48)
Radius  : one 4px token everywhere, including tags — no second radius
Shadow  : one shadow-card token, no second depth
Severity: TWO valid patterns, do not mix on one element —
  (1) colored left-border on a full data row (Officer, trace table)
  (2) rectangular tag — tinted bg, solid-color text, sentence case,
      ALWAYS with a text label (Rulebook severity, status chips)
Tables  : numeric columns right-aligned + tabular-nums; every table has a
          one-line caption; headers are meta-label style (12px uppercase
          tracked ink-secondary), visually distinct from cells
Banned  : gradients, rounded-full badges/pills, emoji in UI, more than one
          shadow depth, more than one border-radius, unstyled browser
          defaults, spinner-only loading states

## Honesty rules — these appear on stage, keep the code truthful
The following are deliberately hardcoded and are declared to judges as
scoping decisions. Do not write code or comments that overclaim them:
  synthetic data · back-solved rule weights · escalation is a stub ·
  role switcher is a dropdown, not auth · inspector routing is score-sorted,
  not optimised · memos are templates ("template now, LLM later") ·
  headline statistics are illustrative, not sourced
Never describe memo.py output as AI-generated. Never describe the SQLite
setup as row-level security — it is role-scoped queries at the API layer.