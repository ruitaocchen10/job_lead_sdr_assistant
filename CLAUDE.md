# CLAUDE.md

# Job Lead SDR Agent

## What this is

A "Sales Development Representative" agent for job searching. It
finds leads (people worth reaching out to — recruiters, hiring managers,
warm contacts) by mining LinkedIn, company websites, etc. It then identifies potential connections, leads, and opportunities using the user's resume, preferences, jobs they might have applied to, and communicates with the user through one or more chat interfaces.

This is self-hosted — users clone the repo, fill in their credentials, and run `docker-compose up`. Each user runs their own isolated instance. The agent is designed for flexibility so users can choose their own interface layers, database layers, and context sources.

## Architecture at a glance

Four layers, data flows bottom to top:

```
Interface layer → Telegram bot polling (pluggable: Slack, Discord, web UI via webhooks)
Agent layer     → PydanticAI (agent loop, tools, typed outputs) + LiteLLM (model routing)
Database layer  → Notion (pluggable: Supabase, Google Sheets)
Context layer   → Gmail, LinkedIn CSV, resume
```

Full design rationale lives in `docs/architecture.md` — read it before making structural changes, don't duplicate it here.

## Tech stack

- **Backend**: Python + FastAPI (for future webhook-based interfaces; not used by Telegram)
- **Agent**: PydanticAI (agent loop, tool registration, dependency injection, typed outputs)
- **Model routing**: LiteLLM (model-agnostic wrapper — Claude, GPT-4, Gemini, etc.; configured via a single string in config.yaml)
- **Async execution**: APScheduler (scheduled triggers); Telegram polling loop handles reactive triggers
- **Database adapter**: Notion API (first implementation; abstract interface supports others)
- **Interface adapter**: Telegram via python-telegram-bot in polling mode — no public URL required, runs fully locally
- **Gmail**: Gmail API, queried on-demand via tool functions — no ingestion pipeline or storage
- **LinkedIn**: Manual CSV export
- **Deploy**: Docker Compose (self-hosted)

## Trigger modes

Agent runs are initiated by triggers, which users can configure:

- **Reactive**: Agent responds when the user messages it via the interface
- **Scheduled**: Agent runs on a cron schedule (e.g. every morning, checks Gmail and surfaces leads)

Multiple triggers can be active simultaneously.

## Project structure

```
job_lead_sdr_assistant/
├── docker-compose.yml          # user entry point
├── Dockerfile
├── .env.example                # credentials template
├── config.yaml.example         # agent behavior config
├── requirements.txt
├── scripts/
│   └── setup_gmail.py          # one-time Gmail OAuth setup
├── docs/
└── src/
    ├── api/main.py             # FastAPI app
    ├── agent/                  # PydanticAI agent definition, tools, prompts
    ├── adapters/               # database/ and interface/ ABCs + implementations
    ├── context/                # gmail.py, linkedin.py, resume.py
    ├── triggers/               # message.py, schedule.py
    └── scheduler.py            # APScheduler setup for scheduled triggers
```

Full structure and rationale in `docs/architecture.md`.

## Extensibility

Database and interface layers use an abstract adapter pattern. Adding a new database (Supabase, Google Sheets) or interface (Slack, Discord) means implementing the relevant abstract class — no changes to core agent logic. See `docs/architecture.md` for the adapter contracts.
