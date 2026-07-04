from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext

from src.agent.prompts import SYSTEM_PROMPT
from src.config import load_config
from src.context.linkedin import search_connections
from src.context.profile import load_profile


@dataclass
class AgentDeps:
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
