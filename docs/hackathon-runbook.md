# Hackathon Runbook

## North Star

Build a high-fidelity prototype for migration intelligence and human-guided readiness, not a real migration engine.

## Demo Promise

A tech implementation partner uploads legacy migration input, Codex analyzes it, proposes mappings, a human resolves ambiguity, and the system shows migration readiness plus a believable simulation preview.

## Success Criteria

- One golden path works end to end.
- At least one Codex step is clearly real on-screen.
- At least one HITL mapping decision is clearly real on-screen.
- The demo fits comfortably inside 1 minute.
- The live flow is deterministic and fast.

## Feature Cut Line

### Must-have

- Upload legacy CSV or schema
- `Analyze with Codex`
- Structured analysis results
- `Generate mappings`
- One human review/edit/approve interaction
- `Validate`
- Readiness/issues/confidence view
- `Simulate`
- Before/after preview

### Nice-to-have

- activity feed
- agent labels
- migration score
- stronger control-room styling

### Do Not Build Unless Everything Above Is Done

- real migration load
- real orchestration layer
- real validation engine
- multi-agent backend
- dynamic target schema selection

## Team Split

### Bing: product lead + frontend owner

- Lock final user story and exact demo script
- Own product scope and feature cut decisions
- Build upload screen
- Build action bar: `Analyze`, `Generate mappings`, `Validate`, `Simulate`
- Build results panels
- Build mapping review table with ambiguity/confidence badges
- Build readiness/progress panel
- Build simulation preview panel
- Build optional activity feed if time remains
- Own the 1-minute video and 3-minute live demo script

### Izzie: prompts + integration owner

- Define response contracts for `/analyze` and `/map`
- Write prompts for schema understanding and mapping generation
- Prepare fallback stub JSON if API breaks
- Own the final integration decision-making

### Eldhose: backend owner

- Build `POST /analyze`
- Optionally build `POST /map`
- Connect to OpenAI Responses API
- Return structured JSON
- Add logging and fallback mode
- Keep payloads simple and stable for the frontend

## 4-Hour Schedule

### 0:00-0:20 Scope Lock

- Agree on one input format: CSV
- Agree on one hardcoded target schema
- Agree that `Analyze` must be real
- Decide if `Map` is real or semi-real
- Freeze the demo script early

### 0:20-0:45 Contract And Seed Setup

- Define sample CSV
- Define target schema
- Define 2 ambiguous fields for HITL
- Define JSON shapes
- Prepare stub responses

### 0:45-2:00 Parallel Build

- UI shell
- `/analyze`
- prompt + output contract
- seed mapping and validation data

### 2:00-2:45 Critical Integration

- Upload -> analyze -> render
- Make this stable before anything else

### 2:45-3:20 Add Review And Polish Flow

- mapping suggestions
- human approval/edit step
- validation panel
- simulate preview
- readiness score

### 3:20-3:40 Demo Hardening

- remove lag
- seed deterministic outputs
- improve text labels
- rehearse once

### 3:40-3:50 Record 1-Minute Video

- short, high-energy walkthrough

### 3:50-4:00 Live Demo Rehearsal

- practice 3-minute version
- prep Q&A answers

## Golden Path User Journey

1. User uploads legacy CSV.
2. User clicks `Analyze with Codex`.
3. System shows structured schema understanding.
4. User clicks `Generate mappings`.
5. System shows proposed mappings and flags ambiguity.
6. User reviews one ambiguous mapping and approves or edits it.
7. User clicks `Validate`.
8. System shows issues resolved/unresolved plus readiness.
9. User clicks `Simulate`.
10. System shows before/after preview and migration package ready state.

## UI Sections

### 1. Upload Panel

- CSV dropzone
- sample file shortcut
- schema summary after upload

### 2. Action Bar

- `Analyze with Codex`
- `Generate mappings`
- `Validate`
- `Simulate`

### 3. Analysis Panel

- detected entities/tables
- inferred field types
- key fields
- data quality notes
- legacy quirks/risk flags

### 4. Mapping Review Panel

- source field
- proposed target field
- confidence
- rationale
- status: `auto-approved` / `needs review`
- actions: `Approve`, `Edit`, `Reject`

### 5. Validation Panel

- unresolved mappings
- type mismatches
- required fields missing
- transformation warnings
- readiness status

### 6. Simulation Panel

- before/after sample rows
- highlighted transformed fields
- ready-for-migration style summary

### 7. Progress/Status Panel

