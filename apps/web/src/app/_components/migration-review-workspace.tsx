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

type ChatRole = "user" | "assistant";
type CheckpointState = "pending" | "approved" | "needs_input" | "escalated" | "rejected";
type GraphPhase = "crawl" | "shape" | "reason" | "question" | "mapping";

type Message = {
  id: string;
  role: ChatRole;
  content: string;
  pending?: boolean;
};

type Checkpoint = {
  id: string;
  label: string;
  title: string;
  description: string;
  state: CheckpointState;
};

type ActivityItem = {
  id: string;
  text: string;
};

const SOURCE_FIELD = "oracle.crm_customer.status_cd";
const RECOMMENDED_TARGET = "public.customer_status";
const ALTERNATIVE_TARGET = "public.account_state";
const SEMANTIC_CONCEPT = "Customer standing";

const INITIAL_MESSAGES: Message[] = [
  {
    id: "m-1",
    role: "assistant",
    content: `I recommend mapping ${SOURCE_FIELD} to ${RECOMMENDED_TARGET}. I found stronger customer-level evidence than account-lifecycle evidence, but I still need your checkpoint approvals.`,
  },
  {
    id: "m-2",
    role: "assistant",
    content:
      "The graph already contains the source field, the proposed semantic concept, and two candidate targets. Review the structure first, then answer the ambiguity question, then approve or reject the mapping.",
  },
];

const INITIAL_CHECKPOINTS: Checkpoint[] = [
  {
    id: "structure",
    label: "Checkpoint 1",
    title: "Approve discovered structure",
    description:
      "Confirm that the source field belongs in the customer-status reasoning path before Codex hardens the graph.",
    state: "needs_input",
  },
  {
    id: "clarify",
    label: "Checkpoint 2",
    title: "Resolve the ambiguity",
    description:
      "Codex needs one human answer on whether `status_cd` reflects customer standing or account lifecycle in the merged flow.",
    state: "pending",
  },
  {
    id: "mapping",
    label: "Checkpoint 3",
    title: "Approve the suggestion",
    description:
      "Accept, reject, or escalate the recommended target mapping after the evidence is clear enough to trust.",
    state: "pending",
  },
];

const DATABASE_PROMPTS = [
  {
    label: "Explain evidence",
    prompt: `Explain briefly why ${SOURCE_FIELD} is better aligned with ${RECOMMENDED_TARGET} than ${ALTERNATIVE_TARGET}.`,
  },
  {
    label: "Show join clues",
    prompt:
      "Show the strongest join clues between the Oracle source tables and the Supabase customer model.",
  },
  {
    label: "Ask the blocker",
    prompt:
      "Ask the single most important human clarification question you still need for this mapping decision.",
  },
  {
    label: "Compare mappings",
    prompt: `Compare ${RECOMMENDED_TARGET} and ${ALTERNATIVE_TARGET} for this source field in one short decision memo.`,
  },
  {
    label: "Prepare package",
    prompt: "Prepare a short migration-ready package summary based on the current checkpoint state.",
  },
];

const CLARIFICATION_CHOICES = [
  "This code is customer-level standing",
  "This code is account lifecycle",
  "Both meanings exist, escalate it",
];

async function loadProbe(): Promise<BackendProbe> {
  const response = await fetch("/api/backend/health", { cache: "no-store" });
  const data = (await response.json()) as BackendProbe & { error?: string };
  if (!response.ok) {
    throw new Error(data.error ?? "Backend probe failed.");
  }
  return data;
}

function createId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function statusLabel(state: CheckpointState): string {
  if (state === "approved") return "Approved";
  if (state === "needs_input") return "Needs input";
  if (state === "escalated") return "Escalated";
  if (state === "rejected") return "Rejected";
  return "Queued";
}

