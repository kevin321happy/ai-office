from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"


STATUSES = [
    "CREATED",
    "PLANNED",
    "ASSIGNED",
    "EXECUTING",
    "CODE_READY",
    "REVIEWING",
    "REVIEW_PASS",
    "VALIDATING",
    "ACCEPTED",
    "NEED_FIX",
    "BLOCKED",
]


ROLE_DEFAULTS = {
    "planner": "codex",
    "developer": "cursor",
    "reviewer": "claude",
    "validator": "codex",
}


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: str = "CREATED"
    risk: str = "normal"
    roles: dict[str, str] = field(default_factory=lambda: dict(ROLE_DEFAULTS))
    created_at: str = field(default_factory=lambda: now_iso())
    updated_at: str = field(default_factory=lambda: now_iso())
    current_owner: str = "codex"
    tags: list[str] = field(default_factory=list)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    return value[:48] or "task"


def next_task_id(title: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{slugify(title)}"


def task_dir(task_id: str) -> Path:
    return TASKS_DIR / task_id


def task_file(task_id: str) -> Path:
    return task_dir(task_id) / "task.json"


def events_file(task_id: str) -> Path:
    return task_dir(task_id) / "events.jsonl"


def ensure_dirs() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)


def create_task(
    title: str,
    description: str = "",
    risk: str = "normal",
    roles: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> Task:
    ensure_dirs()
    task_id = next_task_id(title)
    selected_roles = dict(ROLE_DEFAULTS)
    if roles:
        selected_roles.update({k: v for k, v in roles.items() if v})
    task = Task(
        id=task_id,
        title=title,
        description=description,
        risk=risk,
        roles=selected_roles,
        current_owner=selected_roles.get("planner", "codex"),
        tags=tags or [],
    )
    path = task_dir(task_id)
    path.mkdir(parents=True, exist_ok=False)
    for name in ["artifacts", "prompts", "logs"]:
        (path / name).mkdir(exist_ok=True)
    save_task(task)
    append_event(task_id, "TASK_CREATED", "system", {"title": title, "risk": risk})
    write_default_prompts(task)
    return task


def save_task(task: Task) -> None:
    task.updated_at = now_iso()
    path = task_file(task.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(task), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_task(task_id: str) -> Task:
    data = json.loads(task_file(task_id).read_text(encoding="utf-8"))
    return Task(**data)


def list_tasks() -> list[Task]:
    ensure_dirs()
    tasks: list[Task] = []
    for path in sorted(TASKS_DIR.iterdir(), reverse=True):
        if path.is_dir() and (path / "task.json").exists():
            tasks.append(load_task(path.name))
    return tasks


def update_status(task_id: str, status: str, actor: str = "system", note: str = "") -> Task:
    if status not in STATUSES:
        raise ValueError(f"Unsupported status: {status}")
    task = load_task(task_id)
    old_status = task.status
    task.status = status
    task.current_owner = owner_for_status(task)
    save_task(task)
    append_event(task_id, "STATUS_CHANGED", actor, {"from": old_status, "to": status, "note": note})
    return task


def owner_for_status(task: Task) -> str:
    if task.status in {"CREATED", "PLANNED"}:
        return task.roles.get("planner", "codex")
    if task.status in {"ASSIGNED", "EXECUTING", "NEED_FIX"}:
        return task.roles.get("developer", "cursor")
    if task.status in {"CODE_READY", "REVIEWING"}:
        return task.roles.get("reviewer", "claude")
    if task.status in {"REVIEW_PASS", "VALIDATING"}:
        return task.roles.get("validator", "codex")
    return "boss"


def append_event(task_id: str, event_type: str, actor: str, payload: dict[str, Any] | None = None) -> None:
    path = events_file(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": now_iso(),
        "type": event_type,
        "actor": actor,
        "payload": payload or {},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_events(task_id: str) -> list[dict[str, Any]]:
    path = events_file(task_id)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def task_payload(task_id: str) -> dict[str, Any]:
    task = load_task(task_id)
    path = task_dir(task_id)
    artifacts = []
    for item in sorted((path / "artifacts").glob("*")):
        if item.is_file():
            artifacts.append({"name": item.name, "path": str(item)})
    prompts = []
    for item in sorted((path / "prompts").glob("*.md")):
        prompts.append({"name": item.name, "path": str(item), "content": item.read_text(encoding="utf-8")})
    return {
        "task": asdict(task),
        "events": read_events(task_id),
        "artifacts": artifacts,
        "prompts": prompts,
        "directory": str(path),
    }


def write_artifact(task_id: str, name: str, content: str, actor: str = "system") -> Path:
    path = task_dir(task_id) / "artifacts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    append_event(task_id, "ARTIFACT_WRITTEN", actor, {"name": name, "path": str(path)})
    return path


def write_default_prompts(task: Task) -> None:
    prompts_dir = task_dir(task.id) / "prompts"
    cursor_prompt = f"""# Cursor 执行任务包

任务：{task.title}

背景：
{task.description or "待补充。"}

角色：执行工程师。

边界：
- 只按任务包执行，不做架构扩大。
- 不提交 commit，不创建 MR，不回写 TAPD。
- 完成后输出修改文件、验证命令、风险和未完成项。

交付：
- 代码 diff。
- 自测结果。
- 需要审查的问题。
"""
    claude_prompt = f"""# Claude 审查任务包

任务：{task.title}

背景：
{task.description or "待补充。"}

角色：架构/审查负责人。

审查重点：
- 需求是否覆盖。
- 边界条件和回归风险。
- 代码可维护性。
- 测试缺口。
- 是否存在不该修改的范围。

输出格式：
- 必须修复。
- 建议优化。
- 可接受风险。
- 是否通过审查。
"""
    codex_prompt = f"""# Codex 验收任务包

任务：{task.title}

背景：
{task.description or "待补充。"}

角色：技术负责人和最终验收者。

验收重点：
- git status / git diff 是否干净且范围正确。
- 是否符合 AGENTS.md 和项目约束。
- 构建、测试、真机或其他必要验证是否真实通过。
- 是否需要提交、MR、TAPD 回写或人工确认。

输出：
- 可提交 / 需返工 / 阻断。
- 验证证据。
- 剩余风险。
"""
    (prompts_dir / "cursor.md").write_text(cursor_prompt, encoding="utf-8")
    (prompts_dir / "claude-review.md").write_text(claude_prompt, encoding="utf-8")
    (prompts_dir / "codex-accept.md").write_text(codex_prompt, encoding="utf-8")


def simulate_step(task_id: str, actor: str) -> Task:
    task = load_task(task_id)
    if actor == "planner":
        write_artifact(task_id, "plan.md", f"# 执行计划\n\n- 任务：{task.title}\n- Planner：{task.roles.get('planner')}\n- Developer：{task.roles.get('developer')}\n- Reviewer：{task.roles.get('reviewer')}\n- Validator：{task.roles.get('validator')}\n", "codex")
        return update_status(task_id, "PLANNED", "codex", "已生成计划。")
    if actor == "developer":
        write_artifact(task_id, "execution-report.md", "# 执行回执\n\n- 当前为模拟执行。\n- 后续会接入 Cursor / Codex 真实执行器。\n- 未产生真实代码 diff。\n", task.roles.get("developer", "cursor"))
        return update_status(task_id, "CODE_READY", task.roles.get("developer", "cursor"), "模拟执行完成，等待审查。")
    if actor == "reviewer":
        write_artifact(task_id, "review.md", "# 审查结论\n\n- 当前为模拟审查。\n- 未发现阻断问题。\n- 真实流程会读取 diff.patch 和 checks.log。\n", task.roles.get("reviewer", "claude"))
        return update_status(task_id, "REVIEW_PASS", task.roles.get("reviewer", "claude"), "模拟审查通过。")
    if actor == "validator":
        write_artifact(task_id, "result.md", "# 验收结果\n\n- 当前为模拟验收。\n- 真实流程会运行 git diff、构建、测试或真机验证。\n- 结果：ACCEPTED。\n", task.roles.get("validator", "codex"))
        return update_status(task_id, "ACCEPTED", task.roles.get("validator", "codex"), "模拟验收通过。")
    raise ValueError(f"Unsupported actor: {actor}")
