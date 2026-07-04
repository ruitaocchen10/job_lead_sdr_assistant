import csv
from pathlib import Path

CONNECTIONS_PATH = Path("data/linkedin_connections.csv")


def search_connections(company: str | None = None) -> list[dict]:
    if not CONNECTIONS_PATH.exists():
        raise FileNotFoundError(
            f"LinkedIn connections CSV not found at {CONNECTIONS_PATH}. "
            "Export it from LinkedIn: Settings → Data Privacy → Get a copy of your data."
        )
    with CONNECTIONS_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [
            {
                "first_name": row["First Name"],
                "last_name": row["Last Name"],
                "company": row["Company"],
                "position": row["Position"],
                "url": row["URL"],
                "email": row.get("Email Address", ""),
            }
            for row in reader
            if not company or company.lower() in row["Company"].lower()
        ]
    return rows
