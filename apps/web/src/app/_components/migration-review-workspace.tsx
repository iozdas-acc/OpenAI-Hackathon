"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";

type BackendProbe = {
  backendUrl: string;
  checkedAt: string;
  latencyMs: number;
  payload: { status?: string } | null;
  ok: boolean;
  status: number;
};

type ProbeState = {
  data: BackendProbe | null;
  error: string | null;
  loading: boolean;
};

type ReviewDecision = "approve" | "reject" | "defer" | "request_changes";
type ReviewState = "pending" | "approved" | "needs_input" | "escalated" | "rejected";
type GraphPhase = "crawl" | "shape" | "reason" | "question" | "mapping";

type ChatRole = "user" | "assistant";

type Message = {
  id: string;
  role: ChatRole;
  content: string;
  pending?: boolean;
};

type Checkpoint = {
  id: "structure" | "clarify" | "mapping";
  label: string;
  title: string;
  description: string;
  state: ReviewState;
};

type ReviewRecord = {
  decision?: ReviewDecision;
  notes?: string;
  submitted_at?: string;
};

type RunRecord = {
  id: string;
  project_id: string;
  status: string;
  instructions: string;
  metadata?: {
    reviews?: {
      crawl_review?: ReviewRecord;
      reasoning_review?: ReviewRecord;
      mapping_review?: ReviewRecord;
    };
    crawl_artifacts?: {
      source_profile?: ProfileRecord;
      target_profile?: ProfileRecord & { warnings?: Array<{ message?: string }> };
    };
    migration_request?: {
      notes?: string;
      requested_at?: string;
    };
    error_message?: string;
  };
};

type QuestionRecord = {
  prompt?: string;
};

type ConfidenceRecord = {
  overall?: number;
  by_entity?: Record<string, number>;
};

type ResultRecord = {
  summary?: string;
  questions?: QuestionRecord[];
  confidence?: ConfidenceRecord;
};

type GraphNodeRecord = {
  id?: string;
  label?: string;
  type?: string;
  data?: {
    role?: string;
    data_type?: string;
  };
};

type GraphEdgeRecord = {
  source?: string;
  target?: string;
  relation?: string;
};

type GraphRecord = {
  nodes?: GraphNodeRecord[];
  edges?: GraphEdgeRecord[];
};

type EventRecord = {
  id: string;
  type: string;
  timestamp?: string;
  payload?: Record<string, unknown>;
};

type TableRecord = {
  name?: string;
  schema?: string;
  columns?: Array<{ name?: string; type?: string }>;
  sample_rows?: Array<Record<string, unknown>>;
};

type ProfileRecord = {
  database?: {
    name?: string;
    kind?: string;
    role?: string;
  };
  schemas?: Array<{ name?: string }>;
  tables?: TableRecord[];
  warnings?: Array<{ message?: string }>;
};

type DemoRunResponse = {
  selectedRunId: string | null;
  selectionReason: string;
  run: RunRecord | null;
  result: ResultRecord | null;
  graph: GraphRecord | null;
  events: EventRecord[];
};

const DEFAULT_SOURCE_FIELD = "core.customers.customer_id";
const DEFAULT_PRIMARY_TARGET = "public.customers.customer_id";
const DEFAULT_SECONDARY_TARGET = "public.customers";
const DEFAULT_CONCEPT = "Customer identity";
const DEFAULT_QUESTION =
  "Does this source field represent the canonical customer identifier we should preserve into the target model?";

const INITIAL_CHECKPOINTS: Checkpoint[] = [
  {
    id: "structure",
    label: "Checkpoint 1",
    title: "Approve discovered structure",
    description: "Confirm the source and target structures are correct before semantic reasoning continues.",
    state: "pending",
  },
  {
    id: "clarify",
    label: "Checkpoint 2",
    title: "Approve reasoning checkpoint",
    description: "Review Codex reasoning and capture the key human clarification that decides the mapping.",
    state: "pending",
  },
  {
    id: "mapping",
    label: "Checkpoint 3",
    title: "Approve mapping package",
    description: "Accept, reject, or escalate the final candidate package before migration is exposed.",
    state: "pending",
  },
];

