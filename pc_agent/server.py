"""HTTP endpoint the Pi calls over LAN with transcribed text; routes it and acts.

Run with: py pc_agent/server.py  (from the repo root, so `shared` and `pc_agent`
resolve as top-level packages).
"""

from __future__ import annotations

import threading
from urllib.parse import quote_plus

from flask import Flask, jsonify, request

from pc_agent import app_launcher, tasks_client
from shared.router import route

app = Flask(__name__)


def _tasks_summary(days: int) -> str:
    due = tasks_client.list_due_within(days)
    if not due:
        return "You have no tasks due."
    lines = [f"{t['title']} due {t['due'].strftime('%A')}" for t in due]
    noun = "task" if len(due) == 1 else "tasks"
    return f"You have {len(due)} {noun} due: " + "; ".join(lines) + "."


@app.route("/command", methods=["POST"])
def command():
    text = (request.get_json(force=True) or {}).get("text", "")
    cmd = route(text)

    if cmd.type == "routine" and cmd.payload["name"] == "daddys_home":
        threading.Thread(target=app_launcher.daddys_home, daemon=True).start()
        return jsonify(speak=_tasks_summary(6))

    if cmd.type == "open":
        app_launcher.open_target(cmd.payload["target"])
        return jsonify(speak="Opening it now.")

    if cmd.type == "search":
        query = cmd.payload["query"]
        app_launcher.open_target("https://www.google.com/search?q=" + quote_plus(query))
        return jsonify(speak=f"Searching Google for {query}.")

    if cmd.type == "reminder_write":
        tasks_client.add_task(cmd.payload["task"], cmd.payload["due_date"])
        return jsonify(speak=f"Added: {cmd.payload['task']}.")

    if cmd.type == "reminder_read":
        return jsonify(speak=_tasks_summary(6))

    return jsonify(speak="Sorry, I didn't understand that.")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
