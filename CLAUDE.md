# CLAUDE.md

# Job Lead SDR Agent

## What this is

A personal "Sales Development Representative" agent for job searching. It
finds leads (people worth reaching out to — recruiters, hiring managers,
warm contacts) by mining email and LinkedIn, scores them against the
user's resume and preferences, and surfaces recommended actions through
one or more chat interfaces.

This is a single-user personal tool, not a multi-tenant product. Optimize
for "works reliably for one person" over generality.

## Architecture at a glance

Four layers, data flows bottom to top:

```
Interface layer   → Claude (MCP), Telegram bot, web dashboard
Agent layer        → reasoning, scoring, autonomy gating
Database layer     → SQLite (source of truth), accessed via a LeadStore contract
Context layer       → Gmail (event-driven via Pub/Sub), LinkedIn (CSV export)
```

Full design rationale lives in `docs/architecture.md` — read it before
making structural changes, don't duplicate it here.

## Tech stack

- Backend: FastAPI + SQLite, deployed on an existing VPS
- Agent ↔ Claude: MCP server (`job-assistant`) exposing tool calls
  (`add_lead`, `get_leads`, `update_lead`, `add_job`, `daily_brief`, etc.)
- Gmail ingestion: Gmail API + Cloud Pub/Sub push notifications (not polling)
- LinkedIn ingestion: manual CSV export, parsed on ingest (no scraping/API)

<!-- TODO once code exists: fill in actual commands -->

- Run locally: `[fill in]`
- Run tests: `[fill in]`
- Migrate DB: `[fill in]`

## Conventions

- Storage access always goes through the `LeadStore` interface
  (`get_leads`, `add_lead`, `update_lead`, `get_digest`) — never call SQLite
  directly from interface-layer code (MCP handlers, bot handlers, routes).
  This is what keeps Notion/Postgres swappable later.
- Every agent action that writes or sends checks the autonomy config before
  acting. Default to the most conservative tier (`suggest`) for any new
  action type until the user explicitly loosens it.
- Never auto-send an outreach message. `send_message` requires explicit
  per-message confirmation regardless of config — this is a hard rule, not
  a default.

## Autonomy tiers (current defaults)

```json
{
  "new_lead_found": "suggest",
  "outreach_draft": "draft",
  "send_message": "draft",
  "company_research": "suggest"
}
```

Tiers: `passive` (log only) → `suggest` (surface, user decides) →
`draft` (prepare for review) → `send` (acts, opt-in only). Source of truth
for current values is the `config` table, not this file — update this
section only if the _defaults_ change.

## Current status / build order

1. [ ] Autonomy config table
2. [ ] Gmail extraction → `add_lead`
3. [ ] LinkedIn CSV ingestion → `add_lead`
4. [ ] `score_lead()` against resume + preferences
5. [ ] Daily digest as scheduled task
6. [ ] Telegram bot (push alerts)
7. [ ] Outreach drafting (gated)
8. [ ] Web dashboard (optional)

Update checkboxes as work lands — this list is the fastest way for a new
session to know where things stand. Don't let it drift from reality.

## Terminology

- "Lead" = a person, not a company or a job posting
- "Job" = a posting in the database, distinct from "application" (the act
  of applying) and "lead" (a person)
