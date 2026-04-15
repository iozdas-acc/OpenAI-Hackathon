# Ralph Backend Review

Run ID: `2026-04-15T13-14-54Z`
Started: `2026-04-15T13:14:54Z`
Completed: `2026-04-15T13:14:54Z`
Interval Minutes: `15`
Status: `needs_attention`

## Scope

- Included files: 19
- Excluded patterns: .data, .git, .next, .venv, __pycache__, node_modules

## Changed Files

- No file content changes since the previous Ralph run.

## Findings

### High

- `apps/api/app/store.py`: **Run listing uses a live dict view outside the store lock**. Iterating a dict values view after releasing the lock can raise runtime errors or return inconsistent results when concurrent writes occur.
- `apps/api/main.py`: **Migration failures can leave runs stuck in migrating**. The API transitions a run to migrating before verifying the executor import and before guarding the migration call, so failures can strand the run without a terminal status.
- `services/crawlers/supabase.py`: **Target crawl exports raw sample rows**. Sample rows are copied verbatim into crawl output, which creates a direct path for PII and secret leakage into downstream persistence and review artifacts.
- `services/migration/supabase.py`: **Migration metrics assume graph nodes are objects instead of dicts**. When graph nodes are stored as dictionaries, the current mapping count logic reports zero candidates and makes migration telemetry misleading.
- `services/orchestrator/workflow.py`: **Orchestrator response parsing assumes a narrow OpenAI payload shape**. The parser only checks a small set of response fields, so supported API variations or wrapped structured output can fail without a durable fallback path.
- `services/orchestrator/workflow.py`: **Structured output parsing does not preserve context on JSON decode failures**. Malformed or wrapped model output will bubble up as a raw JSON decode failure, which makes recurring contract issues harder to diagnose.

### Medium

- `apps/api services/orchestrator services/crawlers services/migration`: **Backend review targets are missing automated tests**. No backend-focused test modules were found under the reviewed surfaces, so the Ralph loop can report recurring issues but cannot validate regressions automatically.
- `apps/api/app/store.py`: **Run status transitions wipe started_at for non-running states**. Completed and failed runs lose their original start timestamp, which breaks duration tracking and weakens backend auditability.
- `apps/api/app/store.py`: **Uploaded filenames are written into storage paths without sanitization**. A crafted filename can escape the intended upload area or create unstable local file paths because the store concatenates the raw filename into the saved path.
- `services/crawlers/oracle.py`: **Oracle preview logic trusts arbitrary file metadata paths**. The crawler reads the first line of whatever path is present in file metadata without confining that path to the upload area.

## Recurring Findings

- `brittle-openai-parser`
- `live-dict-values-view`
- `mapping-count-dict-bug`
- `migration-stuck-status`
- `missing-backend-tests`
- `oracle-arbitrary-path-read`
- `sample-row-leak`
- `started-at-reset`
- `unsafe-json-loads`
- `unsanitized-upload-filename`

## Resolved Findings

- None.

## New Findings

- None.
