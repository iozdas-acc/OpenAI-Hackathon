#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / "reports" / "ralph-backend"
RUNS_DIR = REPORTS_DIR / "runs"
LATEST_DIR = REPORTS_DIR / "latest"
LOCK_PATH = REPORTS_DIR / ".lock"

BACKEND_TARGETS = [
    ROOT_DIR / "apps" / "api",
    ROOT_DIR / "services" / "orchestrator",
    ROOT_DIR / "services" / "crawlers",
    ROOT_DIR / "services" / "migration",
    ROOT_DIR / "services" / "context_graph_builder.py",
]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".next",
    ".data",
    "node_modules",
    "__pycache__",
}


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    title: str
    path: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "path": self.path,
            "detail": self.detail,
        }


RuleCheck = Callable[[str, str], Optional[Finding]]


@dataclass(frozen=True)
class Rule:
    rule_id: str
    check: RuleCheck


def main() -> int:
    args = parse_args()
    ensure_output_dirs()

    with loop_lock():
        while True:
            run_once(args.interval_minutes)
            if args.once:
                return 0
            time.sleep(max(args.interval_minutes, 1) * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Ralph backend review loop.")
    parser.add_argument("--interval-minutes", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def ensure_output_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_DIR.mkdir(parents=True, exist_ok=True)


class loop_lock:
    def __enter__(self) -> "loop_lock":
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if LOCK_PATH.exists():
            if _lock_is_stale(LOCK_PATH):
                LOCK_PATH.unlink()
            else:
                raise SystemExit("Ralph loop is already running.")

        payload = {
            "pid": os.getpid(),
            "started_at": utcnow(),
        }
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(str(LOCK_PATH), flags)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if LOCK_PATH.exists():
                LOCK_PATH.unlink()
        except OSError:
            pass


def _lock_is_stale(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return True

    pid = payload.get("pid")
    if not isinstance(pid, int):
        return True

    try:
        os.kill(pid, 0)
    except OSError:
        return True
    return False


def run_once(interval_minutes: int) -> None:
    started = utcnow()
    run_id, run_dir = next_run_target()
    run_dir.mkdir(parents=True, exist_ok=False)

    previous_meta = load_previous_meta()
    failure_stage = "initializing"

    try:
        failure_stage = "collecting_files"
        collected = collect_backend_files()
        flattened_text = build_flattened_snapshot(collected)
        file_hashes = {item["path"]: item["sha256"] for item in collected}
        changed_files = diff_files(previous_meta, file_hashes)

        failure_stage = "reviewing_backend"
        findings = run_review(collected)
        finding_counts = summarize_findings(findings)
        recurring_ids, resolved_ids, new_ids = compare_findings(previous_meta, findings)
        status = status_from_findings(findings)

        flattened_path = run_dir / "flattened-backend.txt"
        review_path = run_dir / "review.md"
        meta_path = run_dir / "meta.json"

        failure_stage = "writing_artifacts"
        flattened_path.write_text(flattened_text, encoding="utf-8")
        review_path.write_text(
            render_review(
                run_id=run_id,
                started_at=started,
                completed_at=utcnow(),
                interval_minutes=interval_minutes,
                included_files=[item["path"] for item in collected],
                changed_files=changed_files,
                findings=findings,
                recurring_ids=recurring_ids,
                resolved_ids=resolved_ids,
                new_ids=new_ids,
                status=status,
            ),
            encoding="utf-8",
        )
        meta = {
            "run_id": run_id,
            "started_at": started,
            "completed_at": utcnow(),
            "interval_minutes": interval_minutes,
            "included_files": [item["path"] for item in collected],
            "excluded_patterns": sorted(EXCLUDED_PARTS),
            "changed_files": changed_files,
            "finding_counts": finding_counts,
            "status": status,
            "file_hashes": file_hashes,
            "findings": [finding.to_dict() for finding in findings],
            "recurring_findings": recurring_ids,
            "resolved_findings": resolved_ids,
            "new_findings": new_ids,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        refresh_latest(flattened_path, review_path, meta_path)
    except Exception as exc:
        failure_meta = {
            "run_id": run_id,
            "started_at": started,
            "completed_at": utcnow(),
            "interval_minutes": interval_minutes,
            "included_files": [],
            "excluded_patterns": sorted(EXCLUDED_PARTS),
            "changed_files": [],
            "finding_counts": {"high": 0, "medium": 0, "low": 0},
            "status": "failed",
            "error": str(exc),
            "failure_stage": failure_stage,
            "findings": [],
        }
        (run_dir / "review.md").write_text(
            render_failure_review(run_id=run_id, failure_stage=failure_stage, error=str(exc)),
            encoding="utf-8",
        )
        (run_dir / "meta.json").write_text(json.dumps(failure_meta, indent=2), encoding="utf-8")
        (run_dir / "flattened-backend.txt").write_text("", encoding="utf-8")
        refresh_latest(
            run_dir / "flattened-backend.txt",
            run_dir / "review.md",
            run_dir / "meta.json",
        )


def load_previous_meta() -> Dict[str, Any]:
    meta_path = LATEST_DIR / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def collect_backend_files() -> List[Dict[str, str]]:
    collected: List[Dict[str, str]] = []
    for target in BACKEND_TARGETS:
        if not target.exists():
            continue
        if target.is_file():
            item = read_file_record(target)
            if item is not None:
                collected.append(item)
            continue

        for path in sorted(target.rglob("*")):
            if path.is_dir() or should_exclude(path):
                continue
            item = read_file_record(path)
            if item is not None:
                collected.append(item)
    collected.sort(key=lambda item: item["path"])
    return collected


def should_exclude(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def read_file_record(path: Path) -> Optional[Dict[str, str]]:
    relative_path = path.relative_to(ROOT_DIR).as_posix()
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return {
        "path": relative_path,
        "content": content,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def build_flattened_snapshot(collected: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for item in collected:
        parts.append("===== FILE: {path} =====\n{content}".format(**item))
    return "\n\n".join(parts).rstrip() + "\n"


def diff_files(previous_meta: Dict[str, Any], current_hashes: Dict[str, str]) -> List[str]:
    previous_hashes = previous_meta.get("file_hashes", {}) or {}
    changed = [
        path
        for path, digest in current_hashes.items()
        if previous_hashes.get(path) != digest
    ]
    return sorted(changed)


def run_review(collected: List[Dict[str, str]]) -> List[Finding]:
    findings: List[Finding] = []
    rule_set = rules()

    for item in collected:
        path = item["path"]
        content = item["content"]
        for rule in rule_set:
            finding = rule.check(path, content)
            if finding is not None:
                findings.append(finding)

    findings.extend(run_compile_checks(collected))
    if backend_tests_missing():
        findings.append(
            Finding(
                id="missing-backend-tests",
                severity="medium",
                title="Backend review targets are missing automated tests",
                path="apps/api services/orchestrator services/crawlers services/migration",
                detail=(
                    "No backend-focused test modules were found under the reviewed surfaces, so the "
                    "Ralph loop can report recurring issues but cannot validate regressions automatically."
                ),
            )
        )

    return dedupe_findings(findings)


def rules() -> List[Rule]:
    return [
        Rule("migration-stuck-status", check_migration_stuck_status),
        Rule("live-dict-values-view", check_live_dict_values_view),
        Rule("started-at-reset", check_started_at_reset),
        Rule("unsanitized-upload-filename", check_unsanitized_upload_filename),
        Rule("brittle-openai-parser", check_brittle_openai_parser),
        Rule("unsafe-json-loads", check_unsafe_json_loads),
        Rule("sample-row-leak", check_sample_row_leak),
        Rule("mapping-count-dict-bug", check_mapping_count_dict_bug),
        Rule("oracle-arbitrary-path-read", check_oracle_arbitrary_path_read),
    ]


def check_migration_stuck_status(path: str, content: str) -> Optional[Finding]:
    if path != "apps/api/main.py":
        return None
    if "store.update_run_status(run_id, status=RunStatus.MIGRATING.value)" in content and "if execute_supabase_migration is None:" in content:
        return Finding(
            id="migration-stuck-status",
            severity="high",
            title="Migration failures can leave runs stuck in migrating",
            path=path,
            detail=(
                "The API transitions a run to migrating before verifying the executor import and before "
                "guarding the migration call, so failures can strand the run without a terminal status."
            ),
        )
    return None


def check_live_dict_values_view(path: str, content: str) -> Optional[Finding]:
    if path != "apps/api/app/store.py":
        return None
    if 'records = self._read_dict("runs").values()' in content:
        return Finding(
            id="live-dict-values-view",
            severity="high",
            title="Run listing uses a live dict view outside the store lock",
            path=path,
            detail=(
                "Iterating a dict values view after releasing the lock can raise runtime errors or return "
                "inconsistent results when concurrent writes occur."
            ),
        )
    return None


def check_started_at_reset(path: str, content: str) -> Optional[Finding]:
    if path != "apps/api/app/store.py":
        return None
    if 'started_at = datetime.utcnow() if status == RunStatus.RUNNING.value else None' in content:
        return Finding(
            id="started-at-reset",
            severity="medium",
            title="Run status transitions wipe started_at for non-running states",
            path=path,
            detail=(
                "Completed and failed runs lose their original start timestamp, which breaks duration "
                "tracking and weakens backend auditability."
            ),
        )
    return None


def check_unsanitized_upload_filename(path: str, content: str) -> Optional[Finding]:
    if path != "apps/api/app/store.py":
        return None
    if 'stored_name = "{file_id}_{filename}"' in content:
        return Finding(
            id="unsanitized-upload-filename",
            severity="medium",
            title="Uploaded filenames are written into storage paths without sanitization",
            path=path,
            detail=(
                "A crafted filename can escape the intended upload area or create unstable local file paths "
                "because the store concatenates the raw filename into the saved path."
            ),
        )
    return None


def check_brittle_openai_parser(path: str, content: str) -> Optional[Finding]:
    if path != "services/orchestrator/workflow.py":
        return None
    if "output_text = response_json.get(\"output_text\")" in content and "content_item.get(\"type\")" not in content:
        return Finding(
            id="brittle-openai-parser",
            severity="high",
            title="Orchestrator response parsing assumes a narrow OpenAI payload shape",
            path=path,
            detail=(
                "The parser only checks a small set of response fields, so supported API variations or "
                "wrapped structured output can fail without a durable fallback path."
            ),
        )
    return None


def check_unsafe_json_loads(path: str, content: str) -> Optional[Finding]:
    if path != "services/orchestrator/workflow.py":
        return None
    if "json.loads(candidate)" in content and "JSONDecodeError" not in content:
        return Finding(
            id="unsafe-json-loads",
            severity="high",
            title="Structured output parsing does not preserve context on JSON decode failures",
            path=path,
            detail=(
                "Malformed or wrapped model output will bubble up as a raw JSON decode failure, which makes "
                "recurring contract issues harder to diagnose."
            ),
        )
    return None


def check_sample_row_leak(path: str, content: str) -> Optional[Finding]:
    if path != "services/crawlers/supabase.py":
        return None
    if 'table["sample_rows"] = [dict(row) for row in rows]' in content:
        return Finding(
            id="sample-row-leak",
            severity="high",
            title="Target crawl exports raw sample rows",
            path=path,
            detail=(
                "Sample rows are copied verbatim into crawl output, which creates a direct path for PII and "
                "secret leakage into downstream persistence and review artifacts."
            ),
        )
    return None


def check_mapping_count_dict_bug(path: str, content: str) -> Optional[Finding]:
    if path != "services/migration/supabase.py":
        return None
    if 'getattr(node, "type", "") == "mapping_candidate"' in content:
        return Finding(
            id="mapping-count-dict-bug",
            severity="high",
            title="Migration metrics assume graph nodes are objects instead of dicts",
            path=path,
            detail=(
                "When graph nodes are stored as dictionaries, the current mapping count logic reports zero "
                "candidates and makes migration telemetry misleading."
            ),
        )
    return None


def check_oracle_arbitrary_path_read(path: str, content: str) -> Optional[Finding]:
    if path != "services/crawlers/oracle.py":
        return None
    if "path = Path(path_value)" in content and "read_text" in content:
        return Finding(
            id="oracle-arbitrary-path-read",
            severity="medium",
            title="Oracle preview logic trusts arbitrary file metadata paths",
            path=path,
            detail=(
                "The crawler reads the first line of whatever path is present in file metadata without "
                "confining that path to the upload area."
            ),
        )
    return None


def run_compile_checks(collected: List[Dict[str, str]]) -> List[Finding]:
    findings: List[Finding] = []
    for item in collected:
        path = item["path"]
        if not path.endswith(".py"):
            continue
        try:
            compile(item["content"], path, "exec")
        except SyntaxError as exc:
            findings.append(
                Finding(
                    id="compile-error:{path}".format(path=path),
                    severity="high",
                    title="Python source does not compile",
                    path=path,
                    detail=str(exc),
                )
            )
    return findings


def backend_tests_missing() -> bool:
    test_files = list(ROOT_DIR.glob("tests/test_*.py"))
    test_files.extend(ROOT_DIR.glob("tests/**/*test*.py"))
    return len(list(test_files)) == 0


def dedupe_findings(findings: List[Finding]) -> List[Finding]:
    unique: Dict[str, Finding] = {}
    for finding in findings:
        unique[finding.id] = finding
    ordered = list(unique.values())
    severity_order = {"high": 0, "medium": 1, "low": 2}
    ordered.sort(key=lambda item: (severity_order.get(item.severity, 9), item.path, item.id))
    return ordered


def summarize_findings(findings: List[Finding]) -> Dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return counts


def compare_findings(previous_meta: Dict[str, Any], findings: List[Finding]) -> tuple[List[str], List[str], List[str]]:
    previous = {item["id"] for item in previous_meta.get("findings", []) if isinstance(item, dict) and "id" in item}
    current = {finding.id for finding in findings}
    recurring = sorted(previous & current)
    resolved = sorted(previous - current)
    new = sorted(current - previous)
    return recurring, resolved, new


def status_from_findings(findings: List[Finding]) -> str:
    if any(finding.severity == "high" for finding in findings):
        return "needs_attention"
    if any(finding.severity == "medium" for finding in findings):
        return "watch"
    return "clean"


def render_review(
    run_id: str,
    started_at: str,
    completed_at: str,
    interval_minutes: int,
    included_files: List[str],
    changed_files: List[str],
    findings: List[Finding],
    recurring_ids: List[str],
    resolved_ids: List[str],
    new_ids: List[str],
    status: str,
) -> str:
    lines: List[str] = [
        "# Ralph Backend Review",
        "",
        "Run ID: `{run_id}`".format(run_id=run_id),
        "Started: `{started}`".format(started=started_at),
        "Completed: `{completed}`".format(completed=completed_at),
        "Interval Minutes: `{interval}`".format(interval=interval_minutes),
        "Status: `{status}`".format(status=status),
        "",
        "## Scope",
        "",
        "- Included files: {count}".format(count=len(included_files)),
        "- Excluded patterns: {patterns}".format(patterns=", ".join(sorted(EXCLUDED_PARTS))),
        "",
        "## Changed Files",
        "",
    ]

    if changed_files:
        lines.extend("- `{path}`".format(path=path) for path in changed_files)
    else:
        lines.append("- No file content changes since the previous Ralph run.")

    lines.extend(["", "## Findings", ""])
    if findings:
        for severity in ("high", "medium", "low"):
            bucket = [finding for finding in findings if finding.severity == severity]
            if not bucket:
                continue
            lines.append("### {severity}".format(severity=severity.capitalize()))
            lines.append("")
            for finding in bucket:
                lines.append("- `{path}`: **{title}**. {detail}".format(
                    path=finding.path,
                    title=finding.title,
                    detail=finding.detail,
                ))
            lines.append("")
    else:
        lines.append("- No findings.")
        lines.append("")

    lines.extend(["## Recurring Findings", ""])
    if recurring_ids:
        lines.extend("- `{finding_id}`".format(finding_id=finding_id) for finding_id in recurring_ids)
    else:
        lines.append("- None.")

    lines.extend(["", "## Resolved Findings", ""])
    if resolved_ids:
        lines.extend("- `{finding_id}`".format(finding_id=finding_id) for finding_id in resolved_ids)
    else:
        lines.append("- None.")

    lines.extend(["", "## New Findings", ""])
    if new_ids:
        lines.extend("- `{finding_id}`".format(finding_id=finding_id) for finding_id in new_ids)
    else:
        lines.append("- None.")

    return "\n".join(lines).rstrip() + "\n"


def render_failure_review(run_id: str, failure_stage: str, error: str) -> str:
    return (
        "# Ralph Backend Review\n\n"
        "Run ID: `{run_id}`\n"
        "Status: `failed`\n\n"
        "## Failure\n\n"
        "- Stage: `{stage}`\n"
        "- Error: `{error}`\n"
    ).format(run_id=run_id, stage=failure_stage, error=error)


def refresh_latest(flattened_path: Path, review_path: Path, meta_path: Path) -> None:
    shutil.copyfile(flattened_path, LATEST_DIR / "flattened-backend.txt")
    shutil.copyfile(review_path, LATEST_DIR / "review.md")
    shutil.copyfile(meta_path, LATEST_DIR / "meta.json")


def next_run_target() -> tuple[str, Path]:
    base = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    candidate = RUNS_DIR / base
    if not candidate.exists():
        return base, candidate

    suffix = 1
    while True:
        run_id = "{base}-{suffix:02d}".format(base=base, suffix=suffix)
        candidate = RUNS_DIR / run_id
        if not candidate.exists():
            return run_id, candidate
        suffix += 1


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
