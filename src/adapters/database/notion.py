# WE SHOULD MAKE THE PROGRAM AUTOMATICALLY SET UP A NOTION DATABASE

import os
from datetime import date

from notion_client import AsyncClient

from src.adapters.database.base import DatabaseAdapter, Lead

# Maps Lead field names to Notion property names
_PROPERTY_NAMES = {
    "name": "Name",
    "company": "Company",
    "role": "Role",
    "type": "Type",
    "status": "Status",
    "source": "Source",
    "linkedin_url": "LinkedIn URL",
    "email": "Email",
    "notes": "Notes",
    "last_contacted": "Last Contacted",
}


def _build_properties(lead: Lead) -> dict:
    return {
        "Name": {"title": [{"text": {"content": lead.name}}]},
        "Company": {"rich_text": [{"text": {"content": lead.company}}]},
        "Role": {"rich_text": [{"text": {"content": lead.role}}]},
        "Type": {"select": {"name": lead.type}},
        "Status": {"select": {"name": lead.status}},
        "Source": {"select": {"name": lead.source}},
        "LinkedIn URL": {"url": lead.linkedin_url or None},
        "Email": {"email": lead.email or None},
        "Notes": {"rich_text": [{"text": {"content": lead.notes}}]},
        "Last Contacted": (
            {"date": {"start": lead.last_contacted.isoformat()}}
            if lead.last_contacted
            else {"date": None}
        ),
    }


def _parse_page(page: dict) -> Lead:
    props = page["properties"]

    def text(key: str) -> str:
        items = props[key].get("rich_text", [])
        return items[0]["text"]["content"] if items else ""

    def title(key: str) -> str:
        items = props[key].get("title", [])
        return items[0]["text"]["content"] if items else ""

    def select(key: str) -> str:
        s = props[key].get("select")
        return s["name"] if s else ""

    def url(key: str) -> str:
        return props[key].get("url") or ""

    def email(key: str) -> str:
        return props[key].get("email") or ""

    def notion_date(key: str) -> date | None:
        d = props[key].get("date")
        return date.fromisoformat(d["start"]) if d else None

    return Lead(
        id=page["id"],
        name=title("Name"),
        company=text("Company"),
        role=text("Role"),
        type=select("Type"),
        status=select("Status"),
        source=select("Source"),
        linkedin_url=url("LinkedIn URL"),
        email=email("Email"),
        notes=text("Notes"),
        last_contacted=notion_date("Last Contacted"),
    )


class NotionAdapter(DatabaseAdapter):
    def __init__(self, api_key: str, database_id: str) -> None:
        self._client = AsyncClient(auth=api_key)
        self._database_id = database_id

    async def save_lead(self, lead: Lead) -> str:
        response = await self._client.pages.create(
            parent={"database_id": self._database_id},
            properties=_build_properties(lead),
        )
        return response["id"]

    async def get_leads(self, status: str | None = None) -> list[Lead]:
        filter_obj = (
            {"property": "Status", "select": {"equals": status}} if status else None
        )
        response = await self._client.databases.query(
            database_id=self._database_id,
            **({"filter": filter_obj} if filter_obj else {}),
        )
        return [_parse_page(page) for page in response["results"]]

    async def update_lead(self, id: str, updates: dict) -> None:
        properties = {}
        for field, value in updates.items():
            notion_key = _PROPERTY_NAMES.get(field)
            if not notion_key:
                continue
            if field == "name":
                properties[notion_key] = {"title": [{"text": {"content": value}}]}
            elif field in ("company", "role", "notes"):
                properties[notion_key] = {"rich_text": [{"text": {"content": value}}]}
            elif field in ("type", "status", "source"):
                properties[notion_key] = {"select": {"name": value}}
            elif field == "linkedin_url":
                properties[notion_key] = {"url": value or None}
            elif field == "email":
                properties[notion_key] = {"email": value or None}
            elif field == "last_contacted":
                properties[notion_key] = (
                    {"date": {"start": value.isoformat()}} if value else {"date": None}
                )
        await self._client.pages.update(page_id=id, properties=properties)

    async def delete_lead(self, id: str) -> None:
        await self._client.pages.update(page_id=id, archived=True)


def create_notion_adapter(config: dict) -> NotionAdapter:
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        raise EnvironmentError("NOTION_API_KEY is not set in environment or .env file.")
    database_id = config["database"]["database_id"]
    return NotionAdapter(api_key=api_key, database_id=database_id)
