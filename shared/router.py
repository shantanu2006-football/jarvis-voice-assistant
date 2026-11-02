"""Rule-based command router — turns transcribed text into a structured Command.

No LLM: everything here is keyword/regex matching, checked in priority order.
Add new phrases to the trigger lists below, or new open-able things to open_targets.json —
no need to touch the matching logic itself for those.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .reminder_parser import parse_reminder

_OPEN_TARGETS_PATH = Path(__file__).parent / "open_targets.json"

_ROUTINE_TRIGGERS = {
    "daddys_home": [r"daddy'?s home", r"daddy is home"],
}

_REMINDER_WRITE_TRIGGERS = [
    r"^remind me to ",
    r"^add (this )?to (the )?reminder",
    r"^add a reminder",
]

_REMINDER_READ_TRIGGERS = [
    r"what are my reminders",
    r"reminders for (today|this week)",
    r"read (me )?my reminders",
]

_MUSIC_TRIGGERS = [r"listen to (some )?music", r"play (some )?music", r"play (some )?songs"]

_SEARCH_PATTERN = re.compile(r"search (?:for )?(.+?) on google", re.IGNORECASE)
_OPEN_PATTERN = re.compile(r"^open (?:the )?(.+)$", re.IGNORECASE)


@dataclass
class Command:
    type: str  # "routine" | "open" | "search" | "reminder_write" | "reminder_read" | "unknown"
    payload: dict[str, Any] = field(default_factory=dict)


def route(text: str) -> Command:
    text = text.strip()
    lower = text.lower()

    for name, patterns in _ROUTINE_TRIGGERS.items():
        if any(re.search(p, lower) for p in patterns):
            return Command(type="routine", payload={"name": name})

    if any(re.search(p, lower) for p in _REMINDER_WRITE_TRIGGERS):
        parsed = parse_reminder(text)
        return Command(type="reminder_write", payload={"task": parsed.task, "due_date": parsed.due_date})

    if any(re.search(p, lower) for p in _REMINDER_READ_TRIGGERS):
        return Command(type="reminder_read", payload={})

    search_match = _SEARCH_PATTERN.search(text)
    if search_match:
        return Command(type="search", payload={"query": search_match.group(1).strip()})

    if any(re.search(p, lower) for p in _MUSIC_TRIGGERS):
        return Command(type="open", payload={"target": _resolve_target("music")})

    open_match = _OPEN_PATTERN.match(text)
    if open_match:
        name = open_match.group(1).strip().lower()
        return Command(type="open", payload={"target": _resolve_target(name)})

    return Command(type="unknown", payload={"text": text})


def _resolve_target(name: str) -> str:
    with open(_OPEN_TARGETS_PATH) as f:
        targets = json.load(f)
    return targets.get(name, name)  # unknown name: PC agent will still try `start <name>` as-is
