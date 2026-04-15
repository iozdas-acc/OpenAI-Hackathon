# Oracle to Supabase Semantic Mapping Design

## Date

2026-04-15

## Goal

Build the first real backend slice for live database exploration and semantic mapping from an Oracle source database onto a Supabase/Postgres target database.

The system must:

- connect to both databases
- crawl structure and representative data
- build a deterministic evidence graph
- use Codex to reason semantically over that graph
- pause for human review at multiple checkpoints
- allow migration to Supabase only after explicit human approval

## Why This Slice

The hackathon story is not generic ETL. The product value is that enterprise databases often drift away from clear business meaning. Column names become cryptic, enums lose documentation, implicit joins replace foreign keys, and the same business concept appears under different labels across systems.

This slice proves the core claim:

- the backend can inspect real enterprise systems
- Codex can reason over what the data likely means
- humans remain in control at every important decision point
- migration is operator-triggered, not automatic

## Scope

In scope:

- live Oracle source connection
- live Supabase/Postgres target connection
- structural crawl of both databases
- sampled data profiling for semantic evidence
- deterministic context graph construction
- Codex semantic reasoning over the context graph
- proposed Oracle-to-Supabase mappings
- explicit human review checkpoints
- explicit human-triggered migration action

Out of scope for this slice:

- full production-grade migration planner
- continuous sync or CDC
- automatic schema evolution management
- production auth and RBAC
- high-scale distributed execution
- advanced UI design beyond what is necessary to review states and actions

## Problem Statement

The product is solving the gap between technical structure and business meaning.

Examples the system must handle:

- badly named fields such as `cust_cls`, `x12`, `desc2`, `flag_a`
- same concept with different labels such as `client_id`, `customer_no`, `bp_number`
- same label with different meanings such as `status`, `type`, `code`
- coded enums such as `A`, `B2`, `03`, `999`
- poor-quality and inconsistent values
- hidden joins with no declared foreign keys
- local jargon and legacy abbreviations
- denormalized text with embedded business meaning

The system should answer not just "what is this column called?" but "what business concept does this data represent?"

## Approaches Considered

### 1. LLM-first graph generation

Codex directly inspects raw metadata and generates the graph.

Pros:

- fastest prototype path

Cons:

- weakest auditability
- harder to debug
- less stable for repeated runs
- poor foundation for human review

### 2. Deterministic graph first, Codex reasons second

The backend crawls both databases, builds an evidence graph from facts, and then Codex reasons over that graph.

Pros:

- strong audit trail
- replayable and debuggable
- clear human review surfaces
- safer foundation for migration

Cons:

- more backend work up front

### 3. Full LangGraph-first orchestration from day one

Everything is built as a complete staged workflow with full orchestration before proving the vertical slice.

Pros:

- clean long-term architecture

Cons:

- too much critical-path complexity for the first build

## Recommended Approach

Use approach 2.

The system should be fact-first and reasoning-second:

1. crawl both databases
2. build a deterministic evidence graph
3. run Codex semantic reasoning over that graph
4. collect human approvals
5. allow migration only after approval

LangGraph should orchestrate the stages, but it should not be responsible for inventing the graph itself.

## Core Architecture

### apps/api

Owns:

- API endpoints
- run creation
- event streaming
- review actions
- migration trigger

### services/orchestrator

Owns:

- orchestration entrypoint
- LangGraph workflow
- transitions between crawl, graph, reasoning, review, and migration stages
- Codex calls for semantic reasoning and mapping proposals

### services/context-graph

Owns:

- deterministic context graph construction
- graph snapshot persistence
- graph versioning for each stage

### services/crawlers

Owns:

- Oracle metadata and sample-data crawl
- Supabase/Postgres metadata and sample-data crawl

### services/migration

Owns:

- migration execution into Supabase after approval
- guardrails, idempotency checks, and run-state validation

## LangGraph Position

LangGraph is the workflow engine, not the graph builder.

LangGraph should manage:

- stage transitions
- retries
- pause/resume at human checkpoints
- approval gating
- migration precondition checks

The graph itself must be built by backend code from database evidence.

## End-to-End Workflow

### Stage A: Connect and crawl

The system connects to:

- Oracle source
- Supabase/Postgres target

For each database it gathers:

- schemas
- tables
- columns
- data types
- primary keys
- foreign keys
- indexes
- constraints
- row counts where practical
- null rates
- low-cardinality fields
- sample values
- representative sample rows
- likely join clues when explicit keys are missing

### Human review checkpoint 1

After crawling both databases and building the initial structural map, the system pauses.

Operators review:

- what the Oracle database contains
- what the Supabase target contains
- structural overlaps and gaps
- inferred relationships and possible crawl issues

No semantic reasoning proceeds until this checkpoint is approved.

### Stage B: Deterministic context graph build

The backend constructs an evidence graph from the crawl results.

Example node types:

- database
- schema
- table
- column
- key
- constraint
- enum_candidate
- value_pattern
- entity_hypothesis
- mapping_candidate

Example edge types:

- contains
- belongs_to
- references
- joins_with
- looks_like_enum
- co_occurs_with
- may_represent
- maps_to_candidate

The deterministic graph should prefer stable identifiers and versioned snapshots so later reasoning can reference exact evidence.

### Stage C: Codex semantic reasoning

Codex consumes the deterministic graph and structured evidence, then produces:

