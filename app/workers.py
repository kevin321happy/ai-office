from __future__ import annotations

from dataclasses import asdict, dataclass
import shutil
import subprocess


WORKERS = {
    "codex": "Technical lead and validator",
    "claude": "Planner and reviewer",
    "cursor": "Executor",
}


@dataclass
class WorkerStatus:
    name: str
    role: str
    available: bool
    command: str
    version: str
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


def detect_workers() -> list[WorkerStatus]:
    return [detect_worker(name, role) for name, role in WORKERS.items()]


def detect_worker(name: str, role: str) -> WorkerStatus:
    command = shutil.which(name) or ""
    if not command:
        return WorkerStatus(
            name=name,
            role=role,
            available=False,
            command="",
            version="",
            note="Command not found in PATH. Use handoff artifacts or configure an adapter.",
        )
    version = read_version(command)
    return WorkerStatus(
        name=name,
        role=role,
        available=True,
        command=command,
        version=version,
        note="Available for local adapter integration.",
    )


def read_version(command: str) -> str:
    for args in ([command, "--version"], [command, "version"]):
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=5)
        output = (result.stdout or result.stderr).strip()
        if output:
            return output.splitlines()[0]
    return "version unavailable"

