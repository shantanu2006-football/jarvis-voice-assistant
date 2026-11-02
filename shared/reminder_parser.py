"""Rule-based date parsing for voice-added reminders. No LLM — just dateparser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from dateparser.search import search_dates

_SETTINGS = {
    "PREFER_DATES_FROM": "future",
    "RETURN_AS_TIMEZONE_AWARE": False,
}
_LANGUAGES = ["en"]  # without this, dateparser's free-text search matches stray words as dates in other locales

_LEAD_WORD = re.compile(r"(this|next|on|by|for)\s+$", re.IGNORECASE)
_TRAILING_CONNECTOR = re.compile(r"\s+(this|next|on|by|for)\s*$", re.IGNORECASE)


@dataclass
class ParsedReminder:
    task: str
    due_date: date | None  # None if no date phrase was found — caller should ask or default to today


def parse_reminder(text: str, now: datetime | None = None) -> ParsedReminder:
    """Split free-form reminder speech into a task description and a due date.

    Example: "remind me to submit the report this Friday"
      -> task="submit the report", due_date=<upcoming Friday>
    """
    settings = dict(_SETTINGS)
    if now is not None:
        settings["RELATIVE_BASE"] = now

    matches = search_dates(text, settings=settings, languages=_LANGUAGES)

    if not matches:
        return ParsedReminder(task=_clean(text), due_date=None)

    # Take the first date phrase found; widen it to include a leading "this"/"next" if present,
    # then strip it out of the text to get the task.
    date_phrase, parsed_dt = matches[0]
    start = text.index(date_phrase)
    lead_match = _LEAD_WORD.search(text[:start])
    if lead_match:
        start = lead_match.start()
    phrase_end = text.index(date_phrase, start) + len(date_phrase)
    task_text = text[:start] + text[phrase_end:]
    task_text = _TRAILING_CONNECTOR.sub("", task_text)
    return ParsedReminder(task=_clean(task_text), due_date=parsed_dt.date())


def _clean(text: str) -> str:
    text = text.strip(" .,:;-")
    for lead in ("remind me to ", "add this to the reminder for this day ", "add a reminder to ", "remind me "):
        if text.lower().startswith(lead):
            text = text[len(lead):]
    return text.strip(" .,:;-")