const INITIAL_MESSAGES: Message[] = [
  {
    id: "m-1",
    role: "assistant",
    content:
      "I am watching the active migration review run. Use the touchpoints on the right to approve structure, reasoning, and the final mapping package.",
  },
];

const DATABASE_PROMPTS = [
  { label: "Explain evidence", prompt: "Explain the strongest evidence behind the current recommendation." },
  { label: "Show join clues", prompt: "Summarize the strongest structural join clues between source and target." },
  { label: "Ask blocker", prompt: "Ask the single human question that would reduce semantic risk the most." },
  { label: "Compare options", prompt: "Compare the primary mapping and the fallback in one short decision memo." },
  { label: "Prepare package", prompt: "Summarize what is approved and what still blocks migration." },
];

const CLARIFICATION_CHOICES = [
  "Approve reasoning and keep the current recommendation",
  "Approve reasoning but note semantic ambiguity for later review",
  "Stop here and request changes from the analyst",
];

async function loadProbe(): Promise<BackendProbe> {
  const response = await fetch("/api/backend/health", { cache: "no-store" });
  const data = (await response.json()) as BackendProbe & { error?: string };
  if (!response.ok) {
    throw new Error(data.error ?? "Backend probe failed.");
  }
  return data;
}

async function loadDemoRun(): Promise<DemoRunResponse> {
  const response = await fetch("/api/demo/run", { cache: "no-store" });
  const data = (await response.json()) as DemoRunResponse;
  if (!response.ok) {
    throw new Error(data.selectionReason || "Could not load demo run.");
  }
  return data;
}

async function loadPinnedDemoRun(runId: string | null): Promise<DemoRunResponse> {
  const search = runId ? `?runId=${encodeURIComponent(runId)}` : "";
  const response = await fetch(`/api/demo/run${search}`, { cache: "no-store" });
  const data = (await response.json()) as DemoRunResponse;
  if (!response.ok) {
    throw new Error(data.selectionReason || "Could not load demo run.");
  }
  return data;
}

function createId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function statusLabel(state: ReviewState): string {
  if (state === "approved") return "Approved";
  if (state === "needs_input") return "Needs input";
  if (state === "escalated") return "Escalated";
  if (state === "rejected") return "Rejected";
  return "Queued";
}

function classifyReview(decision: ReviewDecision | undefined, fallback: ReviewState): ReviewState {
  if (decision === "approve") return "approved";
  if (decision === "reject") return "rejected";
  if (decision === "request_changes" || decision === "defer") return "escalated";
  return fallback;
}

function deriveCheckpoints(run: RunRecord | null): Checkpoint[] {
  const checkpoints = INITIAL_CHECKPOINTS.map((checkpoint) => ({ ...checkpoint }));
  if (!run) {
    return checkpoints;
  }

  const reviews = run.metadata?.reviews ?? {};
  const status = run.status;

  if (status === "awaiting_crawl_review") {
    checkpoints[0].state = classifyReview(reviews.crawl_review?.decision, "needs_input");
  }

  if (status === "awaiting_reasoning_review") {
    checkpoints[0].state = classifyReview(reviews.crawl_review?.decision, "approved");
    checkpoints[1].state = classifyReview(reviews.reasoning_review?.decision, "needs_input");
  }

  if (status === "awaiting_mapping_review") {
    checkpoints[0].state = classifyReview(reviews.crawl_review?.decision, "approved");
    checkpoints[1].state = classifyReview(reviews.reasoning_review?.decision, "approved");
    checkpoints[2].state = classifyReview(reviews.mapping_review?.decision, "needs_input");
  }

  if (["migration_ready", "migrating", "migration_completed", "completed"].includes(status)) {
    checkpoints[0].state = classifyReview(reviews.crawl_review?.decision, "approved");
    checkpoints[1].state = classifyReview(reviews.reasoning_review?.decision, "approved");
    checkpoints[2].state = classifyReview(reviews.mapping_review?.decision, "approved");
  }

  if (status === "failed") {
    checkpoints[0].state = classifyReview(reviews.crawl_review?.decision, "rejected");
    checkpoints[1].state = classifyReview(reviews.reasoning_review?.decision, "pending");
    checkpoints[2].state = classifyReview(reviews.mapping_review?.decision, "pending");
  }

  return checkpoints;
}

