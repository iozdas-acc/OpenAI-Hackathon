---
name: repo-bootstrap
description: Scaffold and maintain the hackathon repository structure, shared docs, and local developer setup. Use when creating repo folders, sync scripts, shared project conventions, or documentation that supports the build without implementing product features.
---

# Repo Bootstrap

Use this skill for repository setup work only.

## Scope

- Create or update shared repo structure.
- Add or refine project scaffolding docs.
- Maintain local helper scripts such as skill sync scripts.
- Keep setup changes lightweight and reversible.

## Rules

- Do not implement product features.
- Prefer the smallest scaffold that unblocks the next iteration.
- Keep canonical shared assets inside the repo so teammates can get them from git.
- Local machine convenience should be handled by scripts, not by committed machine-specific files.

## For This Repo

- Skills live under `skills/` and are organized by category.
- Local Codex availability is handled by symlinks into `~/.codex/skills`.
- Repo docs should explain what is portable, what needs adaptation, and what is deferred.
- Stage 0 work is scaffold-only and should not include runtime product logic.
