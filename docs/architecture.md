# Architecture

## Product direction

Build an enterprise dashboard with gamified elements for human-in-the-loop semantic translation.

The system should:

- ingest source schema information
- propose business ontology mappings
- ask targeted clarifying questions
- update a live context graph
- expose visible progress and confidence changes in the UI

## Stage 0 scope

Only scaffold the system.

Required shells:

- Next.js frontend
- FastAPI API
- LangGraph orchestrator
- context graph service shell
- shared packages and docs

## Planned architecture

### `apps/web`

Enterprise dashboard UI with gamified feedback, graph views, mapping review, and session state visualization.

### `apps/api`

FastAPI service for frontend-facing endpoints and event streaming.

### `services/orchestrator`

LangGraph runtime that will eventually coordinate schema profiling, semantic extraction, mapping, clarification, and graph updates.

### `services/context-graph`

Persistence-oriented service shell for graph writes and graph reads.

### `packages/shared-types`

Cross-service contracts.

### `packages/ontology-core`

Ontology models, enums, and validators.

## Data direction

Primary persistence target is Postgres. `pgvector` is a likely later addition for semantic retrieval.
