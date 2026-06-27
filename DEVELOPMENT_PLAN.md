# AI Office Development Plan

## Product Goal

AI Office is a local multi-agent workflow desk. It coordinates Codex, Claude, Cursor, and future AI workers through one task system.

The target workflow:

```text
Boss creates a task
-> Planner prepares scope and acceptance criteria
-> Executor implements or runs the assigned workflow
-> Reviewer checks risk, diff, and quality
-> Validator verifies real evidence
-> Reporter summarizes the result for the boss
```

## Role Model

| Role | Default Worker | Responsibility |
| --- | --- | --- |
| Planner | Codex / Claude | Scope, plan, acceptance criteria |
| Executor | Cursor / Codex | Code, scripts, documents, repeatable work |
| Reviewer | Claude / Codex | Independent review, risk analysis, test gaps |
| Validator | Codex | Git, build, tests, local environment, final result |
| Boss | User | Priority, approval, product decisions |

## Safety Rules

- Code work must separate executor and reviewer.
- Cursor cannot be the final validator.
- Claude review cannot replace real build or test evidence.
- Codex validates real local state before completion.
- Runtime data, private configs, company identifiers, and real work artifacts must never be committed.
- Run `./scripts/privacy_scan.sh` before every commit.

## Phase 1: Local MVP

Goal: make the system usable locally.

Tasks:

- Implement CLI commands: `submit`, `list`, `show`, `step`.
- Implement local API server.
- Implement Web dashboard.
- Support task creation and state transitions.
- Show task events, prompts, artifacts, and current owner.
- Support simulated planner/developer/reviewer/validator steps.

Acceptance:

- Open `http://localhost:8787` and view the dashboard.
- Create a task from the dashboard.
- Step through planner, developer, reviewer, and validator.
- See generated artifacts under `tasks/<task-id>/artifacts/`.

## Phase 2: Real Worker Adapters

Goal: connect the task system to real AI tools.

Tasks:

- Add Codex adapter for planning and validation.
- Add Claude adapter for review.
- Add Cursor task-pack export first, then CLI/agent integration when available.
- Add fallback rules when Claude quota is unavailable.
- Add execution logs for every worker call.

Acceptance:

- Generate a standard Cursor task package.
- Generate a Claude review package from task context and artifacts.
- Generate a Codex validation report from local git state.

## Phase 3: Coding Workflow

Goal: run a real coding task with review and validation gates.

Tasks:

- Add Git tools: status, diff, diff-stat, diff-check.
- Generate `diff.patch`, `checks.log`, `review.md`, and `result.md`.
- Block completion without review and validation.
- Add commit helper with Chinese commit messages.

Acceptance:

- A small code task can go through plan -> execute -> review -> validate.
- Failed validation moves the task to `NEED_FIX` or `BLOCKED`.

## Phase 4: Daily Work Agents

Goal: support real daily work workflows.

Initial agents:

- MR Review Agent.
- Task Analysis Agent.
- AI Daily Agent.
- Build Validation Agent.

Each agent must define:

- Input.
- Steps.
- Tools.
- Artifacts.
- Quality gates.
- Human approval points.
- Failure handling.

## Phase 5: LangGraph Workflow Engine

Goal: replace manual flow control with a graph-based workflow engine.

Nodes:

- Planner.
- Executor.
- Reviewer.
- Validator.
- Reporter.
- Human Approval.

Capabilities:

- Conditional routing.
- Retry.
- Quota fallback.
- Human-in-the-loop.
- Durable state.

## Phase 6: RAG and Knowledge Base

Goal: make AI Office learn from safe local knowledge.

Data sources:

- Sanitized task summaries.
- Public examples.
- Personal notes.
- Local-only private knowledge ignored by git.

Capabilities:

- Similar task search.
- Risk suggestions.
- Historical solution retrieval.
- Source citations.

## Near-Term Checklist

- [ ] Implement `app/server.py`.
- [ ] Implement `app/cli.py`.
- [ ] Implement `web/index.html`.
- [ ] Implement `web/styles.css`.
- [ ] Implement `web/app.js`.
- [ ] Start local dashboard on port `8787`.
- [ ] Run one simulated end-to-end task.
- [ ] Commit and push after privacy scan.

