#!/usr/bin/env python3
"""Manage a local Codex timeline JSON with session-based milestone events."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / ".codex"
TIMELINE_PATH = STATE_DIR / "timeline.json"
SESSION_STATE_PATH = STATE_DIR / "active-session.json"
LOCK_PATH = STATE_DIR / "timeline.lock"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def current_branch() -> str:
    try:
        branch = git_output("branch", "--show-current")
    except subprocess.CalledProcessError:
        return "unknown"
    return branch or "detached-head"


def sanitize_label(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_", " "}:
            cleaned.append("-")
    compact = "".join(cleaned).strip("-")
    return compact or "session"


def ensure_paths() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not TIMELINE_PATH.exists():
        save_timeline({"version": 1, "updated_at": now_iso(), "sessions": []})


@contextmanager
def timeline_lock():
    ensure_paths()
    with LOCK_PATH.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        yield
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def load_timeline() -> dict[str, Any]:
    ensure_paths()
    with TIMELINE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_timeline(payload: dict[str, Any]) -> None:
    payload["updated_at"] = now_iso()
    with TIMELINE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def read_session_state() -> dict[str, Any] | None:
    if not SESSION_STATE_PATH.exists():
        return None
    with SESSION_STATE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_session_state(payload: dict[str, Any]) -> None:
    ensure_paths()
    with SESSION_STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def clear_session_state() -> None:
    if SESSION_STATE_PATH.exists():
        SESSION_STATE_PATH.unlink()


def find_session(timeline: dict[str, Any], session_id: str) -> dict[str, Any]:
    for session in timeline.get("sessions", []):
        if session["session_id"] == session_id:
            return session
    raise SystemExit(f"session '{session_id}' not found in {TIMELINE_PATH}")


def append_event(
    session: dict[str, Any],
    event_type: str,
    summary: str,
    *,
    files_changed: list[str] | None = None,
    user_input: str | None = None,
    command_summary: str | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    event = {
        "timestamp": now_iso(),
        "type": event_type,
        "summary": summary,
    }
    if files_changed:
        event["files_changed"] = files_changed
    if user_input:
        event["user_input"] = user_input
    if command_summary:
        event["command_summary"] = command_summary
    if commit_hash:
        event["commit_hash"] = commit_hash
    session.setdefault("events", []).append(event)
    return event


@dataclass
class CommitInfo:
    commit_hash: str
    subject: str
    committed_at: str
    files_changed: list[str]


def get_commit_info(commit_ref: str) -> CommitInfo:
    subject = git_output("log", "-1", "--format=%s", commit_ref)
    committed_at = git_output("log", "-1", "--format=%cI", commit_ref)
    files_raw = git_output("show", "--format=", "--name-only", commit_ref)
    files_changed = [line for line in files_raw.splitlines() if line.strip()]
    commit_hash = git_output("rev-parse", commit_ref)
    return CommitInfo(
        commit_hash=commit_hash,
        subject=subject,
        committed_at=committed_at,
        files_changed=files_changed,
    )


def command_init(_: argparse.Namespace) -> int:
    ensure_paths()
    print(TIMELINE_PATH)
    return 0


def command_start(args: argparse.Namespace) -> int:
    ensure_paths()
    active_session = read_session_state()
    if active_session:
        raise SystemExit(
            f"an active session already exists: {active_session['session_id']}. "
            "Run timeline-session-end.sh before starting another session."
        )

    branch = current_branch()
    session_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{sanitize_label(branch)}-{uuid.uuid4().hex[:6]}"
    started_at = now_iso()
    session = {
        "session_id": session_id,
        "label": args.label or sanitize_label(args.goal)[:64],
        "branch": branch,
        "started_at": started_at,
        "ended_at": None,
        "status": "active",
        "user_goal": args.goal,
        "events": [],
    }
    append_event(
        session,
        "session_start",
        args.summary or "Started Codex timeline session.",
        user_input=args.user_input or args.goal,
    )

    with timeline_lock():
        timeline = load_timeline()
        timeline.setdefault("sessions", []).append(session)
        save_timeline(timeline)
    write_session_state({"session_id": session_id, "started_at": started_at})
    print(session_id)
    return 0


def command_log(args: argparse.Namespace) -> int:
    state = read_session_state()
    if not state:
        raise SystemExit("no active session. Run scripts/timeline-session-start.sh first.")

    with timeline_lock():
        timeline = load_timeline()
        session = find_session(timeline, state["session_id"])
        append_event(
            session,
            args.type,
            args.summary,
            files_changed=args.files,
            user_input=args.user_input,
            command_summary=args.command_summary,
        )
        save_timeline(timeline)

    print(f"logged {args.type}")
    return 0


def command_end(args: argparse.Namespace) -> int:
    state = read_session_state()
    if not state:
        raise SystemExit("no active session to end.")

    with timeline_lock():
        timeline = load_timeline()
        session = find_session(timeline, state["session_id"])
        if args.summary:
            append_event(session, "summary", args.summary, user_input=args.user_input)
        session["status"] = "completed"
        session["ended_at"] = now_iso()
        save_timeline(timeline)

    clear_session_state()
    print(state["session_id"])
    return 0


def command_post_commit(args: argparse.Namespace) -> int:
    state = read_session_state()
    if not state:
        return 0

    commit_info = get_commit_info(args.commit)

    with timeline_lock():
        timeline = load_timeline()
        session = find_session(timeline, state["session_id"])
        append_event(
            session,
            "commit",
            commit_info.subject,
            files_changed=commit_info.files_changed,
            commit_hash=commit_info.commit_hash,
        )
        session["last_commit_at"] = commit_info.committed_at
        save_timeline(timeline)
    return 0


def command_status(_: argparse.Namespace) -> int:
    ensure_paths()
    state = read_session_state()
    if not state:
        print("no active session")
        return 0

    with timeline_lock():
        timeline = load_timeline()
        session = find_session(timeline, state["session_id"])
    print(json.dumps(session, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create local timeline files if missing")
    init_parser.set_defaults(func=command_init)

    start_parser = subparsers.add_parser("start", help="start a new timeline session")
    start_parser.add_argument("--goal", required=True, help="primary user goal for the session")
    start_parser.add_argument("--label", help="optional short label for the session")
    start_parser.add_argument("--summary", help="optional start summary")
    start_parser.add_argument("--user-input", help="user request excerpt to store")
    start_parser.set_defaults(func=command_start)

    log_parser = subparsers.add_parser("log", help="append a milestone event to the active session")
    log_parser.add_argument(
        "--type",
        required=True,
        choices=["planning", "file_edit", "command", "summary"],
        help="milestone type",
    )
    log_parser.add_argument("--summary", required=True, help="short summary for the event")
    log_parser.add_argument("--files", nargs="*", default=[], help="repo-relative files touched")
    log_parser.add_argument("--user-input", help="relevant user input excerpt")
    log_parser.add_argument("--command-summary", help="summary of the command or validation")
    log_parser.set_defaults(func=command_log)

    end_parser = subparsers.add_parser("end", help="end the active session")
    end_parser.add_argument("--summary", help="closing summary for the session")
    end_parser.add_argument("--user-input", help="optional user input excerpt")
    end_parser.set_defaults(func=command_end)

    commit_parser = subparsers.add_parser("post-commit", help="append a commit event from git hooks")
    commit_parser.add_argument("--commit", default="HEAD", help="commit ref to log")
    commit_parser.set_defaults(func=command_post_commit)

    status_parser = subparsers.add_parser("status", help="show the active session payload")
    status_parser.set_defaults(func=command_status)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