- ingestion complete
- analysis complete
- mappings proposed
- human review complete
- validation passed
- simulation ready

## Minimal API Contracts

### POST `/analyze`

Request:

```json
{
  "filename": "customer_export.csv",
  "columns": ["cust_id", "cust_name", "addr_1", "postcode", "segment_cd"],
  "sample_rows": [
    {
      "cust_id": "C001",
      "cust_name": "Acme Ltd",
      "addr_1": "1 King St",
      "postcode": "SW1A 1AA",
      "segment_cd": "ENT"
    }
  ],
  "target_schema": {
    "table": "customers",
    "fields": [
      "customer_id",
      "name",
      "address_line_1",
      "postal_code",
      "segment"
    ]
  }
}
```

Response:

```json
{
  "source_summary": {
    "dataset_name": "customer_export",
    "likely_domain": "customer master",
    "detected_entities": ["customer"],
    "notes": [
      "Legacy abbreviations detected",
      "Address fields appear partially normalized"
    ]
  },
  "fields": [
    {
      "source_field": "cust_id",
      "inferred_type": "string",
      "description": "Legacy customer identifier",
      "quality_flags": []
    },
    {
      "source_field": "segment_cd",
      "inferred_type": "string",
      "description": "Segment code",
      "quality_flags": ["requires business lookup"]
    }
  ],
  "risks": [
    "Abbreviated field names may require human review",
    "Code values may need translation before migration"
  ]
}
```

### POST `/map`

Request:

```json
{
  "analysis": {},
  "target_schema": {
    "table": "customers",
    "fields": [
      "customer_id",
      "name",
      "address_line_1",
      "postal_code",
      "segment"
    ]
  }
}
```

Response:

```json
{
  "mappings": [
    {
      "source_field": "cust_id",
      "target_field": "customer_id",
      "confidence": 0.98,
      "rationale": "Identifier naming aligns strongly",
      "status": "auto-approved"
    },
    {
      "source_field": "segment_cd",
      "target_field": "segment",
      "confidence": 0.62,
      "rationale": "Looks like a code field but requires business confirmation",
      "status": "needs-review"
    }
  ]
}
```

## Validation Can Be Frontend-Driven

Use simple rule logic:

- required target fields mapped?
- any low-confidence mappings?
- any code fields unresolved?
- any inferred type mismatch?

## Simulation Can Be Mocked

Just transform 2-3 sample rows into believable target rows.

## Prompt Guidance

### Analyze Prompt Goal

Turn raw CSV headers and samples into:

- dataset purpose
- inferred field meanings
- inferred types
- likely migration risks
- structured JSON only

### Map Prompt Goal

Turn source understanding into:

- proposed target mappings
- confidence
- rationale
- review flags for ambiguous fields

## Fallback Strategy

If live API is slow or fails:

- keep a toggle for stub mode
- use pre-seeded JSON for the sample file
- make the UI identical either way

That protects demo quality.

## Live Demo Script: 3 Minutes

- Migration teams lose time early by interpreting messy legacy data and resolving ambiguous mappings.
- This prototype shows how Codex and automation can accelerate that work while keeping humans in control.
- Upload sample CSV.
- Click `Analyze with Codex`.
- Show structured understanding and risk flags.
- Click `Generate mappings`.
- Show confident mappings plus 1 ambiguous field.
- Human approves or edits the ambiguous one.
- Click `Validate`.
- Show readiness and remaining issues reduced.
- Click `Simulate`.
- Show before/after preview and ready-state.

## 1-Minute Video Script

- We built a migration copilot for implementation teams handling legacy data migration.
- A user uploads a legacy CSV, and Codex analyzes the schema and identifies migration risks.
- The system proposes target mappings and flags ambiguous fields for human review.
- After one quick approval step, the workflow validates the migration package and simulates the transformed result.
- This shows how agents and automation can accelerate migration discovery, mapping, and readiness without spending time on a full migration run.

## Q&A Prep

### Why not run a real migration?

- Because the highest-value early migration bottleneck is understanding and mapping legacy data correctly. We focused the prototype there.

### What is real vs mocked?

- Codex-powered analysis is real, and the human review workflow is real. Validation and simulation are prototype-level to keep the demo fast and focused.

### Why is this useful?

- It reduces manual discovery and mapping effort for implementation teams and creates reusable migration readiness workflows.

## Hard Rules During The Build

- Do not add extra agents unless they create visible demo value.
- Do not wait for the backend before building the UI.
- Do not chase polish before the golden path works.
- Do not let any step take more than a few seconds in the demo.
