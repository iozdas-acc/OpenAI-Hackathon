# Oracle to Supabase Review Workspace Design

## Date

2026-04-15

## Goal

Ship a frontend-first demo workspace that feels real in front of the team:

- uses the provided `oracle-supabase-migration-copilot.html` as the visual base
- maps directly onto the current backend and Stage 1 plan
- preserves explicit human review checkpoints
- includes a persistent Codex side panel with demo-visible actions
- shows a compelling context graph treatment that can be upgraded later
- supports a demo script even before every backend action is fully wired

## Product Position

For now, this review workspace is the main landing experience of the product.

The UI is not a general dashboard. It is a focused operator workspace for one migration review case:

- Oracle source connected
- Supabase/Postgres target selected
- Codex has crawled, interpreted, and reduced the noisy migration estate
- the operator sees one active decision in focus
- Codex remains present as a persistent collaborator

This preserves demo clarity. The system can add a higher-level project dashboard later without changing the core review case design.

## Source of Truth

The visual and interaction baseline is the manager-provided HTML:

- `oracle-supabase-migration-copilot.html`

That HTML establishes the correct product pattern:

- compressed top context
- one active arbitration in the hero area
- evidence on the left
- queue and outcomes on the right
- deeper secondary surfaces below

The implementation should adapt this pattern into the Next.js app rather than replacing it with a generic SaaS dashboard.

## Primary Experience

The user lands in a migration review case workspace with five coordinated regions:

1. Header
2. Context and progress band
3. Hero arbitration workspace
4. Persistent Codex side panel
5. Secondary tabbed workspaces

### Header

Purpose:

- orient the viewer in one sentence
- show current milestone and readiness level
- keep Oracle source and Supabase target visible

Contents:

- title and subhead
- milestone/status card
- source/target badges
- current review case identity

### Context and Progress Band

Purpose:

- compress the migration estate into a readable summary
- show that Codex has already reduced noise into actionable work

Contents:

- migration context summary
- mini metrics
- simplified source topology card
- progress rail:
  - connect and scan
  - build evidence graph
  - Codex reasoning
  - human review
  - validate
  - package

### Hero Arbitration Workspace

Purpose:

- keep one active decision in focus
- make the human checkpoint unmistakable

Three-column structure:

- left: context and evidence
- center: active Codex recommendation and decision controls
- right: queue, readiness, notes

#### Left column

Shows:

- why the field or concept is ambiguous
- source evidence
- target expectation
- Codex rationale
- nearby mappings

#### Center column

Shows:

- active arbitration title
- recommended mapping
- alternatives
- confidence and risk framing
- explicit human controls:
  - approve
  - reject
  - edit target
  - escalate
  - add note

This column is the control point. Codex can propose, but the operator records the canonical decision.

#### Right column

Shows:

- review queue
- outcome/readiness snapshot
- decision notes
- linked Codex suggestions

## Persistent Codex Side Panel

## Intent

Codex must feel native to the workspace, not bolted on.

The side panel is always visible on desktop and collapsible on smaller screens.

## Panel sections

1. Chat transcript
2. Suggested actions
3. Quick prompts
4. Action composer
5. Event/result footer

## Demo-visible actions

The panel should expose the full UI action vocabulary even if some actions are still demo-backed:

- explain this mapping
- compare alternatives
- draft reviewer note
- approve recommendation
- reject mapping
- escalate to lead
- rerun reasoning
- rerun validation
- open supporting evidence
- prepare target package
- summarize open blockers

## Demo safety rule

Actions can exist before every backend capability is complete.

For demo mode:

- all actions update frontend state
- actions append visible activity items
- actions can call demo endpoints or mock handlers
- approval, rejection, escalation, and rerun actions must still look operational
- destructive/final actions must show confirmation language

This lets the team demo the full operating model without falsely claiming full automation.

## Backend Mapping

The UI must map cleanly to the backend work already done and the next Stage 1 tasks in `PLANS.md`.

### Backend-aligned workflow

1. Connect source and target
2. Crawl metadata and representative evidence
3. Build deterministic context graph
4. Run Codex semantic reasoning on the graph
5. Surface candidate mappings
6. Require human approval
7. Validate readiness
8. Prepare target package

### Current backend data that can already feed the UI

- projects
- uploaded files
- runs
- run history
- run events over SSE
- structured understand result
- graph snapshots

### New frontend contract expectations

The frontend should be ready to consume these event and state shapes:

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

Additional UI-facing event types that can be mocked now and formalized later:

- `checkpoint_opened`
- `checkpoint_approved`
- `checkpoint_rejected`
- `checkpoint_escalated`
- `review_note_added`
- `package_prepared`
- `validation_completed`
- `codex_action_requested`
- `codex_action_completed`

## Human Touchpoints

The human checkpoints from the plan are mandatory and must be visible in the UI narrative.

