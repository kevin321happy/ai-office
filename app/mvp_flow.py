from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app import storage
from app.local_workflows import run_work_item_dry_run


@dataclass
class MVPFlowResult:
    ok: bool
    status: str
    artifacts: list[str]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def run_minimal_mvp(task_id: str, params: dict[str, Any]) -> MVPFlowResult:
    task = storage.load_task(task_id)
    if not task.work_item:
        raise ValueError("minimal MVP flow requires a work item task")

    artifacts: list[str] = []
    notes: list[str] = []

    analysis = render_analysis(task)
    storage.write_artifact(task_id, "00-work-item-analysis.md", analysis, "codex")
    artifacts.append("00-work-item-analysis.md")
    storage.update_status(task_id, "PLANNED", "codex", "Work item analysis generated.")

    dry_run = run_work_item_dry_run(task, storage.task_dir(task_id), params)
    storage.write_artifact(task_id, "01-local-workflow-dry-run.md", dry_run.report, "local-workflow")
    artifacts.append("01-local-workflow-dry-run.md")
    storage.append_event(task_id, "LOCAL_WORKFLOW_DRY_RUN", "local-workflow", dry_run.to_dict())
    if not dry_run.ok:
        notes.append(f"Local workflow dry-run did not complete: {dry_run.status}")

    repair_plan = render_repair_plan(task, dry_run.status)
    storage.write_artifact(task_id, "02-repair-plan.md", repair_plan, "planner")
    artifacts.append("02-repair-plan.md")
    storage.update_status(task_id, "ASSIGNED", "codex", "Repair plan generated and assigned to executor.")

    execution = render_execution_report(task)
    storage.write_artifact(task_id, "03-execution-report.md", execution, task.roles.get("developer", "cursor"))
    artifacts.append("03-execution-report.md")
    storage.update_status(task_id, "CODE_READY", task.roles.get("developer", "cursor"), "Safe-mode execution report generated.")

    review = render_review_report(task)
    storage.write_artifact(task_id, "04-review-report.md", review, task.roles.get("reviewer", "claude"))
    artifacts.append("04-review-report.md")
    storage.update_status(task_id, "REVIEW_PASS", task.roles.get("reviewer", "claude"), "Safe-mode review report generated.")

    delivery = render_delivery_checklist(task, dry_run.ok)
    storage.write_artifact(task_id, "05-delivery-checklist.md", delivery, task.roles.get("validator", "codex"))
    artifacts.append("05-delivery-checklist.md")
    storage.update_status(task_id, "ACCEPTED", task.roles.get("validator", "codex"), "Minimal MVP flow completed in safe mode.")

    notes.append("Safe-mode MVP completed. No branch, commit, merge request, or external status update was created by this flow.")
    return MVPFlowResult(ok=True, status="safe-mode-complete", artifacts=artifacts, notes=notes)


def render_analysis(task: storage.Task) -> str:
    item = task.work_item or {}
    return "\n".join([
        "# Work Item Analysis",
        "",
        f"- Title: {task.title}",
        f"- Type: {item.get('item_type', '-')}",
        f"- External ID: {item.get('external_id', '-')}",
        f"- Short ID: {item.get('short_id', '-')}",
        f"- Planned branch: {item.get('branch_name', '-')}",
        f"- Confidence: {item.get('confidence', '-')}",
        "",
        "## Safety",
        "",
        "This analysis is heuristic until a local private adapter verifies the work item source.",
    ]) + "\n"


def render_repair_plan(task: storage.Task, dry_run_status: str) -> str:
    return "\n".join([
        "# Repair Plan",
        "",
        f"- Task: {task.title}",
        f"- Planner: {task.roles.get('planner')}",
        f"- Executor: {task.roles.get('developer')}",
        f"- Reviewer: {task.roles.get('reviewer')}",
        f"- Validator: {task.roles.get('validator')}",
        f"- Local workflow dry-run status: {dry_run_status}",
        "",
        "## Steps",
        "",
        "1. Verify work item type, title, and acceptance criteria.",
        "2. Confirm branch plan and repository target.",
        "3. Executor implements the minimal scoped change.",
        "4. Reviewer checks diff, edge cases, and regression risk.",
        "5. Validator runs local checks and decides whether the task can advance.",
        "",
        "## Current MVP Limitation",
        "",
        "This flow generates reports only. Real code execution is intentionally disabled in this MVP step.",
    ]) + "\n"


def render_execution_report(task: storage.Task) -> str:
    return "\n".join([
        "# Execution Report",
        "",
        f"- Executor: {task.roles.get('developer')}",
        "- Mode: safe report generation",
        "- Code changes: none",
        "- Branch changes: none",
        "- External side effects: none",
        "",
        "## Next Real Executor Contract",
        "",
        "When real execution is enabled, the executor must output modified files, commands run, unresolved risks, and a diff package for review.",
    ]) + "\n"


def render_review_report(task: storage.Task) -> str:
    return "\n".join([
        "# Review Report",
        "",
        f"- Reviewer: {task.roles.get('reviewer')}",
        "- Review target: generated plan and execution report",
        "- Blocking issues: none for safe-mode report generation",
        "- Code review: skipped because no code diff exists in this MVP step",
        "",
        "## Required Before Real Delivery",
        "",
        "- Review actual diff.",
        "- Check tests and local validation output.",
        "- Confirm no unrelated files changed.",
    ]) + "\n"


def render_delivery_checklist(task: storage.Task, dry_run_ok: bool) -> str:
    return "\n".join([
        "# Delivery Checklist",
        "",
        f"- Validator: {task.roles.get('validator')}",
        f"- Local workflow dry-run completed: {dry_run_ok}",
        "- Branch created: false",
        "- Commit created: false",
        "- Test branch synced: false",
        "- Merge request created: false",
        "- External status updated: false",
        "",
        "## MVP Result",
        "",
        "The minimal work item workflow is closed in safe mode. The next milestone is to enable real execution behind explicit approval gates.",
    ]) + "\n"

