import type { ReactNode } from "react";
import { reviewWorkspaceMock as data } from "./review-workspace.mock";

const tone = {
  good: "border-emerald-300/20 bg-emerald-300/10 text-emerald-200",
  warn: "border-amber-300/20 bg-amber-300/10 text-amber-200",
  bad: "border-rose-300/20 bg-rose-300/10 text-rose-200",
};

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-[1520px] flex-1 flex-col gap-4 p-4 md:p-6">
      <section className="rounded-[30px] border border-white/10 bg-[rgba(8,16,28,0.84)] shadow-[0_30px_90px_rgba(0,0,0,0.34)] backdrop-blur">
        <header className="grid gap-4 border-b border-white/10 px-5 py-5 md:grid-cols-[1.5fr_auto] md:px-7">
          <div>
            <div className="mb-2 inline-flex rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-200">Review Workspace</div>
            <h1 className="max-w-3xl text-3xl font-semibold tracking-[-0.04em] text-white md:text-[2.35rem]">Human arbitration for ambiguous migration mappings</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-[color:var(--muted)]">The backend passes Codex context, evidence, proposed options, and queue state into this surface so the implementation lead can make the canonical decision that controls package readiness.</p>
          </div>
          <div className="flex flex-wrap items-start gap-2 md:justify-end">
            <div className="min-w-60 rounded-[18px] border border-emerald-300/20 bg-white/5 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted)]">Current Milestone</div>
              <div className="mt-1 text-[22px] font-extrabold tracking-[-0.03em] text-white">{data.summary.readinessLabel}</div>
              <div className="mt-1 text-sm leading-5 text-[color:var(--subtle)]">{data.summary.unresolvedDecisionCount} arbitration decisions remain before package handoff.</div>
            </div>
            <Badge label="Merged Source" tone="warn" />
            <Badge label="Oracle Connected" />
            <Badge label="Target: Supabase" />
          </div>
        </header>

        <section className="grid gap-4 p-4 md:grid-cols-[1.45fr_.9fr] md:p-5">
          <div className="rounded-[24px] border border-white/10 bg-[rgba(14,26,41,0.96)] p-4">
            <div className="mb-3 flex items-baseline justify-between gap-3"><h2 className="text-xl font-semibold tracking-[-0.03em] text-white">Migration Context</h2><span className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--subtle)]">Compressed view</span></div>
            <div className="grid gap-3 lg:grid-cols-[1.35fr_auto]">
              <div>
                <div className="rounded-2xl border border-white/10 bg-[rgba(18,33,52,0.82)] px-4 py-3"><strong className="block text-[15px] text-white">{data.summary.sourceSystemLabel} is mapped into one review case.</strong><p className="mt-1 text-sm leading-6 text-[color:var(--muted)]">{data.context.narrative}</p></div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Schemas" value="3" copy="1 review case" /><Metric label="Flagged tables" value="18" copy="6 overlap on customer meaning" /><Metric label="Open conflicts" value="12" copy="2 need human arbitration now" /><Metric label="Last scan" value="09:14" copy="Codex summary refreshed" /></div>
              </div>
              <div className="min-w-[280px] rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.88)] p-3">
                <div className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted)]">Source Network</div>
                <div className="mt-2 rounded-2xl border border-white/10 bg-[rgba(17,31,48,0.65)] px-3 py-4">{data.context.sourceNetwork.nodes.map((node) => <div key={node.id} className="mb-2 last:mb-0 text-sm text-white">{node.label} <span className="text-[color:var(--muted)]">· {node.caption}</span></div>)}</div>
                <p className="mt-2 text-xs leading-5 text-[color:var(--muted)]">Small topology context keeps the source story visible without dominating the page.</p>
              </div>
            </div>
          </div>

          <div className="rounded-[24px] border border-white/10 bg-[rgba(14,26,41,0.96)] p-4">
            <div className="mb-3 flex items-baseline justify-between gap-3"><h2 className="text-xl font-semibold tracking-[-0.03em] text-white">Progress</h2><span className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--subtle)]">Operator state</span></div>
            <div className="rounded-2xl border border-white/10 bg-[rgba(18,33,52,0.78)] px-4 py-3"><strong className="block text-[15px] text-white">Codex has finished interpretation and raised only the mappings that still need human judgement.</strong><p className="mt-1 text-sm leading-6 text-[color:var(--muted)]">Everything else here is about clearing readiness blockers, not running the migration itself.</p><div className="mt-3 flex flex-wrap gap-2"><Badge label={`${data.summary.autoResolvedCount} auto-cleared`} /><Badge label={`${data.summary.unresolvedDecisionCount} reviews open`} tone="warn" /></div></div>
          </div>
        </section>

        <section className="p-4 pt-0 md:p-5 md:pt-0">
          <div className="rounded-[24px] border border-white/10 bg-[rgba(15,28,45,0.96)] p-4">
            <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><h2 className="text-2xl font-semibold tracking-[-0.03em] text-white">Review Workspace</h2><div className="inline-flex w-fit rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-amber-200">Core decision in focus</div></div>
            <div className="grid gap-4 xl:grid-cols-[0.92fr_1.18fr_0.9fr]">
              <section className="grid gap-3">
                <Panel title="Codex Context" eyebrow="Why this field is ambiguous"><p className="text-sm leading-6 text-[color:var(--muted)]">Codex sees the same code family reused across inherited systems with different implied ownership and lifecycle meaning after the merger.</p><div className="flex flex-wrap gap-2">{data.context.conflictThemes.map((theme) => <Badge key={theme} label={theme} />)}</div></Panel>
                <Panel title="Evidence" eyebrow="Signals passed from backend" subtle>{data.evidence.map((item) => <article key={item.evidenceId} className="rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.76)] p-3"><div className="font-mono text-[11px] text-[color:var(--subtle)]">{item.sourceLabel}</div><div className="mt-1 flex items-center justify-between gap-3"><strong className="text-[13px] text-white">{item.title}</strong><span className="text-[11px] font-semibold uppercase text-emerald-200">{item.weight}</span></div><p className="mt-1 text-sm leading-6 text-[color:var(--muted)]">{item.summary}</p></article>)}</Panel>
                <Panel title="Nearby mappings" eyebrow="Decision adjacency" subtle>{data.nearbyMappings.map((mapping) => <article key={mapping.mappingId} className="grid gap-2 rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.76)] p-3 md:grid-cols-[1fr_auto]"><div><div className="text-sm font-semibold text-white">{mapping.sourceField}</div><div className="mt-1 font-mono text-[11px] text-[color:var(--subtle)]">{mapping.sourcePath}</div><div className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{mapping.summary}</div></div><Badge label={String(mapping.status).replace('_', ' ')} tone={mapping.status === 'auto_resolved' ? 'good' : 'warn'} /></article>)}</Panel>
              </section>

              <section className="rounded-[20px] border border-amber-300/20 bg-[linear-gradient(180deg,rgba(241,197,111,0.12),rgba(16,31,51,0.92))] p-5">
                <div className="mb-2 text-[11px] uppercase tracking-[0.16em] text-amber-200">Active Arbitration</div>
                <h3 className="text-[1.65rem] font-semibold tracking-[-0.03em] text-white">{data.activeDecision.title}</h3>
                <p className="mt-2 text-sm leading-7 text-[color:var(--muted)]">{data.activeDecision.rationale}</p>
                <div className="mt-4 rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.38)] p-4"><div className="font-mono text-[11px] text-[color:var(--subtle)]">{data.activeDecision.sourceField.path}</div><div className="mt-1 text-base font-semibold text-white">{data.activeDecision.sourceField.fieldName}</div><div className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{data.activeDecision.sourceField.description}</div><div className="mt-3 rounded-2xl border border-emerald-300/15 bg-emerald-300/10 px-3 py-3 text-sm leading-6 text-emerald-100">{data.activeDecision.impactSummary}</div></div>
                <div className="mt-4 grid gap-3">{data.activeDecision.options.map((option) => <article key={option.optionId} className={`rounded-2xl border p-4 ${option.recommendation === "recommended" ? "border-emerald-300/20 bg-emerald-300/10" : "border-white/10 bg-[rgba(8,16,29,0.72)]"}`}><div className="flex flex-wrap items-center justify-between gap-3"><div><strong className="block text-[15px] text-white">{option.label}</strong><div className="mt-1 font-mono text-[11px] text-[color:var(--subtle)]">target field: {option.targetField}</div></div><Badge label={option.recommendation} tone={option.recommendation === "recommended" ? "good" : "warn"} /></div><p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{option.rationale}</p><ul className="mt-3 grid gap-2 text-sm leading-6 text-[color:var(--muted)]">{option.consequences.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-2 w-2 rounded-full bg-[color:var(--accent)]" /><span>{item}</span></li>)}</ul></article>)}</div>
                <div className="mt-5 flex flex-wrap gap-2">{data.activeDecision.actions.map((action, index) => <button key={action.actionId} type="button" className={index === 0 ? "rounded-full bg-[linear-gradient(135deg,rgba(105,216,193,0.96),rgba(150,203,255,0.88))] px-4 py-3 text-sm font-semibold text-slate-950" : "rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white"}>{action.label}</button>)}</div>
              </section>

              <section className="grid gap-3">
                <Panel title="Queue" eyebrow="What is waiting">{data.queue.map((item) => <article key={item.queueItemId} className="rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.76)] p-3"><div className="flex items-start justify-between gap-3"><strong className="text-[13px] text-white">{item.title}</strong><Badge label={item.state} tone={item.state === "queued" ? "good" : "warn"} /></div><p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{item.summary}</p></article>)}</Panel>
                <Panel title="Outcome snapshot" eyebrow="What this decision affects" subtle><div className="grid gap-3 sm:grid-cols-2">{data.outcomes.map((outcome) => <article key={outcome.outcomeId} className="rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.76)] p-3"><strong className="block text-[1.15rem] text-white">{outcome.value}</strong><div className="mt-1 text-sm font-semibold text-white">{outcome.label}</div><p className="mt-1 text-sm leading-6 text-[color:var(--muted)]">{outcome.summary}</p></article>)}</div></Panel>
                <Panel title="Decision note" eyebrow="Reviewer input" subtle><p className="text-sm leading-6 text-[color:var(--muted)]">{data.reviewerNote.placeholder}</p><div className="grid gap-2 rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.72)] p-3"><div className="h-3 rounded-full bg-white/10" /><div className="h-3 w-[78%] rounded-full bg-white/10" /><div className="h-3 w-[62%] rounded-full bg-white/10" /></div></Panel>
              </section>
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function Badge({ label, tone: kind = "neutral" }: { label: string; tone?: "good" | "warn" | "bad" | "neutral" }) {
  const toneClass = kind === "good" ? tone.good : kind === "warn" ? tone.warn : kind === "bad" ? tone.bad : "border-white/10 bg-white/5 text-[color:var(--muted)]";
  return <span className={`inline-flex rounded-full border px-3 py-2 text-[11px] font-semibold ${toneClass}`}>{label}</span>;
}

function Metric({ label, value, copy }: { label: string; value: string; copy: string }) {
  return <article className="rounded-2xl border border-white/10 bg-[rgba(9,18,31,0.72)] p-3"><div className="text-[11px] uppercase tracking-[0.12em] text-[color:var(--subtle)]">{label}</div><div className="mt-1 text-[20px] font-extrabold tracking-[-0.03em] text-white">{value}</div><div className="mt-1 text-xs leading-5 text-[color:var(--muted)]">{copy}</div></article>;
}

function Panel({ title, eyebrow, subtle, children }: { title: string; eyebrow: string; subtle?: boolean; children: ReactNode }) {
  return <section className={`rounded-[18px] border p-4 ${subtle ? "border-white/10 bg-[rgba(9,18,31,0.82)]" : "border-white/10 bg-[rgba(18,33,52,0.82)]"}`}><div className="mb-3 text-[11px] uppercase tracking-[0.14em] text-[color:var(--subtle)]">{eyebrow}</div><h3 className="mb-2 text-base font-semibold text-white">{title}</h3><div className="grid gap-3">{children}</div></section>;
}
