# Acquisition Schema Comparison

## Scenario

This document defines the first-pass schema comparison for an industrial manufacturing acquisition demo.

- `Company A`: cleaner acquirer ERP-style manufacturer
- `Company B`: acquired legacy manufacturer
- Goal: make semantic mapping difficult enough that naive code matching fails and a human-in-the-loop semantic layer is clearly valuable

This comparison now has matching Postgres DDL drafts in:

- `docs/sql/furnifuture.sql`
- `docs/sql/pinewoodworks.sql`

## Design principles

- Only `4` paired tables to keep the demo legible
- Every pair includes at least one field that looks mappable but is semantically unsafe
- Enum and status mismatches are deliberate
- At least one mismatch per pair depends on operational context, not just field name similarity
- Relationships are realistic enough to support later sample data, semantic mapping, and human approval flows

## Cross-table relationship summary

| Relationship | Company A | Company B | Why it matters |
| --- | --- | --- | --- |
| Product to BOM | `erp_material_master.material_id` -> `erp_bom_component.parent_material_id` / `component_material_id` | `legacy_item_catalog.item_no` -> `legacy_recipe_lines.top_item_no` / `line_item_no` | Material identity looks straightforward, but product classes and component semantics differ |
| Product to Inventory | `erp_material_master.material_id` -> `erp_inventory_balance.material_id` | `legacy_item_catalog.item_no` -> `legacy_stock_snapshot.item_no` | Stock meaning depends on status buckets and site modeling |
| Product to Orders | `erp_material_master.material_id` -> `erp_production_order.material_id` | `legacy_item_catalog.item_no` -> `legacy_job_ticket.item_no` | Order lifecycle state differs enough that product demand and execution are interpreted differently |

## 1. Product master

### Table purpose

- `Company A`: `erp_material_master` is a structured material master for manufactured, purchased, and engineering-controlled items
- `Company B`: `legacy_item_catalog` is a flatter item catalog where product type, sourcing intent, and operational readiness are partially encoded in reusable flags

### Side-by-side comparison

| Aspect | Company A: `erp_material_master` | Company B: `legacy_item_catalog` | Semantic trap |
| --- | --- | --- | --- |
| Primary key | `material_id` | `item_no` | Looks directly mappable, but legacy item numbering may include kits, tooling, and sellable bundles under the same namespace |
| Product type | `material_type_code` such as `FG`, `HALB`, `ROH`, `PHAN` | `item_class` such as `ASM`, `BUY`, `KIT`, `PKG` | Similar intent, different business boundaries; `KIT` in Company B may be commercial packaging, not a manufacturable semi-finished good |
| Lifecycle state | `lifecycle_status` such as `DESIGN`, `RELEASED`, `OBSOLETE` | `status_code` such as `A`, `H`, `S`, `R`, `D` | Legacy status meaning depends on item class and site usage; `H` may mean hold, inactive, or pending QA release depending on product family |
| Unit of measure | `base_uom` | `stock_uom` | Appears equivalent, but Company B may stock in purchasing units while Company A uses engineering base units |
| Sourcing model | `procurement_type` such as `E`, `F`, `X` | `source_flag` such as `M`, `P`, `T` | Both look like make/buy indicators, but Company B uses transfer or temporary outsource semantics that do not align cleanly to ERP procurement types |
| Planning behavior | `planning_strategy_code` | `family_rollup_code` | One is a planning control; the other is often a reporting or replenishment family grouping |
| Revision tracking | `revision_code` | `eng_rev_text` | Company A revision is controlled and discrete; Company B may store ad hoc engineering notes or mixed revision labels |
| Site context | optional `default_plant_code` | `site_mask` or site eligibility flag | Company B may allow one item row to imply multiple valid sites without a clean site master relationship |

### Why naive mapping fails

Fields like `material_type_code`, `status_code`, and `source_flag` look like direct enum mapping candidates, but their business meaning is not aligned. In Company B, the same code can imply different operational behaviors depending on item class, family, or site.

