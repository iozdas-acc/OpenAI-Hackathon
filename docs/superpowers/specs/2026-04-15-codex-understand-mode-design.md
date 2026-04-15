# Codex Understand Mode Backend Design

## Date

2026-04-15

## Goal

Ship the first real Codex-native backend slice for the semantic translation platform.

This slice establishes the "control room" backend contract for one workflow mode: `Understand`.
Codex is the reasoning engine. The backend accepts uploaded project files, starts a Codex-backed
run, streams activity to the UI, and persists a lightweight context graph snapshot that can later
drive richer graph workflows and 3D visualizations.

## Why This Slice

The repo has completed Stage 0 scaffolding. The next milestone should not be another shell. It
should be one convincing vertical slice that proves:

- the product is genuinely Codex-native
- the UI can trigger a real backend run
- activity can be streamed as visible work
- semantic understanding can accumulate as graph state
- follow-up questions for employees can be generated from the run

This design intentionally limits scope to one mode so the team can ship a usable backend within the
next few hours.

## Scope

In scope:

- one project lifecycle with local persistence
- file attachment to a project
- one run mode: `understand`
- Codex-backed execution via the OpenAI Responses API
- streamed run events over SSE
- typed structured output for Understand Mode
- lightweight graph persistence using node and edge snapshots
- follow-up question generation for human-in-the-loop clarification

Out of scope for this slice:

- additional modes (`map`, `validate`, `simulate`)
- frontend 3D graph rendering
- production authentication and multi-tenant access control
- durable Postgres storage
- full LangGraph-first orchestration in the critical path
- migration planning or downstream transform execution

## Product Narrative

The target use case is post-acquisition system migration. A new parent company acquires another
company and needs to migrate or consolidate databases, but the two sides use different business
terms, structures, and ontologies. The first product capability is to inspect uploaded schema and
dataset context, infer semantic meaning, construct a provisional context graph, and surface the
questions that employees need to answer to disambiguate the mapping.

## Core Decision

Use Codex as the only execution and reasoning engine now. LangGraph remains the orchestration
direction, but not a demo-time requirement if it introduces boot or integration risk.

This yields the clean product statement:

- Codex powers the run.
- The backend builds a context graph as understanding grows.
- LangGraph is the orchestration backbone the system is growing into, but it is not allowed to
  block the first convincing demo slice.

## Recommended Approach

Adopt a Codex-first architecture with a thin orchestration boundary:

1. The API creates a run and stores project inputs.
2. The orchestrator invokes Codex with mode-specific instructions.
3. The orchestrator converts Codex output into:
   - a structured Understand result
   - typed activity events for the UI
   - graph nodes and edges for persistence
4. The context graph service stores the latest graph snapshot and event-derived mutations.

This keeps the backend honest to the Codex-native requirement without prematurely multiplying
systems.

## System Boundaries

### apps/api

Owns:

- HTTP endpoints
- file uploads
- project and run history
- SSE event streaming
- in-process background run scheduling for the first slice

### services/orchestrator

Owns:

- Understand Mode workflow execution
- Codex API calls
- transformation of model output into domain events
- normalization of structured result payloads

### services/context-graph

Owns:

- graph snapshot persistence
- append-only node and edge mutation records
- graph queries for a project or run

For this slice the implementation can be lightweight and local. A future iteration can move the
workflow state machine behind LangGraph without changing the frontend contract.

### packages/shared-types

Owns cross-service contracts:

- project and run identifiers
- run status enum
- event envelope schema
- graph node and edge schema
- Understand Mode result schema

## First API Contract

### POST /projects

Creates a project and returns project metadata.

### POST /projects/{project_id}/files

Attaches an uploaded file to the project and returns file metadata.

### POST /projects/{project_id}/runs

Creates a run for `mode = "understand"` and starts background execution.

Request body includes:

- `mode`
- `instructions`
- optional user notes

### GET /projects/{project_id}/runs

