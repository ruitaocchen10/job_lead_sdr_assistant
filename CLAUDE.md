# CLAUDE.md

# Job Lead SDR Agent

## What this is

A "Sales Development Representative" agent for job searching. It
finds leads (people worth reaching out to — recruiters, hiring managers,
warm contacts) by mining LinkedIn, company websites, etc. It then identifies potential connections, leads, and opportunities using the user's resume, preferences, jobs they might have applied to, and communicates with the user through one or more chat interfaces.

This is meant to have flexibility and customizability for users to be able to choose their own interface layers, database layers, etc.

## Architecture at a glance

Four layers, data flows bottom to top:

```
Interface layer → Telegram bot (pluggable: Slack, Discord, web UI)
Agent layer     → LiteLLM-powered reasoning (model-agnostic)
Database layer  → Notion (pluggable: Supabase, Google Sheets)
Context layer   → Gmail, LinkedIn CSV, resume
```

Full design rationale lives in `docs/architecture.md` — read it before making structural changes, don't duplicate it here.

## Tech stack

- **Backend**: Python + FastAPI
- **Agent**: LiteLLM (model-agnostic wrapper — Claude, GPT-4, Gemini, etc.)
- **Task queue**: Celery + Redis (long-running agent jobs run async)
- **Database adapter**: Notion API (first implementation; abstract interface supports others)
- **Interface adapter**: Telegram via python-telegram-bot (first implementation; abstract interface supports others)
- **Gmail ingestion**: Gmail API + Cloud Pub/Sub push notifications (not polling)
- **LinkedIn ingestion**: Manual CSV export
- **Deploy**: Cloud Run (auto-scales)

## Trigger modes

Agent runs are initiated by triggers, which users can configure:

- **Reactive**: Agent responds when the user messages it via the interface
- **Webhook**: Agent reacts to external events (e.g. Gmail push notification)
- **Scheduled**: Agent runs on a cron schedule (e.g. every morning)

Multiple triggers can be active simultaneously.

## Extensibility

Database and interface layers use an abstract adapter pattern. Adding a new database (Supabase, Google Sheets) or interface (Slack, Discord) means implementing the relevant abstract class — no changes to core agent logic. See `docs/architecture.md` for the adapter contracts.
