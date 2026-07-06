from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext

from src.adapters.database.base import DatabaseAdapter, Lead
from src.agent.prompts import SYSTEM_PROMPT
from src.config import load_config
from src.context.linkedin import search_connections
from src.context.profile import load_profile


@dataclass
class AgentDeps:
    db: DatabaseAdapter
    user_id: str
    trigger: Literal["message", "schedule"]


_config = load_config()
_profile = load_profile()

agent = Agent(
    _config["model"],
    deps_type=AgentDeps,
    instructions=SYSTEM_PROMPT.format(profile=_profile),
)


@agent.tool
async def search_linkedin_connections(
    ctx: RunContext[AgentDeps], company: str | None = None
) -> list[dict]:
    """Search the user's LinkedIn connections, optionally filtered by company name."""
    return search_connections(company)


@agent.tool
async def save_lead(
    ctx: RunContext[AgentDeps],
    name: str,
    company: str,
    role: str,
    type: Literal["Recruiter", "Hiring Manager", "Warm Contact"],
    source: Literal["LinkedIn", "Gmail", "Manual"],
    linkedin_url: str = "",
    email: str = "",
    notes: str = "",
) -> str:
    """Save a new lead to the database. Returns the ID of the created record."""
    lead = Lead(
        name=name,
        company=company,
        role=role,
        type=type,
        source=source,
        linkedin_url=linkedin_url,
        email=email,
        notes=notes,
    )
    return await ctx.deps.db.save_lead(lead)


@agent.tool
async def list_leads(
    ctx: RunContext[AgentDeps], status: str | None = None
) -> list[dict]:
    """List leads from the database, optionally filtered by status (New, Contacted, Replied, Archived)."""
    leads = await ctx.deps.db.get_leads(status=status)
    return [lead.model_dump() for lead in leads]
