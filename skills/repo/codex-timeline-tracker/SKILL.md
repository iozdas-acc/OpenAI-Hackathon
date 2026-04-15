---
name: codex-timeline-tracker
description: Automatically capture a presentation-friendly Codex timeline into one JSON file with session-based milestones. Use when the user wants to track planning, commands, file edits, commits, and final summaries across a coding session.
---

# Codex Timeline Tracker

Use this skill when the user wants a reusable Codex timeline for later demos, retrospectives, or productivity review.

## What it records

- Session start and end
- Planning milestones
- Command milestones
- File edit milestones
- Commit milestones through a git hook
- Final session summaries

This workflow stores short summaries only. It does not store full diffs or full conversation transcripts.

## Setup

Run this once per clone:

```bash
scripts/install-timeline-hooks.sh
```

The local timeline file is:

```text
.codex/timeline.json
```

## Session workflow

Start a session as soon as work begins:

```bash
scripts/timeline-session-start.sh --goal "Add Oracle MCP support to Docker setup"
```

Log milestone summaries as work progresses:

```bash
scripts/timeline-log.sh --type planning --summary "Chose repo-managed git-hook timeline tracking" --user-input "Need a skill that keeps tracing the Codex timeline"
scripts/timeline-log.sh --type command --summary "Validated the hook installer and session scripts" --command-summary "Ran install, start, log, and end scripts locally"
scripts/timeline-log.sh --type file_edit --summary "Added timeline skill, scripts, and hook template" --files scripts/codex_timeline.py scripts/install-timeline-hooks.sh skills/repo/codex-timeline-tracker/SKILL.md
```

Commits are appended automatically after `git commit` while a session is active.

Close the session at the end of the task:

```bash
scripts/timeline-session-end.sh --summary "Completed Stage 0 Codex timeline scaffold and verified JSON output"
```

## Working rules

- Install hooks before relying on automatic commit capture.
- Start one session per coherent task.
- Keep milestone summaries short and presentation-friendly.
- For file edits, record file paths and a concise explanation, not raw diffs.
- If there is no active session, logging should fail loudly instead of silently dropping data.
