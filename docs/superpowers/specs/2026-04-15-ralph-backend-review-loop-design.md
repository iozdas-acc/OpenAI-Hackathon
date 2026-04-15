# Ralph Backend Review Loop Design

## Date

2026-04-15

## Goal

Add a continuous, review-only "Ralph loop" for the backend codebase that:

- runs on a fixed 15-20 minute cadence
- produces a flattened merged backend snapshot for each run
- performs recurring backend code review
- stores timestamped review artifacts in a tracked repo folder
- never edits application code automatically

## Why This Slice

The repo already has active backend work across the API, orchestration, crawlers, migration, and
graph-building surfaces. The immediate need is not another product feature. The immediate need is a
repeatable way to inspect the backend as it changes, preserve a flattened audit trail, and surface
new or persistent issues without relying on a one-off manual review.

This loop is intentionally operational rather than product-facing. It supports the current Stage 1
milestone by making the backend easier to inspect, safer to evolve, and more understandable.

## Scope

In scope:

- a local script-driven review loop under `scripts/`
- backend-only source collection
- one flattened merged text artifact per loop run
- one timestamped review report per loop run
- a tracked output folder for historical Ralph runs
- a "latest" view for easy inspection
- simple run metadata such as timestamp, duration, changed files, and summarized findings
- overlap protection so only one Ralph cycle runs at a time

Out of scope:

- autonomous source-code edits
- git commits or pushes
- frontend review
- review of generated artifacts or local environment folders
- external scheduler requirements such as `cron` or `launchd` as the primary runtime path
- a claim of literal perfection as the stop condition

## Core Decision

Use a repo-local, review-only loop with an internal sleep interval instead of an external daemon or
an autofix agent.

This keeps the workflow portable and understandable:

- the loop can be started from the repo with one command
- cadence is explicit and configurable
- outputs are committed as plain files in a known location
- the loop cannot silently mutate the application codebase

## Recommended Approach

Implement a single Ralph runner script and one small review pipeline:

1. Resolve the backend source set.
2. Compute the current backend file list and change summary.
3. Generate a single flattened merged text snapshot of the backend.
4. Run the backend review pass.
5. Write a timestamped run folder with artifacts.
6. Refresh a `latest/` copy for quick access.
7. Sleep for the configured interval and repeat.

This produces a durable revision trail without adding architectural complexity to the product
runtime.

## Backend Review Surface

The Ralph loop should review only these backend-owned paths:

- `apps/api/`
- `services/orchestrator/`
- `services/crawlers/`
- `services/migration/`
- `services/context_graph_builder.py`

It should ignore:

- `.git/`
- `.venv/`
- `node_modules/`
- `.next/`
- `.data/`
- `__pycache__/`
- any generated report output folders

The intention is to capture authored backend logic only, not dependencies, caches, or local state.

## Output Layout

Store run artifacts under a tracked repo folder:

- `reports/ralph-backend/runs/<timestamp>/flattened-backend.txt`
- `reports/ralph-backend/runs/<timestamp>/review.md`
- `reports/ralph-backend/runs/<timestamp>/meta.json`
- `reports/ralph-backend/latest/flattened-backend.txt`
- `reports/ralph-backend/latest/review.md`
- `reports/ralph-backend/latest/meta.json`

Timestamp format should be stable and sortable, for example:

- `2026-04-15T18-30-00Z`

## Flattened Artifact Format

Each flattened backend snapshot should be a single text document ordered by file path.

For each included file, write:

1. the relative path
2. a divider
3. the file contents

Example shape:

```text
===== FILE: apps/api/main.py =====
<contents>

===== FILE: apps/api/app/store.py =====
<contents>
```

This format is simple, diffable, and easy for both humans and automated reviewers to consume.

## Review Report Shape

Each `review.md` should contain:

- run timestamp
- review scope
- excluded paths
- changed files since the previous Ralph run
- findings ordered by severity
- a section for recurring findings
- a section for resolved findings
- a short status summary

Severity should use a stable scale:

- `high`
- `medium`
- `low`

## Metadata Contract

Each `meta.json` should include:

- `run_id`
- `started_at`
- `completed_at`
- `interval_minutes`
- `included_files`
- `excluded_patterns`
- `changed_files`
- `finding_counts`
- `status`

The metadata file is the machine-readable index for later dashboards or tooling.

## Loop Behavior

The runner should support:

- a default interval of 15 minutes
- an override to 20 minutes or another explicit value
- foreground mode for development
- background mode via shell invocation if the operator chooses
- a lock file so overlapping runs are skipped or refused

The loop should not rely on filesystem watches. The requested behavior is cadence-based, not
event-driven.

## Review Engine Expectations

The Ralph loop should start with a local review implementation that is deterministic and runnable in
this repo.

The first implementation may combine:

- file collection
- flattened snapshot generation
- simple structural checks
- a findings summary seeded from known backend review risks

If a richer native-agent review path is added later, it must remain behind the same output contract:

- write `review.md`
- write `meta.json`
- do not edit application code automatically

## Safety Rails

The Ralph loop must:

- be review-only
- never patch backend source files automatically
- never run destructive git commands
- never include local secrets or generated environments in flattened outputs
- tolerate dirty worktrees
- keep its own outputs separate from product code

If one Ralph cycle fails, it should write a failed run record rather than crash the whole loop
without artifacts.

## Failure Handling

Handle these categories explicitly:

- missing source paths
- unreadable files
- lock contention from another Ralph process
- partial output write failures
- review engine exceptions

Failure behavior:

- write `meta.json` with `status = "failed"`
- write a short `review.md` explaining the failure stage
- continue to the next scheduled cycle unless the operator stops the process

## Good-Enough Signal

"Perfect" is not a valid stop condition for automation. The loop should instead report progress with
a practical signal.

Recommended health signal:

- no high-severity findings
- no new medium-severity findings
- the same medium findings not repeating indefinitely without acknowledgement

This signal is informative only. The review loop keeps running until the operator stops it.

## Testing Strategy

The first implementation should be covered by focused tests for:

- backend file inclusion and exclusion
- flattened output ordering and formatting
- timestamped run-folder creation
- `latest/` refresh behavior
- lock-file handling
- metadata generation
- failure-path artifact writing

If test scaffolding is not yet present for the script runtime, the minimum acceptable validation is:

- a documented startup command
- one manual Ralph run that produces all three artifacts
- one repeated run that creates a second timestamped folder and refreshes `latest/`

## Startup Path

The repo should expose a clear local command such as:

```bash
scripts/ralph-backend-loop.sh
```

Possible flags:

- `--interval-minutes 15`
- `--once`
- `--foreground`

The startup path should be documented near the script so a teammate can run it without reverse
engineering the implementation.

## Stage Fit

This work belongs to the current Stage 1 extension because it improves the backend development loop
and repository understanding without introducing later-stage product behavior.

It does not collapse service boundaries or change the semantic mapping feature scope. It is an
operational support layer for the current backend slice.

## Implementation Boundary

After this spec is approved, implementation should stay small:

- one backend snapshot generator
- one report writer
- one looping runner
- minimal documentation

Do not add a dashboard, a database, or an autofix engine as part of the first Ralph loop slice.
