from abc import ABC, abstractmethod
from datetime import date
from typing import Literal

from pydantic import BaseModel


class Lead(BaseModel):
    id: str = ""  # Notion page ID — populated when reading from the database
    name: str
    company: str
    role: str
    type: Literal["Recruiter", "Hiring Manager", "Warm Contact"]
    status: Literal["New", "Contacted", "Replied", "Archived"] = "New"
    source: Literal["LinkedIn", "Gmail", "Manual"]
    linkedin_url: str = ""
    email: str = ""
    notes: str = ""
    last_contacted: date | None = None


class DatabaseAdapter(ABC):
    @abstractmethod
    async def save_lead(self, lead: Lead) -> str:
        """Save a new lead. Returns the database ID of the created record."""
        ...

    @abstractmethod
    async def get_leads(self, status: str | None = None) -> list[Lead]:
        """Return leads, optionally filtered by status."""
        ...

    @abstractmethod
    async def update_lead(self, id: str, updates: dict) -> None:
        """Update fields on an existing lead by its database ID."""
        ...

    @abstractmethod
    async def delete_lead(self, id: str) -> None:
        """Remove a lead by its database ID."""
        ...