- likely business meaning of tables and columns
- likely meaning of coded fields and enums
- disambiguation of generic labels like `status` and `type`
- hidden relationship hypotheses
- candidate same-concept matches across Oracle and Supabase
- confidence scores
- review questions for humans

Codex should not overwrite structural evidence. It should add semantic annotations and hypotheses on top of it.

### Human review checkpoint 2

After Codex has reasoned over the context graph, the system pauses again.

Operators review:

- semantic interpretations
- confidence levels
- ambiguous fields
- questionable relationships
- follow-up questions the system generated

This checkpoint is specifically for validating the reasoning layer before mappings are proposed as actionable.

### Stage D: Mapping proposal

The system proposes Oracle-to-Supabase mappings using both structural evidence and Codex semantic reasoning.

Each mapping proposal should include:

- source object
- target object
- mapping type
- confidence
- supporting evidence
- unresolved questions
- human decision status

### Human review checkpoint 3

Operators review candidate mappings and explicitly:

- approve
- reject
- defer
- request clarification

Only approved mappings may become migration inputs.

### Stage E: Explicit migration trigger

After required approvals are complete, the system exposes an explicit migrate action.

Migration must:

- require a human button press
- verify approval preconditions
- log the exact approved mapping set
- emit migration events
- write into Supabase only after preflight validation

## Human-in-the-Loop Rules

Human review is not a single final approval. It is part of the workflow state machine.

Required checkpoints:

1. after structural crawl and database mapping
2. after Codex semantic reasoning
3. after candidate mappings are proposed
4. before migration execution begins

The system must never auto-advance across these gates without explicit approval.

## API Direction

The existing run model should expand rather than be replaced.

Likely additions:

- `POST /projects/{project_id}/connections`
  - stores source and target connection configuration references
- `POST /projects/{project_id}/runs`
  - starts the staged semantic mapping run
- `POST /runs/{run_id}/reviews/crawl`
  - approve or reject checkpoint 1
- `POST /runs/{run_id}/reviews/reasoning`
  - approve or reject checkpoint 2
- `POST /runs/{run_id}/reviews/mappings`
  - approve or reject checkpoint 3
- `POST /runs/{run_id}/migrate`
  - explicit migration trigger after all approvals

The final endpoint names may change, but the contract shape should preserve explicit review actions.

## Run States and Events

The current `pending/running/completed/failed` model is too coarse.

Additional run states should be introduced for review gating, such as:

- `awaiting_crawl_review`
- `awaiting_reasoning_review`
- `awaiting_mapping_review`
- `migration_ready`
- `migrating`
- `migration_completed`

Event types should expand to include:

- `source_crawl_started`
- `source_crawl_completed`
- `target_crawl_started`
- `target_crawl_completed`
- `context_graph_built`
- `crawl_review_required`
- `semantic_reasoning_started`
- `semantic_reasoning_completed`
- `reasoning_review_required`
- `mappings_proposed`
- `mapping_review_required`
- `migration_ready`
- `migration_triggered`
- `migration_completed`

## Graph Contract Direction

The graph must support both structural evidence and semantic annotations.

Structural layer:

- database and schema hierarchy
- table and column layout
- keys and declared relationships
- sample statistics and value evidence

Semantic layer:

- inferred business entities
- concept hypotheses
- same-as candidates
- role distinctions
- confidence and ambiguity metadata

The graph should support versioned snapshots:

- post-crawl snapshot
- post-reasoning snapshot
- post-mapping snapshot

## Codex Prompting Direction

Codex should receive structured evidence, not raw unbounded dumps.

Prompt inputs should include:

- normalized crawl summary
- graph nodes and edges relevant to the current task
- representative sample values
- ambiguous fields requiring interpretation
- target-schema context for cross-database matching

Codex outputs should remain structured and machine-validated.

## Migration Constraints

Migration is allowed in this slice only as an explicitly triggered action after approval.

The initial migration path should be conservative:

- approved mappings only
- strong audit log
- preflight validation before writes
- idempotent run guard where practical
- visible failure states

The system is not attempting to solve full enterprise migration planning in this slice.

## Risks

### Driver and connection risk

Oracle and Supabase access introduce dependency, credential, and environment complexity.

### Graph drift risk

If deterministic graph identifiers and Codex semantic annotations do not align, the system will produce unstable or duplicated graph state.

### Human gate complexity

Multiple review checkpoints require careful pause/resume behavior and strict approval validation.

### Migration safety risk

The migrate action must never run on unapproved or partially approved mappings.

## Implementation Phasing

### Phase 1

- add connection contracts
- implement Oracle crawl
- implement Supabase crawl
- persist crawl evidence

### Phase 2

- build deterministic context graph
- emit graph snapshots and events
- add checkpoint 1

### Phase 3

- add Codex semantic reasoning over graph evidence
- persist semantic annotations
- add checkpoint 2

### Phase 4

- generate Oracle-to-Supabase mapping proposals
- add checkpoint 3

### Phase 5

- add explicit migration trigger
- enforce approval preconditions
- write migration audit trail

## Recommendation

Build one convincing backend vertical slice:

- Oracle source
- Supabase target
- deterministic evidence graph
- Codex semantic reasoning
- human approvals at every major gate
- explicit migrate action only after approval

This is the smallest architecture that still honestly demonstrates semantic migration intelligence rather than generic schema inspection.