### What a human reviewer must resolve

- Whether `KIT` means a packaging bundle, a planning phantom, or a true assembly
- Whether `status_code` represents lifecycle, commercial sellability, or shop-floor release state
- Whether `source_flag` describes strategic sourcing, current execution mode, or a temporary migration workaround

## 2. Bill of materials

### Table purpose

- `Company A`: `erp_bom_component` models plant-aware BOM lines with alternate BOM support and controlled effectivity
- `Company B`: `legacy_recipe_lines` stores parent-component relationships, but quantity basis, substitutions, and yield loss behavior are only partially normalized

### Side-by-side comparison

| Aspect | Company A: `erp_bom_component` | Company B: `legacy_recipe_lines` | Semantic trap |
| --- | --- | --- | --- |
| Parent item | `parent_material_id` | `top_item_no` | Parent identity is similar, but Company B may also use the same field for kit headers and temporary conversion bundles |
| Component item | `component_material_id` | `line_item_no` | Straightforward on paper, but Company B may include non-stock text lines or pseudo-components in the same table |
| Site context | `plant_code` | `site_ref` | Both look like location fields, but Company B `site_ref` may combine plant, warehouse, and routing family |
| Variant control | `alternative_bom_no` | `recipe_variant` | Similar structure, different intent; Company A alternates are controlled engineering options, while Company B variants may reflect customer, batch, or line-specific practice |
| Quantity | `component_qty` + `component_uom` | `qty_per` or free-form `qty_basis_text` | Company B may encode quantity as a batch basis, ratio, or narrative formula instead of a clean per-parent quantity |
| Scrap / yield | `component_scrap_pct` | `yield_loss_code` or `scrap_basis_text` | Both describe expected loss, but one is numeric planning logic and the other may be operator guidance or a setup-loss convention |
| Effectivity | `valid_from_date`, `valid_to_date` | `effective_note` or `revision_note` | Company A has explicit dates; Company B may rely on notes, version tags, or shop-floor tribal knowledge |
| Phantom / substitute behavior | `phantom_item_flag`, `component_strategy_code` | `optional_flag`, `substitute_group`, `comment_text` | Similar migration destination, but Company B often hides substitute logic in comments or overloaded flags |

### Why naive mapping fails

The shared shape of parent-component rows makes the tables look easy to align, but Company B mixes engineering intent, operator instructions, and planning logic in the same record. Quantity and substitution semantics are especially unsafe to map directly.

### What a human reviewer must resolve

- Whether a legacy variant is a true alternate BOM or just a site-specific working method
- Whether free-text quantity basis can be normalized into a per-parent component requirement
- Whether optional or substitute flags affect planning, execution, or both

## 3. Inventory

### Table purpose

- `Company A`: `erp_inventory_balance` separates stock by plant, storage location, and formal inventory status
- `Company B`: `legacy_stock_snapshot` records stock posture with overloaded availability codes that blend physical, quality, and business restrictions

### Side-by-side comparison

| Aspect | Company A: `erp_inventory_balance` | Company B: `legacy_stock_snapshot` | Semantic trap |
| --- | --- | --- | --- |
| Product key | `material_id` | `item_no` | Product identity is familiar, but Company B may aggregate substitute items under one reporting code |
| Location | `plant_code`, `storage_location_code` | `site_whse_code` | Company B often collapses plant and warehouse semantics into one composite location token |
| Stock status | `stock_status_code` such as `UNR`, `QI`, `BLK`, `TRN` | `avail_code` such as `AVL`, `HLD`, `QA`, `MRB`, `REL` | Both are coded states, but Company B codes mix physical availability, commercial release, and quality disposition |
| Quantity model | separate quantity buckets such as `unrestricted_qty`, `quality_qty`, `blocked_qty` | `on_hand_qty`, `committed_qty`, `reserved_qty` | Company A uses explicit ERP buckets; Company B uses ledger-style totals that require interpretation before deriving available stock |
| Ownership / restriction | `special_stock_indicator` | `disposition_code` | Similar control surface, but legacy disposition may include customer ownership, quarantine reason, or accounting hold |
| Timing | `snapshot_ts` | `as_of_date` | Superficially similar, but one may be near-real-time and the other an overnight operational extract |

