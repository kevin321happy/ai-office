from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import json
import re
import subprocess
import sys
from typing import Any


DEFAULT_WORKFLOWS_DIR = Path.home() / ".codex" / "local-workflows"


@dataclass
class LocalWorkflowIndex:
    enabled: bool
    root: str
    commands_file_exists: bool
    headings: list[str]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LocalWorkflowRun:
    ok: bool
    status: str
    command: list[str]
    stdout: str
    stderr: str
    report: str
    missing: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def workflows_root() -> Path:
    configured = os.environ.get("AI_OFFICE_LOCAL_WORKFLOWS_DIR", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_WORKFLOWS_DIR


def load_index() -> LocalWorkflowIndex:
    root = workflows_root()
    commands_file = root / "COMMANDS.md"
    headings: list[str] = []
    notes: list[str] = []
    if commands_file.exists():
        content = redact(commands_file.read_text(encoding="utf-8"))
        headings = extract_headings(content)
        notes.append("Local workflow command index detected.")
    else:
        notes.append("Local workflow command index not found.")
    notes.append("Private workflow files are read at runtime and are not committed to this repository.")
    return LocalWorkflowIndex(
        enabled=root.exists(),
        root=redact_path(root),
        commands_file_exists=commands_file.exists(),
        headings=headings,
        notes=notes,
    )


def run_work_item_dry_run(task: Any, task_path: Path, params: dict[str, Any]) -> LocalWorkflowRun:
    defaults = load_local_config().get("work_item_dry_run", {})
    workflow = task.work_item or {}
    item_type = workflow.get("item_type", "story")
    command_path = Path(str(params.get("command") or defaults.get("command") or workflows_root() / "task-init" / "task_orchestrator.py")).expanduser()
    source = str(params.get("source_url") or task.source_url or workflow.get("source_url") or "").strip()
    product = str(params.get("product") or defaults.get("product") or "").strip()
    components = str(params.get("components") or defaults.get("components") or "").strip()
    customer = str(params.get("customer") or defaults.get("customer") or "").strip()
    slug = str(params.get("slug") or defaults.get("slug") or slug_from_work_item(workflow) or "").strip()
    title = str(params.get("title") or task.title or workflow.get("title") or "").strip()
    task_type = str(params.get("type") or defaults.get("type") or ("bugfix" if item_type == "bug" else "feature"))
    include_branch_plan = bool(params.get("branch_plan", defaults.get("branch_plan", True)))
    include_mr_context = bool(params.get("mr_context", defaults.get("mr_context", False)))

    missing = []
    for key, value in {
        "source_url": source,
        "product": product,
        "components": components,
        "customer": customer,
        "slug": slug,
    }.items():
        if not value:
            missing.append(key)
    if not command_path.exists():
        missing.append("command")
    if missing:
        return LocalWorkflowRun(
            ok=False,
            status="missing-parameters",
            command=[],
            stdout="",
            stderr="",
            report=render_missing_report(missing),
            missing=missing,
        )

    raw_output = task_path / "artifacts" / "local-workflow-summary.raw.md"
    command = [
        sys.executable,
        str(command_path),
        "--tapd",
        source,
        "--type",
        task_type,
        "--product",
        product,
        "--components",
        components,
        "--customer",
        customer,
        "--slug",
        slug,
        "--title",
        title,
        "--output",
        str(raw_output),
    ]
    if include_branch_plan:
        command.append("--branch-plan")
    if include_mr_context:
        command.append("--mr-context")

    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if raw_output.exists():
        report = redact(raw_output.read_text(encoding="utf-8"))
    else:
        report = render_process_report(result.returncode, result.stdout, result.stderr)
    return LocalWorkflowRun(
        ok=result.returncode == 0,
        status="completed" if result.returncode == 0 else "failed",
        command=[redact(part) for part in command],
        stdout=redact(result.stdout),
        stderr=redact(result.stderr),
        report=report,
        missing=[],
    )


def load_local_config() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    config_file = root / "config" / "config.local.json"
    if not config_file.exists():
        return {}
    return json.loads(config_file.read_text(encoding="utf-8"))


def slug_from_work_item(workflow: dict[str, Any]) -> str:
    branch_name = str(workflow.get("branch_name", ""))
    if "/" not in branch_name:
        return ""
    tail = branch_name.split("/", 1)[1]
    return re.sub(r"-\d{8}$", "", tail)


def render_missing_report(missing: list[str]) -> str:
    lines = [
        "# Local Workflow Dry-Run Blocked",
        "",
        "The dry-run was not executed because required local parameters are missing.",
        "",
        "## Missing Parameters",
        "",
    ]
    lines.extend(f"- {item}" for item in missing)
    lines.extend([
        "",
        "## Safety Boundary",
        "",
        "No external command was executed.",
        "No branch, commit, merge request, or external status update was created.",
    ])
    return "\n".join(lines) + "\n"


def render_process_report(returncode: int, stdout: str, stderr: str) -> str:
    return "\n".join([
        "# Local Workflow Dry-Run Failed",
        "",
        f"Exit code: {returncode}",
        "",
        "## Stdout",
        "",
        "```text",
        redact(stdout).strip(),
        "```",
        "",
        "## Stderr",
        "",
        "```text",
        redact(stderr).strip(),
        "```",
        "",
    ])


def extract_headings(content: str) -> list[str]:
    headings = []
    for line in content.splitlines():
        match = re.match(r"^#{2,3}\s+(.+)$", line.strip())
        if match:
            headings.append(match.group(1).strip())
    return headings


def redact(value: str) -> str:
    patterns = load_local_patterns()
    result = value
    for pattern in patterns:
        if not pattern:
            continue
        result = re.sub(re.escape(pattern), "[redacted]", result, flags=re.IGNORECASE)
    result = re.sub(r"/Users/[^/]+", "~", result)
    return result


def redact_path(path: Path) -> str:
    return redact(str(path.expanduser()))


def load_local_patterns() -> list[str]:
    root = Path(__file__).resolve().parents[1]
    pattern_file = root / "config" / "privacy_patterns.local.txt"
    if not pattern_file.exists():
        return []
    patterns = []
    for line in pattern_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns
