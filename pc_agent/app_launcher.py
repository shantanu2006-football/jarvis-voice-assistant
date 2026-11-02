"""Staggered app launcher for the "daddy's home" routine and generic `open` commands.

Uses cmd's `start` (the same App Paths / URI-protocol resolution Windows uses for
a double-clicked shortcut) — confirmed working on this PC on 2026-08-08 for
`outlook`, `msteams:`, and `chrome` with no hardcoded install paths needed.
"""

from __future__ import annotations

import subprocess
import time

STAGGER_SECONDS = 6  # mid-point of the 5-7s spec range, avoids CPU/disk contention

DADDYS_HOME_CHROME_TABS = [
    "https://mail.google.com",
    "https://tasks.google.com",
]


def _start(*args: str) -> None:
    """Launch something the same way typing `start <args>` at a cmd prompt would."""
    subprocess.Popen(["cmd", "/c", "start", "", *args])


def open_target(target: str) -> None:
    """Open a single resolved target (URL, app name, or URI) — used by the generic `open` command."""
    _start(target)


def daddys_home() -> None:
    """Outlook -> Teams -> Chrome (Gmail + Google Tasks tabs), ~6s apart."""
    _start("outlook")
    time.sleep(STAGGER_SECONDS)

    _start("msteams:")
    time.sleep(STAGGER_SECONDS)

    _start("chrome", *DADDYS_HOME_CHROME_TABS)