function deriveGraphPhase(status: string | undefined): GraphPhase {
  if (status === "awaiting_crawl_review") return "crawl";
  if (status === "awaiting_reasoning_review") return "question";
  if (status === "awaiting_mapping_review") return "reason";
  if (["migration_ready", "migrating", "migration_completed", "completed"].includes(status ?? "")) return "mapping";
  return "shape";
}

function deriveProgressLabel(status: string | undefined): string {
  if (status === "awaiting_crawl_review") return "Waiting on structure approval";
  if (status === "awaiting_reasoning_review") return "Waiting on reasoning approval";
  if (status === "awaiting_mapping_review") return "Waiting on mapping approval";
  if (status === "migration_ready") return "Ready for operator-triggered migration";
  if (status === "migration_completed") return "Mock migration completed";
  if (status === "failed") return "Run needs intervention";
  if (status === "running") return "Orchestration is running";
  return "Suggestion assembled";
}

function formatTimestamp(value: string | undefined): string {
  if (!value) {
    return "just now";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function buildActivity(events: EventRecord[]): Array<{ id: string; text: string }> {
  return events
    .slice(-6)
    .reverse()
    .map((event) => ({
      id: event.id,
      text: `${formatTimestamp(event.timestamp)} · ${event.type.replaceAll("_", " ")}`,
    }));
}

function extractFieldLabels(graph: GraphRecord | null): {
  sourceField: string;
  recommendedTarget: string;
  alternativeTarget: string;
  semanticConcept: string;
} {
  const nodes = graph?.nodes ?? [];
  const sourceColumns = nodes.filter((node) => node.type === "column" && node.data?.role === "source");
  const targetColumns = nodes.filter((node) => node.type === "column" && node.data?.role === "target");
  const semanticNode = nodes.find((node) => node.type === "semantic_concept" || node.type === "entity");

  return {
    sourceField: sourceColumns[0]?.label ?? DEFAULT_SOURCE_FIELD,
    recommendedTarget: targetColumns[0]?.label ?? DEFAULT_PRIMARY_TARGET,
    alternativeTarget: targetColumns[1]?.label ?? targetColumns[0]?.label ?? DEFAULT_SECONDARY_TARGET,
    semanticConcept: semanticNode?.label ?? DEFAULT_CONCEPT,
  };
}

export function MigrationReviewWorkspace() {
  const [probeState, setProbeState] = useState<ProbeState>({
    data: null,
    error: null,
    loading: true,
  });
  const [demoState, setDemoState] = useState<{
    data: DemoRunResponse | null;
    error: string | null;
    loading: boolean;
  }>({
    data: null,
    error: null,
    loading: true,
  });
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [composer, setComposer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [actionPending, setActionPending] = useState<string | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    const runProbe = async () => {
      try {
        const data = await loadProbe();
        if (!cancelled) {
          setProbeState({ data, error: null, loading: false });
        }
      } catch (error) {
        if (!cancelled) {
          setProbeState({
            data: null,
            error: error instanceof Error ? error.message : "Backend probe failed.",
            loading: false,
          });
        }
      }
    };

    void runProbe();
    const timer = window.setInterval(() => void runProbe(), 10000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const refreshDemo = async () => {
      try {
        const data = await loadPinnedDemoRun(selectedRunId);
        if (!cancelled) {
          setSelectedRunId((current) => current ?? data.selectedRunId);
          setDemoState({ data, error: null, loading: false });
        }
      } catch (error) {
        if (!cancelled) {
          setDemoState({
            data: null,
            error: error instanceof Error ? error.message : "Could not load demo run.",
            loading: false,
          });
        }
      }
    };

    void refreshDemo();
    const timer = window.setInterval(() => void refreshDemo(), 4000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [selectedRunId]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  const run = demoState.data?.run ?? null;
  const result = demoState.data?.result ?? null;
  const graph = demoState.data?.graph ?? null;
  const events = demoState.data?.events ?? [];
  const checkpoints = useMemo(() => deriveCheckpoints(run), [run]);
  const graphPhase = useMemo(() => deriveGraphPhase(run?.status), [run?.status]);
  const progressLabel = useMemo(() => deriveProgressLabel(run?.status), [run?.status]);
  const activity = useMemo(() => buildActivity(events), [events]);
  const labels = useMemo(() => extractFieldLabels(graph), [graph]);
  const graphScore = useMemo(() => {
    const overall = result?.confidence?.overall;
    if (typeof overall === "number") {
      return Math.round(overall * 100);
    }
    if (run?.status === "migration_ready" || run?.status === "migration_completed") return 95;
    if (run?.status === "awaiting_mapping_review") return 87;
    if (run?.status === "awaiting_reasoning_review") return 74;
    if (run?.status === "awaiting_crawl_review") return 62;
    return 68;
  }, [result?.confidence?.overall, run?.status]);
  const focusQuestion = result?.questions?.[0]?.prompt ?? DEFAULT_QUESTION;
  const backendLabel = useMemo(() => {
    if (probeState.loading && !probeState.data) return "Connecting";
    if (probeState.error) return "Backend offline";
    if (probeState.data?.ok) return "Backend live";
    return "Pending";
  }, [probeState.data, probeState.error, probeState.loading]);

  const sourceProfile = run?.metadata?.crawl_artifacts?.source_profile;
  const targetProfile = run?.metadata?.crawl_artifacts?.target_profile;
  const sourceTables = sourceProfile?.tables ?? [];
  const targetTables = targetProfile?.tables ?? [];
  const targetWarnings = targetProfile?.warnings ?? [];
  const sourceSchemas = sourceProfile?.schemas?.length ?? 0;
  const targetSchemas = targetProfile?.schemas?.length ?? 0;
  const structureCheckpoint = checkpoints[0];
  const clarifyCheckpoint = checkpoints[1];
  const mappingCheckpoint = checkpoints[2];

  useEffect(() => {
    const graphStage = graphRef.current;
    if (!graphStage) {
      return;
    }

    const nodes = graphStage.querySelectorAll(".graph-node");
    const links = graphStage.querySelectorAll(".graph-link");
    const highlight = graphStage.querySelector(".graph-highlight");

    const timeline = gsap.timeline();
    timeline
      .fromTo(
        nodes,
        { scale: 0.84, opacity: 0.3, y: 14 },
        { scale: 1, opacity: 1, y: 0, duration: 0.65, stagger: 0.08, ease: "power2.out" },
      )
      .fromTo(
        links,
        { opacity: 0.12, scaleX: 0.8 },
        { opacity: 1, scaleX: 1, duration: 0.55, stagger: 0.05, ease: "power1.out" },
        "-=0.35",
      );

    if (highlight) {
      gsap.to(highlight, {
        scale: 1.12,
        opacity: 0.9,
        duration: 1,
        repeat: 1,
        yoyo: true,
        ease: "power1.inOut",
      });
    }

    return () => {
      timeline.kill();
    };
  }, [graphPhase, labels.sourceField, labels.recommendedTarget, labels.semanticConcept]);

  useEffect(() => {
    if (!run) {
      return;
    }
    setMessages((current) => {
      const intro = {
        id: "m-run",
        role: "assistant" as const,
        content: `Active run ${run.id.slice(0, 8)} is in ${run.status.replaceAll("_", " ")}. I will explain evidence while the operator controls the checkpoints.`,
      };
      return [intro, ...current.filter((message) => message.id !== "m-run")];
    });
  }, [run?.id, run?.status]);

  async function refreshDemoState() {
    const data = await loadPinnedDemoRun(selectedRunId);
    setSelectedRunId((current) => current ?? data.selectedRunId);
    setDemoState({ data, error: null, loading: false });
  }

  async function submitReview(reviewType: "crawl" | "reasoning" | "mappings", decision: ReviewDecision, notes: string) {
    if (!run) {
      return;
    }

    setActionPending(reviewType);
    setActionError(null);
    try {
      const response = await fetch(`/api/backend/runs/${run.id}/reviews/${reviewType}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, notes }),
        signal: AbortSignal.timeout(4000),
      });
      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        throw new Error(payload.detail ?? `Review submission failed with status ${response.status}.`);
      }
      await refreshDemoState();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Review submission failed.");
    } finally {
      setActionPending(null);
    }
  }

  async function triggerMigration() {
    if (!run) {
      return;
    }

    setActionPending("migrate");
    setActionError(null);
    try {
      const response = await fetch(`/api/backend/runs/${run.id}/migrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Operator triggered demo migration from the review workspace." }),
        signal: AbortSignal.timeout(4000),
      });
      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        throw new Error(payload.detail ?? `Migration trigger failed with status ${response.status}.`);
      }
      await refreshDemoState();
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Migration trigger failed.");
    } finally {
      setActionPending(null);
    }
  }

  async function sendPrompt(prompt: string, requestedAction?: string) {
    const trimmed = prompt.trim();
    if (!trimmed || isStreaming) {
      return;
    }

    const userMessage: Message = { id: createId("user"), role: "user", content: trimmed };
    const assistantId = createId("assistant");

    setMessages((current) => [...current, userMessage, { id: assistantId, role: "assistant", content: "", pending: true }]);
    setComposer("");
    setIsStreaming(true);

    try {
      const response = await fetch("/api/codex/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage].slice(-10).map((message) => ({
            role: message.role,
            content: message.content,
          })),
          action_context: {
            project_id: run?.project_id ?? "oracle-supabase-demo",
            run_id: run?.id ?? "run-demo-001",
            requested_action: requestedAction ?? null,
            available_actions: [
              "explain_mapping",
              "compare_alternatives",
              "draft_reviewer_note",
              "prepare_package",
            ],
            ui_state: {
              graphPhase,
              graphScore,
              checkpoints,
              focusQuestion,
              selectionReason: demoState.data?.selectionReason ?? null,
            },
          },
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Codex stream failed with status ${response.status}.`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const eventChunk of events) {
          const lines = eventChunk.split(/\r?\n/);
          const eventType = lines.find((line) => line.startsWith("event:"))?.slice(6).trim() ?? "message";
          const payloadText = lines
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.slice(5).trimStart())
            .join("\n")
            .trim();
          if (!payloadText) {
            continue;
          }

          let parsed: Record<string, unknown> = {};
          try {
            parsed = JSON.parse(payloadText) as Record<string, unknown>;
          } catch {
            parsed = { raw: payloadText };
          }

          if (eventType === "assistant_delta") {
            const delta = typeof parsed.delta === "string" ? parsed.delta : "";
            if (delta) {
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId ? { ...message, content: `${message.content}${delta}` } : message,
                ),
              );
            }
          }
        }
      }
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                content:
                  error instanceof Error
                    ? `Codex could not complete that request: ${error.message}`
                    : "Codex could not complete that request.",
              }
            : message,
        ),
      );
    } finally {
      setMessages((current) =>
        current.map((message) => (message.id === assistantId ? { ...message, pending: false } : message)),
      );
      setIsStreaming(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendPrompt(composer);
  }

  const evidenceItems = [
    `Source intake: ${sourceTables.length} table(s) across ${sourceSchemas} schema(s).`,
    `Target database: ${targetTables.length} table(s) across ${targetSchemas} schema(s).`,
    result?.summary || "Codex reasoning summary will appear here once the reasoning checkpoint has completed.",
  ];

  const candidateMappings = [
    {
      id: "primary",
      title: labels.recommendedTarget,
      score: `${graphScore}%`,
      tone: "recommended",
      note: "Current primary recommendation based on the latest backend state.",
    },
    {
      id: "secondary",
      title: labels.alternativeTarget,
      score: `${Math.max(graphScore - 23, 41)}%`,
      tone: "alternative",
      note: "Visible fallback so the operator can redirect the mapping if needed.",
    },
  ];

  const migrateVisible = run?.status === "migration_ready" || run?.status === "migration_completed";
  const migrationResult = [...events].reverse().find((event) => event.type === "migration_completed");
  const canApproveStructure = run?.status === "awaiting_crawl_review";
  const canApproveReasoning = run?.status === "awaiting_reasoning_review";
  const canApproveMapping = run?.status === "awaiting_mapping_review";

  return (
    <main className="orchestrator-page">
      <section className="orchestrator-shell">
        <header className="hero-strip">
          <div>
            <span className="eyebrow">Suggestion-First Review</span>
            <h1>The AI suggestion comes first. The human approves it through explicit semantic checkpoints.</h1>
            <p className="subhead">
              This workspace is now bound to a real backend run. The operator can approve structure, reasoning, and mapping
              directly in the UI, then trigger the mock migration step for the demo.
            </p>
          </div>
            <div className="status-stack">
              <div className="status-card">
                <div className="status-kicker">Current state</div>
                <strong>{progressLabel}</strong>
                <span>Backend: {backendLabel}</span>
                <span>Run: {run ? `${run.id.slice(0, 8)} · ${run.status}` : "Waiting for demo run"}</span>
              </div>
              {actionError ? <div className="inline-error">{actionError}</div> : null}
              <div className="status-chips">
                <span className="status-chip">{sourceTables.length > 0 ? "Source package loaded" : "Source pending"}</span>
                <span className="status-chip">{targetTables.length > 0 ? "Target database read" : "Target pending"}</span>
                <span className="status-chip accent">Graph score {graphScore}%</span>
              </div>
          </div>
        </header>

        <section className="main-grid">
          <div className="primary-column">
            <section className="suggestion-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">AI Suggested Mapping</span>
                  <h2>
                    {labels.sourceField} → {labels.recommendedTarget}
                  </h2>
                </div>
                <span className="stream-pill active-soft">{statusLabel(mappingCheckpoint.state)}</span>
              </div>

              <div className="suggestion-summary">
                <div className="summary-core">
                  <div className="mapping-pill recommended">Recommended target</div>
                  <strong>{labels.semanticConcept}</strong>
                  <p>
                    {result?.summary ??
                      "Codex will attach a reasoning summary here once the backend run passes the structure checkpoint."}
                  </p>
                </div>
                <div className="confidence-card">
                  <span>Confidence</span>
                  <strong>{graphScore}%</strong>
                  <p>{demoState.data?.selectionReason ?? "Reviewable run selection is pending."}</p>
                </div>
              </div>

              <div className="evidence-list">
                {evidenceItems.map((item) => (
                  <article key={item} className="evidence-card">
                    <span className="evidence-kicker">Backend evidence</span>
                    <p>{item}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="candidate-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Database Evidence</span>
                  <h2>Source intake and live target read</h2>
                </div>
              </div>

              <div className="database-grid">
                <article className="database-card">
                  <span className="section-label">Source side</span>
                  <strong>{sourceProfile?.database?.name ?? "Oracle source package"}</strong>
                  <p>{sourceTables.length} table(s), {sourceSchemas} schema(s)</p>
                  <code>{sourceTables[0]?.schema ?? "core"}.{sourceTables[0]?.name ?? "customers"}</code>
                </article>
                <article className="database-card">
                  <span className="section-label">Target side</span>
                  <strong>{targetProfile?.database?.name ?? "Supabase target"}</strong>
                  <p>{targetTables.length} table(s), {targetSchemas} schema(s)</p>
                  <code>{targetTables[0]?.schema ?? "public"}.{targetTables[0]?.name ?? "customers"}</code>
                </article>
                <article className="database-card warning">
                  <span className="section-label">Target read health</span>
                  <strong>{targetWarnings.length === 0 ? "No read warnings" : `${targetWarnings.length} warning(s)`}</strong>
                  <p>{targetWarnings[0]?.message ?? "Sample rows and structural metadata were captured successfully."}</p>
                </article>
              </div>
            </section>

            <section className="candidate-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Two Candidate Mappings</span>
                  <h2>Primary suggestion with one visible fallback</h2>
                </div>
              </div>

              <div className="candidate-grid">
                {candidateMappings.map((candidate) => (
                  <article key={candidate.id} className={`candidate-card ${candidate.tone}`}>
                    <div className="candidate-topline">
                      <span className="mapping-pill">{candidate.tone === "recommended" ? "Primary" : "Alternative"}</span>
                      <strong>{candidate.score}</strong>
                    </div>
                    <h3>{candidate.title}</h3>
                    <p>{candidate.note}</p>
                    <div className="candidate-inline-map">
                      <span>{labels.sourceField}</span>
                      <i />
                      <span>{candidate.title}</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="graph-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Context Graph</span>
                  <h2>Source field, semantic concept, and target path</h2>
                </div>
                <span className="mini-pill">{progressLabel}</span>
              </div>

              <div className="graph-stage" ref={graphRef} aria-hidden="true">
                <div className="graph-highlight" />
                <div className="graph-link strong link-a" />
                <div className="graph-link strong link-b" />
                <div className="graph-link link-c" />
                <div className="graph-link link-d" />

                <div className="graph-node oracle node-a">
                  <strong>{labels.sourceField}</strong>
                  <span>Source field</span>
                </div>
                <div className="graph-node oracle node-b">
                  <strong>{sourceTables[0]?.schema ?? "core"}.{sourceTables[0]?.name ?? "customers"}</strong>
                  <span>Source structure</span>
                </div>
                <div className="graph-node semantic node-c">
                  <strong>{labels.semanticConcept}</strong>
                  <span>Suggested ontology concept</span>
                </div>
                <div className="graph-node target recommended node-e">
                  <strong>{labels.recommendedTarget}</strong>
                  <span>Primary target mapping</span>
                </div>
                <div className="graph-node target node-f">
                  <strong>{labels.alternativeTarget}</strong>
                  <span>Fallback target mapping</span>
                </div>
              </div>

              <div className="graph-caption">
                The thick path shows the current recommendation from the backend state. The fallback remains visible so the
                operator can redirect the mapping if needed.
              </div>
            </section>
          </div>

          <aside className="support-column">
            <section className="touchpoint-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Human Touchpoints</span>
                  <h2>Approval flow</h2>
                </div>
              </div>

              <div className="touchpoint-stack">
                <article className={`touchpoint ${structureCheckpoint.state}`}>
                  <span className="touchpoint-kicker">{structureCheckpoint.label}</span>
                  <strong>{structureCheckpoint.title}</strong>
                  <p>{structureCheckpoint.description}</p>
                  <span className="touchpoint-state">{statusLabel(structureCheckpoint.state)}</span>
                  <div className="touchpoint-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => void submitReview("crawl", "approve", "Operator approved the discovered structure from the UI.")}
                      disabled={isStreaming || actionPending !== null || !run || !canApproveStructure}
                    >
                      {actionPending === "crawl" ? "Submitting..." : "Approve structure"}
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void submitReview("crawl", "request_changes", "Operator requested a structure rescan from the UI.")}
                      disabled={isStreaming || actionPending !== null || !run || !canApproveStructure}
                    >
                      Request rescan
                    </button>
                  </div>
                </article>

                <article className={`touchpoint ${clarifyCheckpoint.state}`}>
                  <span className="touchpoint-kicker">{clarifyCheckpoint.label}</span>
                  <strong>{clarifyCheckpoint.title}</strong>
                  <p>{focusQuestion}</p>
                  <span className="touchpoint-state">{statusLabel(clarifyCheckpoint.state)}</span>
                  <div className="choice-list">
                    {CLARIFICATION_CHOICES.map((choice, index) => (
                      <button
                        key={choice}
                        type="button"
                        className="choice-chip"
                        onClick={() =>
                          void submitReview(
                            "reasoning",
                            index === 2 ? "request_changes" : "approve",
                            choice,
                          )
                        }
                        disabled={isStreaming || actionPending !== null || !run || !canApproveReasoning}
                      >
                        {choice}
                      </button>
                    ))}
                  </div>
                </article>

                <article className={`touchpoint final ${mappingCheckpoint.state}`}>
                  <span className="touchpoint-kicker">{mappingCheckpoint.label}</span>
                  <strong>{mappingCheckpoint.title}</strong>
                  <p>{mappingCheckpoint.description}</p>
                  <span className="touchpoint-state">{statusLabel(mappingCheckpoint.state)}</span>
                  <div className="touchpoint-actions">
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => void submitReview("mappings", "approve", "Operator approved the mapping package from the UI.")}
                      disabled={isStreaming || actionPending !== null || !run || !canApproveMapping}
                    >
                      {actionPending === "mappings" ? "Submitting..." : "Approve suggestion"}
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void submitReview("mappings", "reject", "Operator rejected the mapping package from the UI.")}
                      disabled={isStreaming || actionPending !== null || !run || !canApproveMapping}
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => void submitReview("mappings", "request_changes", "Operator escalated the mapping package from the UI.")}
                      disabled={isStreaming || actionPending !== null || !run || !canApproveMapping}
                    >
                      Escalate
                    </button>
                  </div>
                </article>
              </div>
            </section>

            <section className="migration-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Migration Gate</span>
                  <h2>Operator-triggered handoff</h2>
                </div>
              </div>

              <div className="migration-card">
                <strong>{migrateVisible ? "Ready for demo migration" : "Blocked until approvals complete"}</strong>
                <p>
                  The backend keeps migration blocked until all three reviews are approved. The current implementation returns a
                  mock migration result for the demo.
                </p>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void triggerMigration()}
                  disabled={isStreaming || actionPending !== null || run?.status !== "migration_ready"}
                >
                  {actionPending === "migrate" ? "Triggering..." : "Trigger mock migration"}
                </button>
                {migrationResult ? (
                  <div className="migration-result">
                    <span className="section-label">Latest result</span>
                    <p>{JSON.stringify(migrationResult.payload ?? {}, null, 2)}</p>
                  </div>
                ) : null}
              </div>
            </section>

            <section className="conversation-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Ask Codex Why</span>
                  <h2>Support chat</h2>
                </div>
                <span className={isStreaming ? "stream-pill active" : "stream-pill"}>
                  {isStreaming ? "Streaming" : "Ready"}
                </span>
              </div>

              <div className="prompt-grid">
                {DATABASE_PROMPTS.map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    className="prompt-chip"
                    onClick={() => void sendPrompt(item.prompt)}
                    disabled={isStreaming}
                  >
                    {item.label}
                  </button>
                ))}
              </div>

              <div className="transcript-panel compact">
                {messages.map((message) => (
                  <article key={message.id} className={message.role === "assistant" ? "message assistant" : "message user"}>
                    <span className="message-role">{message.role === "assistant" ? "Codex" : "Operator"}</span>
                    <p>{message.content || (message.pending ? "..." : "")}</p>
                  </article>
                ))}
                <div ref={transcriptEndRef} />
              </div>

              <form className="composer" onSubmit={handleSubmit}>
                <textarea
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  placeholder="Ask for more evidence, a shorter explanation, or a different candidate comparison..."
                />
                <button type="submit" className="primary-button" disabled={isStreaming || composer.trim().length === 0}>
                  {isStreaming ? "Codex is responding..." : "Send to Codex"}
                </button>
              </form>
            </section>

            <section className="activity-panel">
              <div className="panel-head">
                <div>
                  <span className="section-label">Activity</span>
                  <h2>Recent orchestration events</h2>
                </div>
              </div>

              <div className="activity-list">
                {activity.length > 0 ? (
                  activity.map((item) => (
                    <article key={item.id} className="activity-row">
                      {item.text}
                    </article>
                  ))
                ) : (
                  <article className="activity-row">{demoState.error ?? "Waiting for backend activity."}</article>
                )}
              </div>
            </section>
          </aside>
        </section>
      </section>
    </main>
  );
}
