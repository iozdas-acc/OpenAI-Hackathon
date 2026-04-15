# PLANS.md

## Current milestone

Stage 1: Oracle-to-Supabase semantic mapping golden path

## Planning mode

Detailed feature planning is intentionally deferred until hackathon day.

Until then:

- keep the repo ready for rapid execution
- avoid locking in feature scope too early
- favor scaffolding, context, and reusable setup over speculative implementation

Hackathon-day runbook:

- `docs/hackathon-runbook.md`

## Tasks

- [x] Complete Stage 0 repo and service scaffolding
- [x] Write Codex Understand Mode backend design spec
- [x] Add shared run, event, graph, and result contracts
- [x] Add local persistence for projects, files, runs, events, and graph snapshots
- [x] Add API endpoints for projects, uploads, runs, run history, and SSE events
- [x] Implement Codex-backed Understand Mode orchestration
- [x] Persist structured Understand outputs by project and run
- [x] Document the startup path and required environment for Codex-backed runs
- [ ] Add live source connection support for Oracle and target connection support for Supabase/Postgres
- [ ] Crawl database metadata, schemas, tables, columns, constraints, and join clues
- [ ] Profile sampled data for null patterns, value distributions, enum-like fields, and representative examples
- [ ] Add human review checkpoint after both databases are crawled and initially mapped
- [ ] Build a deterministic context graph from database evidence
- [ ] Add Codex semantic reasoning over graph nodes and edges to infer business meaning
- [ ] Add human review checkpoint after Codex reasons over the context graph
- [ ] Propose semantic matches from the Oracle source model onto the Supabase target model
- [ ] Add human review checkpoint for candidate mappings before any migration action
- [ ] Persist approved semantic mappings for later migration planning
- [ ] Add a final operator-controlled migrate action that runs only after mapping approval

## Exit criteria

- API starts locally
- Project creation works
- File upload works
- Understand runs can be created
- Run events stream to the client
- Structured Understand output persists by run
- Run history can be queried by project
- Oracle source and Supabase target databases can be explored through a backend connection contract
- A run can produce a context graph with nodes and edges derived from real database evidence
- Operators can review the crawled structure of both databases before semantic reasoning proceeds
- Codex can explain what tables, columns, codes, and relationships likely mean in business terms
- Operators can review and acknowledge Codex reasoning over the context graph before mapping proceeds
- The system can propose semantic matches from Oracle structures onto Supabase structures with confidence and supporting evidence
- A human can review and approve or reject candidate mappings
- Migration to Supabase can only be triggered by an explicit human action after mapping approval

## Product direction for this milestone

Build a backend that can connect to a live Oracle source database and a Supabase/Postgres target database, crawl their structure and representative data, and turn that evidence into a context graph. LangGraph is the orchestration backbone for the workflow, but it does not create the graph automatically; the backend must build the graph and then use Codex to reason semantically over the nodes and edges.

The graph should capture database structure and evidence first, then semantic hypotheses second. That means deterministic graph construction from schemas, tables, columns, keys, sample values, and inferred relationships, followed by Codex-generated interpretations such as likely business entities, enum meanings, overloaded fields, hidden joins, and same-concept candidates across systems.

Human review is required at multiple checkpoints. First, operators inspect the crawled Oracle source and Supabase target structures after the system maps what each database appears to contain. Second, operators review the context graph after Codex has reasoned over the nodes and edges and added semantic interpretations. Third, operators review candidate Oracle-to-Supabase mappings and explicitly approve or reject them. Only after those approvals should the system expose a button to migrate into Supabase.

## Judging checklist

Use this rubric to evaluate ideas and demo choices on hackathon day:

- `25%` Depth of Codex integration
  Refine as: evaluate how central Codex is to the solution and how meaningfully it is used across the build and runtime workflow.
  Strong entries show Codex as a core driver of development, including generating, iterating, debugging, and improving code through agentic workflows, not just as an assistive tool.
- `25%` Real-world partner impact
  Refine as: evaluate how directly the project addresses a meaningful internal partner problem or customer-facing opportunity.
  Strong entries solve clear, practical challenges in delivery, engineering, implementation, or go-to-market contexts, with a well-defined user and a credible real-world application.
- `25%` Reusability and adoption potential
  Refine as: evaluate the long-term value of the project beyond the hackathon.
  Strong entries demonstrate clear potential to be reused, scaled, or productized as a partner accelerator, internal tool, customer offering, or Codex-embedded aid to a repeatable workflow or delivery motion.
- `25%` Demo and pitch quality
  Refine as: evaluate how clearly and effectively the team communicates the solution and its value.
  Strong entries present a compelling end-to-end narrative covering the problem, what was built, why it matters, and how Codex was used throughout the process.

For the final demo, show both the outcome and the workflow:

- what we built
- why it matters
- where Codex accelerated or transformed the build

## Delivery constraints

- total hackathon time is `4h`
- team size is `3` people
- submission includes a `1 min` recorded video, for example via Loom
- the video should explain what was built and why
- judging includes `3 mins` of live demo plus `1-2 mins` of Q&A
- live demo quality is critical to scoring
- the live demo must be a working product flow, not a slide deck, PDF, or HTML-only explanation

## Next milestone

Stage 2: UI for live context graph updates and operator-facing review workflows

## Deferred

- Migration planning stub after approved mappings
