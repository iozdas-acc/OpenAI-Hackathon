export type ReviewItemState = "active" | "next" | "queued";
export type ReviewStatus = "needs_review" | "ready" | "blocked" | "auto_resolved";
export type EvidenceWeight = "high" | "medium" | "low";
export type EvidenceKind =
  | "observed_behavior"
  | "target_constraint"
  | "codex_inference"
  | "source_overlap";
export type ReviewOptionRecommendation = "recommended" | "alternative";
export type ReviewActionKind = "approve" | "edit" | "reject";

export interface ReviewWorkspacePayload {
  workspaceId: string;
  generatedAt: string;
  summary: ReviewWorkspaceSummary;
  context: ReviewWorkspaceContext;
  activeDecision: ActiveReviewDecision;
  evidence: ReviewEvidence[];
  nearbyMappings: NearbyMapping[];
  queue: ReviewQueueItem[];
  outcomes: ReviewOutcome[];
  reviewerNote: ReviewerNote;
}

export interface ReviewWorkspaceSummary {
  title: string;
  sourceSystemLabel: string;
  targetSystemLabel: string;
  readinessLabel: string;
  unresolvedDecisionCount: number;
  autoResolvedCount: number;
}

export interface ReviewWorkspaceContext {
  narrative: string;
  conflictThemes: string[];
  sourceNetwork: SourceNetworkGraph;
}

export interface SourceNetworkGraph {
  root: SourceNetworkNode;
  nodes: SourceNetworkNode[];
  edges: SourceNetworkEdge[];
}

export interface SourceNetworkNode {
  id: string;
  label: string;
  caption: string;
}

export interface SourceNetworkEdge {
  from: string;
  to: string;
  kind: "schema" | "semantic_overlap" | "dependency";
}

export interface ActiveReviewDecision {
  decisionId: string;
  title: string;
  status: ReviewStatus;
  sourceField: DecisionField;
  targetConcept: TargetConcept;
  rationale: string;
  impactSummary: string;
  recommendedOptionId: string;
  options: ReviewOption[];
  actions: ReviewAction[];
}

export interface DecisionField {
  fieldName: string;
  path: string;
  description: string;
}

export interface TargetConcept {
  conceptId: string;
  label: string;
  description: string;
}

export interface ReviewOption {
  optionId: string;
  label: string;
  targetField: string;
  confidence: number;
  recommendation: ReviewOptionRecommendation;
  rationale: string;
  consequences: string[];
}

export interface ReviewAction {
  actionId: string;
  label: string;
  kind: ReviewActionKind;
}

export interface ReviewEvidence {
  evidenceId: string;
  kind: EvidenceKind;
  title: string;
  sourceLabel: string;
  summary: string;
  weight: EvidenceWeight;
}

export interface NearbyMapping {
  mappingId: string;
  sourceField: string;
  sourcePath: string;
  proposedTarget: string;
  status: ReviewStatus | ReviewItemState;
  confidence: number;
  summary: string;
}

export interface ReviewQueueItem {
  queueItemId: string;
  title: string;
  state: ReviewItemState;
  priority: "high" | "medium" | "low";
  summary: string;
  blockedOutcomeIds: string[];
}

export interface ReviewOutcome {
  outcomeId: string;
  label: string;
  value: string;
  status: "ready" | "blocked" | "pending";
  summary: string;
}

export interface ReviewerNote {
  placeholder: string;
}