### Why naive mapping fails

“Available stock” is not a single comparable field across the two companies. Company A models status buckets directly; Company B expects downstream consumers to infer usable stock from a combination of totals and coded restrictions.

### What a human reviewer must resolve

- Which legacy `avail_code` values correspond to unrestricted, quality, or blocked stock
- Whether `committed_qty` reflects allocations, soft reservations, or open order demand
- Whether `site_whse_code` should map to plant, storage location, or a composite location concept

## 4. Orders

### Table purpose

- `Company A`: `erp_production_order` tracks production execution with explicit type, lifecycle, and quantity progression
- `Company B`: `legacy_job_ticket` captures manufacturing jobs with legacy order classes and phase codes that do not separate planning status from execution status cleanly

### Side-by-side comparison

| Aspect | Company A: `erp_production_order` | Company B: `legacy_job_ticket` | Semantic trap |
| --- | --- | --- | --- |
| Primary key | `production_order_id` | `job_id` | Order identity aligns structurally, but legacy jobs may be reused or split operationally without a strict parent-child order model |
| Product reference | `material_id` | `item_no` | Similar surface meaning, but legacy jobs may also represent rework or pack-out activity against the same item |
| Order type | `order_type_code` such as `PP01`, `REWK`, `ENGR` | `job_class` such as `STD`, `HOT`, `RMA`, `KIT` | Both are coded classes, but the business split is different; Company B mixes priority and fulfillment scenario into one field |
| Status / lifecycle | `order_status_code` such as `CRTD`, `REL`, `PCNF`, `CNF`, `TECO` | `phase_code` such as `10`, `20`, `30`, `90` plus `close_flag` | Legacy lifecycle is distributed across multiple fields and may not distinguish administrative close from physical completion |
| Location context | `plant_code` | `work_center_site` | One is a plant master reference; the other may encode both site and production cell lineage |
| Quantity progression | `planned_qty`, `released_qty`, `confirmed_qty`, `scrapped_qty` | `requested_qty`, `good_qty`, `reject_qty` | Both model execution progress, but they cut the lifecycle at different points and are not one-to-one states |
| Scheduling | `scheduled_start_ts`, `scheduled_end_ts` | `need_by_date`, `dispatch_date` | Similar dates with different operational meaning; Company B often tracks expediting dates rather than formal schedule commitments |
| Notes | controlled exception fields | `expedite_note`, `ops_comment` | Legacy notes often carry status overrides or routing exceptions not represented elsewhere |

### Why naive mapping fails

Company B does not model order lifecycle with a single clean state machine. The implementer would be forced to infer whether a job is released, in process, complete, or administratively closed from a combination of job class, phase code, quantities, and notes.

### What a human reviewer must resolve

- Which combinations of `phase_code` and `close_flag` truly match released, in-process, or completed orders
- Whether `job_class` is a manufacturing type, a priority marker, or a return/rework workflow
- Whether legacy dates represent committed production schedule, customer promise date, or dispatch target

## Why this schema set works for the demo

- Product identity is shared across all four table pairs, so later semantic mapping can propagate across the model
- The BOM pair exposes the difference between controlled engineering structure and operationally messy legacy build logic
- Inventory and order pairs create the kind of coded, context-heavy ambiguity that simple code mapping struggles to resolve
- A human reviewer has clear intervention points where semantics must be interpreted before mappings are approved

## Next iteration

Next likely step:

- add sample seed data that makes the mapping ambiguity visible
- optionally add lookup tables or ontology concepts for the first semantic mapping flow
