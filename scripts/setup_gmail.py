"""
One-time Gmail OAuth setup. Run this before starting the agent.

Prerequisites:
  1. Go to https://console.cloud.google.com and select your project
  2. Enable the Gmail API: APIs & Services > Enable APIs > search 'Gmail API'
     (or run: gcloud services enable gmail.googleapis.com)
  3. Configure the OAuth consent screen: APIs & Services > OAuth consent screen
     - Choose 'External', fill in app name and your email
     - Add your email as a test user under 'Test users'
  4. Create credentials: APIs & Services > Credentials > Create Credentials > OAuth client ID
     - Choose 'Desktop app' as the application type
  5. Download the JSON and save it as credentials.json in the project root

Then run: python scripts/setup_gmail.py
"""

import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",  # needed to apply sdr-processed label
]

ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = ROOT / "credentials.json"
TOKEN_DIR = Path.home() / ".config" / "job-lead-sdr"
TOKEN_FILE = TOKEN_DIR / "token.json"


def save_token(creds: Credentials) -> None:
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def main() -> None:
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            print(f"Already authenticated. Token found at {TOKEN_FILE}")
            return
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_token(creds)
            print(f"Token refreshed and saved to {TOKEN_FILE}")
            return

    if not CREDENTIALS_FILE.exists():
        print(
            "credentials.json not found in the project root.\n\n"
            "To create it:\n"
            "  1. Go to https://console.cloud.google.com and select your project\n"
            "  2. Enable the Gmail API: APIs & Services > Enable APIs > search 'Gmail API'\n"
            "  3. Configure the OAuth consent screen: APIs & Services > OAuth consent screen\n"
            "     - Choose 'External', fill in app name and your email\n"
            "     - Add your email as a test user under 'Test users'\n"
            "  4. Create credentials: APIs & Services > Credentials > Create Credentials > OAuth client ID\n"
            "     - Choose 'Desktop app' as the application type\n"
            "  5. Download the JSON and save it as credentials.json in the project root\n\n"
            "Then re-run this script."
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    save_token(creds)
    print(f"\nGmail authenticated successfully. Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
