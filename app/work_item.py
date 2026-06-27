from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from urllib.parse import parse_qs, urlparse


@dataclass
class WorkItemAnalysis:
    source_url: str
    external_id: str
    short_id: str
    item_type: str
    title: str
    branch_prefix: str
    branch_name: str
    confidence: str
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_work_item(source: str, title: str = "") -> WorkItemAnalysis:
    external_id = extract_external_id(source)
    short_id = external_id[-7:] if len(external_id) > 7 else external_id
    item_type = infer_item_type(source, title)
    branch_prefix = "bugfix" if item_type == "bug" else "fe"
    description = slugify(title) if title else "work-item"
    date = datetime.now().strftime("%Y%m%d")
    branch_name = f"ai-{branch_prefix}-{short_id}/{description}-{date}"
    notes = [
        "This is a generic local analysis. Real system adapters should verify type and title before branch creation.",
        "Do not run external side effects until a validator confirms local configuration and approval gates.",
    ]
    return WorkItemAnalysis(
        source_url=source,
        external_id=external_id,
        short_id=short_id,
        item_type=item_type,
        title=title or f"Work item {short_id}",
        branch_prefix=branch_prefix,
        branch_name=branch_name,
        confidence="heuristic",
        notes=notes,
    )


def extract_external_id(source: str) -> str:
    parsed = urlparse(source)
    values = []
    values.extend(parse_qs(parsed.query).get("id", []))
    values.extend(parse_qs(parsed.query).get("bug_id", []))
    values.extend(parse_qs(parsed.query).get("story_id", []))
    for value in values:
        digits = re.sub(r"\D", "", value)
        if digits:
            return digits
    matches = re.findall(r"\d{6,}", source)
    if matches:
        return matches[-1]
    return datetime.now().strftime("%H%M%S")


def infer_item_type(source: str, title: str) -> str:
    combined = f"{source} {title}".lower()
    bug_markers = ["bug", "defect", "fix", "修复", "缺陷", "故障", "异常", "报错"]
    story_markers = ["story", "feature", "requirement", "需求", "新增", "优化", "功能"]
    if any(marker in combined for marker in bug_markers):
        return "bug"
    if any(marker in combined for marker in story_markers):
        return "story"
    return "story"


def slugify(value: str) -> str:
    value = value.strip().lower()
    replacements = {
        "修复": "fix",
        "新增": "add",
        "优化": "optimize",
        "登录": "login",
        "地图": "map",
        "列表": "list",
        "详情": "detail",
    }
    for src, dst in replacements.items():
        value = value.replace(src, f" {dst} ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value[:48] or "work-item"