### Checkpoint 1: structure review

When:

- after Oracle and Supabase structures are crawled

Operator answers:

- do these systems and tables look correctly understood?
- are the important source areas represented?
- should the run continue into semantic reasoning?

UI treatment:

- checkpoint card in the progress band
- review summary in the workspace
- approve / request rescan / annotate controls

### Checkpoint 2: graph reasoning review

When:

- after Codex has reasoned over the evidence graph

Operator answers:

- do these inferred meanings look plausible?
- are the relationships and clusters sensible?
- should mapping proposals proceed?

UI treatment:

- graph tab or graph panel with visible hypothesis clusters
- Codex explanation support
- approve / challenge / escalate controls

### Checkpoint 3: candidate mapping review

When:

- before any migration/package action

Operator answers:

- do we accept this canonical target field or concept?
- what note should be attached to the audit trail?
- what ambiguity remains unresolved?

UI treatment:

- active arbitration card
- reviewer note field
- approve / reject / edit / escalate controls

## Graph Design Direction

The graph should be visually compelling but scoped for demo reality.

### Role of the graph

The graph is not the whole product view. It is one explanatory layer that proves:

- the system is building a structured understanding
- Codex is reasoning over that structure
- ambiguity resolution is grounded in evidence

### Recommended initial treatment

Use a contained graph surface inside the review workspace:

- glowing node clusters
- link pulses or soft wave motion
- category distinctions for source, semantic, and target concepts
- motion that suggests accumulation rather than a toy animation

### Important constraint

The graph should support the hero decision, not compete with it.

The operator must always understand:

- what the current issue is
- why Codex recommended its answer
- where human judgment is required

## Ralph Loop Plan

The design process should run in explicit evaluation loops.

### Loop 1: information architecture

Decide:

- exact workspace structure
- placement of Codex side panel
- tab set
- positioning of graph surface

Output:

- 2 to 3 wireframe-level workspace variants

### Loop 2: arbitration workspace variants

Decide:

- evidence density
- decision-card layout
- queue/outcome layout

Output:

- 3 higher-fidelity hero variants

### Loop 3: Codex side panel variants

Decide:

- panel width and prominence
- action grouping
- chat vs action balance

Output:

- 3 side-panel variants

### Loop 4: human checkpoint patterns

Decide:

- how approvals, escalations, and reviewer notes appear
- whether checkpoints are inline, modal, or drawer-based

Output:

- 2 to 3 checkpoint interaction patterns

### Loop 5: graph treatment variants

Decide:

- compact graph strip
- mid-size evidence graph
- dramatic hero graph accent

Output:

- 2 to 3 graph presentation variants

### Final merge

Select one winner from each loop and merge into the final implementation.

## Demo Build Scope

This demo must work from the frontend, even if some actions are still demo-backed.

### Must work for the demo

- page loads as a convincing migration workspace
- Codex side panel appears native
- actions are clickable
- active arbitration state changes are visible
- activity/audit trail updates are visible
- graph treatment is visible
- backend status can be shown where available
- one clear demo path can be narrated end-to-end

### Can be mocked initially

- full Oracle/Supabase live connectivity
- every Codex action’s backend implementation
- final package generation
- full graph recomputation after every UI action

## Demo Script

### Opening

"We connect an Oracle source and a Supabase target, but instead of asking the operator to inspect hundreds of tables manually, Codex reduces the estate into the semantic conflicts that actually block migration readiness."

### Context

"At the top, you can see the merged source estate, progress through the workflow, and the current readiness state. Most of the estate has already been reduced automatically."

### Active decision

"The center of the screen is one active arbitration. Codex is explaining why `status_cd` is ambiguous across inherited systems and recommending the canonical target mapping that best preserves downstream behavior."

### Human control

"This is the human checkpoint. Codex proposes, but the migration lead records the canonical choice, adds notes, and either approves, rejects, edits, or escalates."

### Codex panel

"On the right, Codex is available natively in the workspace. I can ask it to explain the mapping, compare alternatives, draft a reviewer note, rerun reasoning, or prepare the next step."

### Graph

"Below or alongside the decision flow, we show the evidence graph. This is how the system builds structured understanding across source systems and semantic concepts before it suggests a mapping."

### Outcome

"Once the human decision is made, the workspace updates readiness, records the audit note, and moves the migration package one step closer to validation and downstream packaging."

## Design Recommendation

Build the first implementation as:

- manager-derived review workspace layout
- persistent Codex side rail
- compact but vivid graph surface
- explicit human checkpoint controls
- demo-safe actions wired to frontend state first, backend second

This is the fastest route to a team-demoable product that still aligns with the real backend roadmap.

## Self-Review

- No placeholders remain.
- Scope is still one review workspace, not the entire product.
- Human checkpoints are explicit and consistent with `PLANS.md`.
- Demo-safe action language is clear about what is real now versus mock-backed.
