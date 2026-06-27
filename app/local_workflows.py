from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import os
import re


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

