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
- **LinkedIn**: Manual CSV export (scraping is not viable — LinkedIn is a JS SPA behind auth; their ToS prohibits it and accounts risk suspension)
- **Lead enrichment**: Apollo.io API (find contacts by company/role), Hunter.io (email finding by domain)
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
├── context/
│   └── profile.md              # user's resume summary, target roles, preferences, tone (static)
├── data/
│   └── linkedin_connections.csv  # raw LinkedIn export — refresh by re-exporting from LinkedIn
└── src/
    ├── api/main.py             # FastAPI app
    ├── agent/                  # PydanticAI agent definition, tools, prompts
    ├── adapters/               # database/ and interface/ ABCs + implementations
    ├── context/                # gmail.py, linkedin.py, resume.py
    ├── triggers/               # message.py, schedule.py
    └── scheduler.py            # APScheduler setup for scheduled triggers
```

Full structure and rationale in `docs/architecture.md`.

## Agent tools

The agent is a **single PydanticAI agent with multiple tools** — not a multi-agent system. Multi-agent adds orchestration complexity without benefit at this scale; the pipeline is sequential, not parallel. Build and test each tool independently before wiring to the agent:

| Tool            | Purpose                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| `search_jobs()` | Query job boards for listings (Indeed, Glassdoor, LinkedIn Jobs public)     |
| `find_leads()`  | Apollo.io API — given company → return contacts (recruiter, hiring manager) |
| `read_gmail()`  | Search/read emails on demand via Gmail API                                  |
| `draft_email()` | Compose and save to Gmail drafts                                            |
| `get_context()` | Load user profile from `context/profile.md`                                 |
| `save_lead()`   | Write lead to Notion                                                        |
| `list_leads()`  | Read leads from Notion                                                      |

## Lead pipeline

```
Job board (company is hiring)
    → Apollo API (find recruiter/hiring manager at that company)
    → LinkedIn connections CSV (check for warm contacts at that company)
    → Draft outreach email
```

LinkedIn profile scraping is not used. Google search (`site:linkedin.com/in`) can surface public profile snippets when needed.

## Context memory model

Context is split by how often it changes — do not re-read all sources on every agent run:

| Type        | Storage                          | Examples                                                          | Load strategy                                    |
| ----------- | -------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------ |
| Static      | `context/profile.md`             | Resume summary, target roles, preferred tone, company preferences | Loaded once at startup into system prompt        |
| Semi-static | `data/linkedin_connections.csv`  | Connections (name, company, title) — raw LinkedIn export          | Tool call on demand; refresh by re-exporting CSV |
| Dynamic     | Fetched on demand via tools      | New emails, fresh job listings, Apollo contacts                   | Tool call, per task                              |
| Accumulated | Notion database                  | Lead notes, application status, follow-up history                 | Tool call, read/write per task                   |

`context/profile.md` is the only context loaded into the system prompt — it's the only source small enough and stable enough to justify that. Everything else is behind tools and fetched only when the task requires it.

## Extensibility

Database and interface layers use an abstract adapter pattern. Adding a new database (Supabase, Google Sheets) or interface (Slack, Discord) means implementing the relevant abstract class — no changes to core agent logic. See `docs/architecture.md` for the adapter contracts.
