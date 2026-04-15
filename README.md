# OpenAI Hackathon

Accenture team submission scaffold for the OpenAI Hackathon.

Stage 0 scaffold for a human-in-the-loop semantic translation platform built for the OpenAI hackathon.

## Planned stack

- `apps/web`: Next.js frontend for the enterprise dashboard with gamified elements
- `apps/api`: FastAPI service for API endpoints and event streaming
- `services/orchestrator`: LangGraph runtime shell
- `services/context-graph`: graph persistence shell
- `packages/shared-types`: shared contracts
- `packages/ontology-core`: ontology definitions and validators
- `skills/`: repo-managed Codex skill base

## Current scope

Scaffolding only. No product features should be implemented in this stage.

## Reference docs

- `docs/acquisition-schema-comparison.md`: first-pass acquisition demo schema comparison for semantic mapping design
- `docs/sql/furnifuture.sql`: Company A Postgres schema draft
- `docs/sql/pinewoodworks.sql`: Company B Postgres schema draft

## Local bootstrap

Fresh clone setup:

```bash
scripts/bootstrap.sh
```

Frontend shell:

```bash
cd apps/web
npm run dev
```

API shell:

```bash
scripts/dev-api.sh
```

Orchestrator shell:

```bash
scripts/dev-orchestrator.sh
```

Context graph shell:

```bash
scripts/dev-context-graph.sh
```

Postgres:

```bash
docker compose up -d postgres
```

## Skills

Repo-managed skills live under `skills/`.

To install them into local Codex:

```bash
scripts/sync-codex-skills.sh
```

Restart Codex after syncing new skills.

## Codex timeline

To track major Codex milestones into one local JSON timeline:

```bash
scripts/install-timeline-hooks.sh
scripts/timeline-session-start.sh --goal "Describe the task you are working on"
```

Log milestone summaries during the session:

```bash
scripts/timeline-log.sh --type planning --summary "Selected the implementation approach"
scripts/timeline-log.sh --type file_edit --summary "Updated Docker and MCP scaffold" --files Dockerfile docker-compose.yml
```

End the session when the task is done:

```bash
scripts/timeline-session-end.sh --summary "Finished the task and verified the changes"
```

The timeline is written locally to `.codex/timeline.json`. Commit milestones are added automatically after `git commit` once hooks are installed.