export function MigrationReviewWorkspace() {
  const [probeState, setProbeState] = useState<ProbeState>({
    data: null,
    error: null,
    loading: true,
  });
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>(INITIAL_CHECKPOINTS);
  const [activity, setActivity] = useState<ActivityItem[]>([
    { id: "a-1", text: `Codex suggested ${RECOMMENDED_TARGET} as the primary target for ${SOURCE_FIELD}.` },
    { id: "a-2", text: `A second candidate, ${ALTERNATIVE_TARGET}, remains visible in the graph as the fallback.` },
  ]);
  const [composer, setComposer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [graphPhase, setGraphPhase] = useState<GraphPhase>("shape");
  const [graphScore, setGraphScore] = useState(68);
  const [focusQuestion, setFocusQuestion] = useState(
    "Does `status_cd` represent customer standing or account lifecycle in the merged finance flow?",
  );
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
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) {
      return;
    }

    const nodes = graph.querySelectorAll(".graph-node");
    const links = graph.querySelectorAll(".graph-link");
    const highlight = graph.querySelector(".graph-highlight");

    const timeline = gsap.timeline();
    timeline
      .fromTo(
        nodes,
        { scale: 0.84, opacity: 0.3, y: 14 },
        {
          scale: 1,
          opacity: 1,
          y: 0,
          duration: 0.65,
          stagger: 0.08,
          ease: "power2.out",
        },
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
  }, [graphPhase]);

  const backendLabel = useMemo(() => {
    if (probeState.loading && !probeState.data) return "Connecting";
    if (probeState.error) return "Backend offline";
    if (probeState.data?.ok) return "Backend live";
    return "Pending";
  }, [probeState.data, probeState.error, probeState.loading]);

  const progressLabel = useMemo(() => {
    if (graphPhase === "crawl") return "Reading source structure";
    if (graphPhase === "shape") return "Suggestion assembled";
    if (graphPhase === "reason") return "Evidence re-ranked";
    if (graphPhase === "question") return "Waiting on human answer";
    return "Mapping ready for package";
  }, [graphPhase]);

  const structureCheckpoint = checkpoints.find((checkpoint) => checkpoint.id === "structure");
  const clarifyCheckpoint = checkpoints.find((checkpoint) => checkpoint.id === "clarify");
  const mappingCheckpoint = checkpoints.find((checkpoint) => checkpoint.id === "mapping");

  const evidenceItems = useMemo(
    () => [
      "The source field clusters with customer profile attributes instead of account-ledger transitions.",
      "Observed value semantics match active, paused, and churned customer states more closely than account-state transitions.",
    ],
    [],
  );

  const candidateMappings = useMemo(
    () => [
      {
        id: "primary",
        title: RECOMMENDED_TARGET,
        score: "91%",
        tone: "recommended",
        note: "Best semantic fit for the current evidence set. This is the AI suggestion you can approve.",
      },
      {
        id: "secondary",
        title: ALTERNATIVE_TARGET,
        score: "63%",
        tone: "alternative",
        note: "Still plausible, but the evidence points more toward customer standing than lifecycle state.",
      },
    ],
    [],
  );

  function pushActivity(text: string) {
    setActivity((current) => [{ id: createId("activity"), text }, ...current].slice(0, 6));
  }

  function setCheckpointState(id: string, nextState: CheckpointState) {
    setCheckpoints((current) =>
      current.map((checkpoint) =>
        checkpoint.id === id ? { ...checkpoint, state: nextState } : checkpoint,
      ),
    );
  }

  function applyAction(action: string) {
    if (action === "approve_mapping") {
      setCheckpointState("mapping", "approved");
      setGraphPhase("mapping");
      setGraphScore(94);
      pushActivity("Final mapping checkpoint approved and the recommended target locked into the graph.");
      return;
    }
    if (action === "reject_mapping") {
      setCheckpointState("mapping", "rejected");
      setGraphScore(58);
      pushActivity("Final mapping checkpoint rejected; the alternative path remains visible.");
      return;
    }
    if (action === "draft_reviewer_note") {
      pushActivity("Codex drafted a reviewer note summarizing the current evidence.");
      return;
    }
    if (action === "rerun_reasoning") {
      setGraphPhase("reason");
      setGraphScore((score) => Math.min(score + 6, 88));
      pushActivity("Codex reran semantic reasoning and refreshed the candidate ranking.");
      return;
    }
    if (action === "prepare_package") {
      setGraphPhase("mapping");
      pushActivity("Codex prepared the package summary for downstream migration planning.");
    }
  }

  async function sendPrompt(prompt: string, requestedAction?: string) {
    const trimmed = prompt.trim();
    if (!trimmed || isStreaming) {
      return;
    }

    const userMessage: Message = { id: createId("user"), role: "user", content: trimmed };
    const assistantId = createId("assistant");

    setMessages((current) => [
      ...current,
      userMessage,
      { id: assistantId, role: "assistant", content: "", pending: true },
    ]);
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
            project_id: "oracle-supabase-demo",
            run_id: "run-demo-001",
            case_id: "case-customer-meaning",
            selected_mapping_id: "status_cd->customer_status",
            requested_action: requestedAction ?? null,
            available_actions: [
              "explain_mapping",
              "compare_alternatives",
              "draft_reviewer_note",
              "approve_mapping",
              "reject_mapping",
              "rerun_reasoning",
              "prepare_package",
            ],
            ui_state: {
              graphPhase,
              graphScore,
              checkpoints,
              focusQuestion,
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
          const eventType =
            lines.find((line) => line.startsWith("event:"))?.slice(6).trim() ?? "message";
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
                  message.id === assistantId
                    ? { ...message, content: `${message.content}${delta}` }
                    : message,
                ),
              );
            }
          }

          if (eventType === "tool_action" && typeof parsed.action === "string") {
            applyAction(parsed.action);
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
      pushActivity("Codex stream failed and the case remains interactive.");
    } finally {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId ? { ...message, pending: false } : message,
        ),
      );
      setIsStreaming(false);
    }
  }

  function handleStructureDecision(approve: boolean) {
    setCheckpointState("structure", approve ? "approved" : "needs_input");
    setCheckpointState("clarify", "needs_input");
    setGraphPhase(approve ? "question" : "crawl");
    setGraphScore(approve ? 74 : 46);
    pushActivity(
      approve
        ? "Human approved the structure checkpoint and unlocked the ambiguity question."
        : "Human requested a structure rescan before accepting the suggestion.",
    );
    void sendPrompt(
      approve
        ? "The operator approved the discovered structure. Ask the next ambiguity question briefly."
        : "The operator requested another structure pass. Explain what should be rechecked in the source and target structures.",
    );
  }

  function answerClarification(choice: string) {
    setCheckpointState("clarify", "approved");
    setCheckpointState("mapping", "needs_input");
    setGraphPhase("reason");
    setGraphScore(choice.includes("customer-level") ? 89 : 67);
    setFocusQuestion(`Operator answer captured: ${choice}`);
    pushActivity(`Human answered the ambiguity checkpoint: ${choice}`);
    void sendPrompt(
      `The operator answered the ambiguity checkpoint with: ${choice}. Refresh the recommendation and keep the explanation short.`,
    );
  }

  function handleMappingDecision(action: "approve" | "reject" | "escalate") {
    if (action === "approve") {
      setCheckpointState("mapping", "approved");
      setGraphPhase("mapping");
      setGraphScore(95);
      pushActivity("Human approved the AI suggestion and locked the primary mapping.");
      void sendPrompt(
        "The operator approved the final mapping recommendation. Summarize what is now approved and ready.",
        "approve_mapping",
      );
      return;
    }

    if (action === "reject") {
      setCheckpointState("mapping", "rejected");
      setGraphScore(57);
      pushActivity("Human rejected the AI suggestion and kept the case open.");
      void sendPrompt(
        "The operator rejected the final mapping recommendation. Explain the safest alternative in one short paragraph.",
        "reject_mapping",
      );
      return;
    }

    setCheckpointState("mapping", "escalated");
    pushActivity("Human escalated the AI suggestion for deeper review.");
    void sendPrompt(
      "The operator escalated the mapping. Draft a short escalation brief with unresolved semantic risk.",
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendPrompt(composer);
  }

  return (
    <main className="orchestrator-page">
      <section className="orchestrator-shell">
        <header className="hero-strip">
          <div>
            <span className="eyebrow">Suggestion-First Review</span>
            <h1>The AI suggestion comes first. The human approves it through explicit semantic checkpoints.</h1>
            <p className="subhead">
              Codex proposes a mapping, shows compact evidence, visualizes the competing targets in the context graph, and then
              asks for human touchpoints in the order the demo needs.
            </p>
          </div>
          <div className="status-stack">
            <div className="status-card">
              <div className="status-kicker">Current state</div>
              <strong>{progressLabel}</strong>
              <span>Backend: {backendLabel}</span>
            </div>
            <div className="status-chips">
              <span className="status-chip">Source field live</span>
              <span className="status-chip">Two target candidates</span>
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
                  <h2>{SOURCE_FIELD} → {RECOMMENDED_TARGET}</h2>
                </div>
                <span className="stream-pill active-soft">{mappingCheckpoint ? statusLabel(mappingCheckpoint.state) : "In review"}</span>
              </div>

              <div className="suggestion-summary">
                <div className="summary-core">
                  <div className="mapping-pill recommended">Recommended target</div>
                  <strong>{SEMANTIC_CONCEPT}</strong>
                  <p>
                    Codex believes this source field most likely describes a customer-level standing concept, not an account
                    lifecycle transition.
                  </p>
                </div>
                <div className="confidence-card">
                  <span>Confidence</span>
                  <strong>91%</strong>
                  <p>Low structural risk, medium semantic ambiguity until the human answers the checkpoint question.</p>
                </div>
              </div>

              <div className="evidence-list">
                {evidenceItems.map((item) => (
                  <article key={item} className="evidence-card">
                    <span className="evidence-kicker">Brief evidence</span>
                    <p>{item}</p>
                  </article>
                ))}
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
                      <span>{SOURCE_FIELD}</span>
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
                  <h2>Source field, semantic concept, and two target mappings</h2>
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
                  <strong>{SOURCE_FIELD}</strong>
                  <span>Source field</span>
                </div>
                <div className="graph-node oracle node-b">
                  <strong>oracle.fin_account.status_cd</strong>
                  <span>Related field family</span>
                </div>
                <div className="graph-node semantic node-c">
                  <strong>{SEMANTIC_CONCEPT}</strong>
                  <span>Suggested ontology concept</span>
                </div>
                <div className="graph-node target recommended node-e">
                  <strong>{RECOMMENDED_TARGET}</strong>
                  <span>Primary target mapping</span>
                </div>
                <div className="graph-node target node-f">
                  <strong>{ALTERNATIVE_TARGET}</strong>
                  <span>Fallback target mapping</span>
                </div>
              </div>

              <div className="graph-caption">
                The thicker path shows the currently recommended mapping. The secondary path stays visible so the human can judge
                whether the AI should be approved or redirected.
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
                <article className={`touchpoint ${structureCheckpoint?.state ?? "pending"}`}>
                  <span className="touchpoint-kicker">{structureCheckpoint?.label}</span>
                  <strong>{structureCheckpoint?.title}</strong>
                  <p>{structureCheckpoint?.description}</p>
                  <span className="touchpoint-state">{structureCheckpoint ? statusLabel(structureCheckpoint.state) : "Queued"}</span>
                  <div className="touchpoint-actions">
                    <button type="button" className="secondary-button" onClick={() => handleStructureDecision(true)} disabled={isStreaming}>
                      Approve structure
                    </button>
                    <button type="button" className="ghost-button" onClick={() => handleStructureDecision(false)} disabled={isStreaming}>
                      Request rescan
                    </button>
                  </div>
                </article>

                <article className={`touchpoint ${clarifyCheckpoint?.state ?? "pending"}`}>
                  <span className="touchpoint-kicker">{clarifyCheckpoint?.label}</span>
                  <strong>{clarifyCheckpoint?.title}</strong>
                  <p>{focusQuestion}</p>
                  <span className="touchpoint-state">{clarifyCheckpoint ? statusLabel(clarifyCheckpoint.state) : "Queued"}</span>
                  <div className="choice-list">
                    {CLARIFICATION_CHOICES.map((choice) => (
                      <button key={choice} type="button" className="choice-chip" onClick={() => answerClarification(choice)} disabled={isStreaming}>
                        {choice}
                      </button>
                    ))}
                  </div>
                </article>

                <article className={`touchpoint final ${mappingCheckpoint?.state ?? "pending"}`}>
                  <span className="touchpoint-kicker">{mappingCheckpoint?.label}</span>
                  <strong>{mappingCheckpoint?.title}</strong>
                  <p>{mappingCheckpoint?.description}</p>
                  <span className="touchpoint-state">{mappingCheckpoint ? statusLabel(mappingCheckpoint.state) : "Queued"}</span>
                  <div className="touchpoint-actions">
                    <button type="button" className="primary-button" onClick={() => handleMappingDecision("approve")} disabled={isStreaming}>
                      Approve suggestion
                    </button>
                    <button type="button" className="ghost-button" onClick={() => handleMappingDecision("reject")} disabled={isStreaming}>
                      Reject
                    </button>
                    <button type="button" className="ghost-button" onClick={() => handleMappingDecision("escalate")} disabled={isStreaming}>
                      Escalate
                    </button>
                  </div>
                </article>
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
                {activity.map((item) => (
                  <article key={item.id} className="activity-row">
                    {item.text}
                  </article>
                ))}
              </div>
            </section>
          </aside>
        </section>
      </section>
    </main>
  );
}