Returns run history for the project.

### GET /runs/{run_id}

Returns run metadata, status, and the latest structured result if available.

### GET /runs/{run_id}/events

Streams run activity via SSE.

## Event Model

The backend must emit stable, UI-facing events even if the visual treatment changes later.

Initial event types:

- `run_created`
- `file_attached`
- `codex_started`
- `reasoning_summary`
- `node_created`
- `edge_created`
- `question_raised`
- `confidence_changed`
- `run_completed`
- `run_failed`

Each event should contain:

- event id
- run id
- project id
- event type
- timestamp
- payload

This contract is intentionally suitable for:

- an activity feed
- a streamed output panel
- progress sidebars
- future 3D graph animation such as Lego-like bricks stacking as context accumulates

## Understand Mode Output

Understand Mode must be operational, not chat-only. The run returns structured JSON with these
top-level fields:

```json
{
  "entities": [],
  "fields": [],
  "inferred_meanings": [],
  "questions": [],
  "graph": {
    "nodes": [],
    "edges": []
  },
  "confidence": {
    "overall": 0,
    "by_entity": []
  },
  "summary": ""
}
```

### Semantics

- `entities`: discovered business objects or source structures
- `fields`: source fields with candidate semantic interpretation
- `inferred_meanings`: natural-language semantic descriptions tied to entities or fields
- `questions`: clarification prompts intended for employees using the platform
- `graph.nodes`: concepts, systems, entities, fields, and inferred business terms
- `graph.edges`: relationships such as "belongs_to", "maps_to_candidate", or "depends_on"
- `confidence`: coarse confidence values suitable for UI scoring and progression
- `summary`: a short run summary for human review

## LangGraph Position

LangGraph is the desired long-term orchestration backbone, but it should be added behind an
internal workflow interface rather than forced into the initial demo path.

The first implementation should expose an interface such as:

- `run_understand_workflow(...)`

The initial implementation may be direct Python orchestration. A later implementation can route the
same interface through LangGraph state nodes and transitions.

This keeps the architecture aligned with repo direction while controlling demo risk.

## Persistence Strategy

Use a simple local file-backed store for the first slice. Persist:

- project metadata
- file metadata and file paths
- run metadata
- append-only events
- final Understand result
- latest graph snapshot

This keeps the API runnable immediately and gives the UI stable history without requiring Postgres
setup during the first live integration.

## Error Handling

Handle and surface these categories:

- invalid upload or unsupported file input
- missing OpenAI API credentials
- Codex execution failure
- malformed model output
- event stream interruption

Rules:

- failed runs must still persist terminal status and a `run_failed` event
- parsing failures should preserve raw model text for inspection when safe
- the API should return explicit operator-facing messages instead of silent failures

## Testing and Verification

Minimum acceptance for this slice:

- API starts locally
- a project can be created
- a file can be attached
- an Understand run can be created
- the run emits streamed events
- the run finishes with persisted structured output
- run history can be fetched by project

If a real Codex call cannot be made in the local environment, the code should still fail clearly and
preserve the intended contract so the team can finish integration quickly once credentials are in
place.

## Immediate Implementation Plan

1. Add shared Python models for projects, runs, events, graph nodes, graph edges, and Understand
   results.
2. Implement a lightweight local repository for projects, uploads, runs, results, and event logs.
3. Add API endpoints for projects, files, runs, run retrieval, run history, and SSE streaming.
4. Implement the orchestrator service for Understand Mode with Codex-backed execution.
5. Normalize Codex output into structured results and graph events.
6. Verify the API boots and the control-room UI can consume the event stream.

## Deferred Follow-Ups

- Add `map`, `validate`, and `simulate` modes behind the same run contract
- Swap local persistence for Postgres
- Move orchestration internals onto LangGraph
- Add graph comparison and run comparison
- Drive gamification from structured confidence and issue outputs
- Feed graph events into a live 3D visualization layer
