# Jarvis

This is a home voice assistant that is rule-based by design. It uses no LLM: spoken commands are matched with regex and keywords. That keeps it fast, predictable and private.

## How it works

```
"Hey Jarvis, remind me to submit the report this Friday"
        │
        ▼
  Raspberry Pi 5 (planned): wake word → speech-to-text → text-to-speech
        │  POST /command {"text": ...}   over the LAN
        ▼
  Windows PC agent (Flask, pc_agent/server.py)
        │  shared/router.py   → Command(type, payload)
        ├─ open      → launch an app / URL / URI   (pc_agent/app_launcher.py)
        ├─ search    → Google search in the browser
        ├─ reminder  → add / read Google Tasks     (pc_agent/tasks_client.py)
        └─ routine   → staggered multi-app startup
        │
        ▼
  {"speak": "Added: submit the report."}  → spoken back on the Pi
```

## Status

| Part | State |
|---|---|
| Command router (`shared/router.py`) | Built and tested |
| Date parsing for reminders (`shared/reminder_parser.py`) | Built and tested |
| Google Tasks read/write via the Tasks API (`pc_agent/tasks_client.py`) | Built and live-tested |
| Windows PC agent: Flask server + staggered app launcher | Built and live-tested |
| Pi voice front-end: wake word (openWakeWord), speech-to-text (faster-whisper), text-to-speech (piper) | **Not built yet** |

## Example commands

| Say | What happens |
|---|---|
| "open spotify" | Opens the target from `shared/open_targets.json` |
| "search for flask tutorials on google" | Opens a Google search |
| "remind me to submit the report this Friday" | Adds a Google Task due on the coming Friday |
| "what are my reminders this week" | Reads back tasks due in the next 7 days |

## Run the PC agent

```bash
pip install -r requirements.txt
# Put a Google OAuth "Desktop app" client secret at pc_agent/secrets/google_client_secret.json
python pc_agent/server.py          # run from the repo root; listens on :5000
curl -X POST localhost:5000/command -H 'Content-Type: application/json' \
     -d '{"text": "open youtube"}'
```

Add new spoken shortcuts in `shared/open_targets.json`; the matching code doesn't need to change.

The server has no authentication, so run it only on a trusted home network.
