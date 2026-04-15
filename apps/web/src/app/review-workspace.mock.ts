import type { ReviewWorkspacePayload } from "../../../../packages/shared-types/src";

export const reviewWorkspaceMock: ReviewWorkspacePayload = {
  workspaceId: "workspace-merged-oracle-customer-domain",
  generatedAt: "2026-04-15T09:14:00Z",
  summary: {
    title: "Customer domain arbitration",
    sourceSystemLabel: "Oracle merged finance + CRM + marketing",
    targetSystemLabel: "Supabase-ready customer package",
    readinessLabel: "Partially ready",
    unresolvedDecisionCount: 2,
    autoResolvedCount: 5,
  },
  context: {
    narrative:
      "Codex reduced the Oracle scan into the semantic conflicts that still require implementation-lead judgement before package promotion.",
    conflictThemes: [
      "duplicate customer and account semantics",
      "shared code family with different business meaning",
      "unclear canonical ownership after merger",
    ],
    sourceNetwork: {
      root: { id: "oracle-prod", label: "oracle-prod", caption: "merged source" },
      nodes: [
        { id: "crm-core", label: "crm_core", caption: "identity" },
        { id: "fin-customer", label: "fin_customer", caption: "status" },
        { id: "legacy-mktg", label: "legacy_mktg", caption: "segment" },
      ],
      edges: [
        { from: "oracle-prod", to: "crm-core", kind: "schema" },
        { from: "oracle-prod", to: "fin-customer", kind: "schema" },
        { from: "fin-customer", to: "legacy-mktg", kind: "semantic_overlap" },
      ],
    },
  },
  activeDecision: {
    decisionId: "decision-status-cd",
    title: "Resolve the merged-company status conflict",
    status: "needs_review",
    sourceField: {
      fieldName: "status_cd",
      path: "fin_customer.account.status_cd",
      description: "Financial account state code reused after the merger.",
    },
    targetConcept: {
      conceptId: "customer_status",
      label: "Customer status",
      description: "Canonical customer-level lifecycle status used for reporting and readiness checks.",
    },
    rationale:
      "Codex detected that the same code family is used with account-oriented meaning in finance, but the downstream migration package expects a single customer-level status concept.",
    impactSummary:
      "This choice affects readiness validation, package semantics, and how downstream teams interpret active versus inactive customer state.",
    recommendedOptionId: "option-customer-status",
    options: [
      {
        optionId: "option-customer-status",
        label: "Map to customer_status",
        targetField: "customer_status",
        confidence: 0.64,
        recommendation: "recommended",
        rationale: "Best fit for consolidated reporting, package validation, and the downstream customer model.",
        consequences: [
          "supports a single canonical readiness rule",
          "keeps downstream package semantics aligned",
          "requires noting the semantic compromise in audit trail",
        ],
      },
      {
        optionId: "option-account-state",
        label: "Map to account_state",
        targetField: "account_state",
        confidence: 0.51,
        recommendation: "alternative",
        rationale: "Closer to the literal finance meaning, but weakens the unified target model and pushes more ambiguity downstream.",
        consequences: [
          "preserves source-local semantics",
          "adds friction to package validation",
          "creates mismatch against customer-level reporting expectations",
        ],
      },
    ],
    actions: [
      { actionId: "approve", label: "Approve recommended mapping", kind: "approve" },
      { actionId: "edit", label: "Edit target field", kind: "edit" },
      { actionId: "reject", label: "Reject and flag", kind: "reject" },
    ],
  },
  evidence: [
    {
      evidenceId: "evidence-finance-behavior",
      kind: "observed_behavior",
      title: "Observed behavior in finance workflows",
      sourceLabel: "fin_customer.account.status_cd",
      summary: "Values align to account lifecycle transitions in finance workflows rather than only customer standing.",
      weight: "high",
    },
    {
      evidenceId: "evidence-target-expectation",
      kind: "target_constraint",
      title: "Target package expectation",
      sourceLabel: "customers.customer_status",
      summary: "Readiness checks assume one customer-level status used for reporting and package validation.",
      weight: "high",
    },
    {
      evidenceId: "evidence-codex-rationale",
      kind: "codex_inference",
      title: "Codex suggested interpretation",
      sourceLabel: "semantic reasoning",
      summary: "Map to the target concept that preserves downstream behavior, then record the semantic compromise in the package audit trail.",
      weight: "medium",
    },
  ],
  nearbyMappings: [
    {
      mappingId: "map-cust-no",
      sourceField: "cust_no",
      sourcePath: "crm_core.customer.cust_no",
      proposedTarget: "customer_id",
      status: "auto_resolved",
      confidence: 0.98,
      summary: "Stable identity mapping to customer_id.",
    },
    {
      mappingId: "map-status-cd",
      sourceField: "status_cd",
      sourcePath: "fin_customer.account.status_cd",
      proposedTarget: "customer_status | account_state",
      status: "needs_review",
      confidence: 0.64,
      summary: "Candidate target is split between customer_status and account_state.",
    },
    {
      mappingId: "map-segment-cd",
      sourceField: "segment_cd",
      sourcePath: "legacy_mktg.segment.segment_cd",
      proposedTarget: "customer_segment",
      status: "queued",
      confidence: 0.59,
      summary: "Needs a translation rule after the current decision lands.",
    },
  ],
  queue: [
    {
      queueItemId: "queue-status-cd",
      title: "status_cd ownership conflict",
      state: "active",
      priority: "high",
      summary: "Finance and CRM use overlapping labels with different operational meaning.",
      blockedOutcomeIds: ["outcome-readiness"],
    },
    {
      queueItemId: "queue-segment-cd",
      title: "segment_cd translation rule",
      state: "next",
      priority: "high",
      summary: "Legacy marketing taxonomy needs one approved canonical translation table.",
      blockedOutcomeIds: ["outcome-package-shape"],
    },
    {
      queueItemId: "queue-region-owner",
      title: "region_owner source selection",
      state: "queued",
      priority: "medium",
      summary: "Important, but not blocking the package until the current decision lands.",
      blockedOutcomeIds: [],
    },
  ],
  outcomes: [
    {
      outcomeId: "outcome-readiness",
      label: "Package readiness",
      value: "87%",
      status: "blocked",
      summary: "Expected readiness after the two open decisions are resolved.",
    },
    {
      outcomeId: "outcome-auto-resolved",
      label: "Auto-cleared mappings",
      value: "5",
      status: "ready",
      summary: "Mappings already strong enough to carry forward automatically.",
    },
  ],
  reviewerNote: {
    placeholder:
      "Add a reviewer comment, package note, or escalation rationale that will travel with the migration package.",
  },
};
