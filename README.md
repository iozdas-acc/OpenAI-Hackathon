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

## Ralph Backend Review Loop

Run the backend Ralph loop in the foreground:

```bash
scripts/ralph-backend-loop.sh --interval-minutes 15
```

Run a single review cycle:

```bash
scripts/ralph-backend-loop.sh --once
```

Start it in the background:

```bash
scripts/ralph-backend-loop.sh --background --interval-minutes 15
```

Artifacts are written under `reports/ralph-backend/`.

## Skills

Repo-managed skills live under `skills/`.

To install them into local Codex:

```bash
scripts/sync-codex-skills.sh
```

Restart Codex after syncing new skills.
