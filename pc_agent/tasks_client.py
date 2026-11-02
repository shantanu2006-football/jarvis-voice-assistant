"""Google Tasks integration — read tasks due soon, write new reminders.

First call opens a browser for a one-time OAuth approval, then caches a token
in secrets/token.json so it won't ask again.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks"]

_SECRETS_DIR = Path(__file__).parent / "secrets"
_CLIENT_SECRET_PATH = _SECRETS_DIR / "google_client_secret.json"
_TOKEN_PATH = _SECRETS_DIR / "token.json"


def _get_credentials() -> Credentials:
    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CLIENT_SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json())
    return creds


def _service():
    return build("tasks", "v1", credentials=_get_credentials())


def add_task(title: str, due: date | None = None) -> dict:
    body = {"title": title}
    if due is not None:
        # Tasks API wants an RFC3339 timestamp; date-only reminders use midnight UTC by convention.
        body["due"] = datetime(due.year, due.month, due.day).isoformat() + "Z"
    return _service().tasks().insert(tasklist="@default", body=body).execute()


def list_due_within(days: int) -> list[dict]:
    """Incomplete tasks due within the next `days` days (0 = today only, 6 = this week)."""
    service = _service()
    tasklists = service.tasklists().list().execute().get("items", [])
    cutoff = datetime.combine(date.today() + timedelta(days=days), datetime.max.time())

    due_tasks = []
    for tl in tasklists:
        items = service.tasks().list(tasklist=tl["id"], showCompleted=False).execute().get("items", [])
        for item in items:
            due_str = item.get("due")
            if not due_str:
                continue
            due_dt = datetime.fromisoformat(due_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if due_dt <= cutoff:
                due_tasks.append({"title": item["title"], "due": due_dt.date()})
    due_tasks.sort(key=lambda t: t["due"])
    return due_tasks
