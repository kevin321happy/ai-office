# AI Office

AI Office is a local multi-agent workflow desk for coordinating AI coding tools and LLM workers.

The first version focuses on a safe local workflow:

- Codex as technical lead and final validator.
- Claude as planner and reviewer.
- Cursor as execution worker.
- Git diffs, task files, event logs, and validation artifacts as the shared source of truth.

## Goals

- Route work to the right AI worker.
- Keep coding and review responsibilities separated.
- Preserve task history and artifacts on disk.
- Provide a local web dashboard for task visibility.
- Keep private company data out of the public project.

## Safety Boundary

This repository is designed to be safe for a personal GitHub project. Runtime data and private company information must stay local.

Do not commit:

- Real work tasks.
- Internal repository paths.
- TAPD, GitLab, Jenkins, or DingTalk credentials.
- Real MR diffs, crash logs, reports, or knowledge base files.
- Local config files or tokens.

Use `config/config.example.json` for public examples and keep real settings in ignored local files.

## Project Layout

```text
app/          Python backend, CLI, storage, tools, workflows
web/          Local dashboard
docs/         Architecture and workflow documentation
config/       Example config only; local config is ignored
templates/    Reusable task and review templates
tasks/        Local task runtime data, ignored by git
knowledge/    Local RAG source files, ignored by git
logs/         Runtime logs, ignored by git
reports/      Generated reports, ignored by git
```

## Current Status

MVP in progress.

Implemented:

- Local task model.
- JSON task storage.
- Event log writer.
- Default prompts for Cursor, Claude, and Codex.
- Simulated planner, developer, reviewer, and validator steps.

Next:

- CLI commands.
- Local API server.
- Web dashboard.
- Real adapter hooks for Codex, Claude, and Cursor.

