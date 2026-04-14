---
name: iteration-stage-gate
description: Enforce staged delivery for the hackathon build. Use when planning or implementing work so the repo advances in explicit iterations and later-stage features do not leak into the current scope.
---

# Iteration Stage Gate

Use this skill whenever work needs to be checked against the current project stage.

## Stage Policy

- Stage 0: scaffolding only
- Stage 1: semantic mapping golden path
- Stage 2: live context graph updates
- Stage 3: business dictionary output
- Stage 4: migration planning stub

## Required Checks

Before starting work:

- Identify the active stage.
- Confirm the requested change belongs in that stage.
- If the change belongs to a later stage, either defer it or create only the minimum placeholder needed now.

Before marking work complete:

- Confirm the output is visible, runnable, or documented for the current stage.
- Confirm no later-stage complexity was pulled in without explicit approval.

## Repo Bias

- Prefer one convincing vertical slice over broad shallow coverage.
- Prefer demo-visible functionality over hidden infrastructure.
