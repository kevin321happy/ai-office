from __future__ import annotations

import argparse
import json

from app import storage


def cmd_submit(args: argparse.Namespace) -> None:
    task = storage.create_task(args.title, args.description or "", args.risk)
    print(json.dumps(task.__dict__, ensure_ascii=False, indent=2))


def cmd_list(_: argparse.Namespace) -> None:
    for task in storage.list_tasks():
        print(f"{task.id}\t{task.status}\t{task.current_owner}\t{task.title}")


def cmd_show(args: argparse.Namespace) -> None:
    print(json.dumps(storage.task_payload(args.task_id), ensure_ascii=False, indent=2))


def cmd_step(args: argparse.Namespace) -> None:
    task = storage.simulate_step(args.task_id, args.actor)
    print(json.dumps(task.__dict__, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-office")
    subparsers = parser.add_subparsers(required=True)

    submit = subparsers.add_parser("submit", help="Create a task")
    submit.add_argument("title")
    submit.add_argument("--description", "-d", default="")
    submit.add_argument("--risk", default="normal")
    submit.set_defaults(func=cmd_submit)

    list_cmd = subparsers.add_parser("list", help="List tasks")
    list_cmd.set_defaults(func=cmd_list)

    show = subparsers.add_parser("show", help="Show task details")
    show.add_argument("task_id")
    show.set_defaults(func=cmd_show)

    step = subparsers.add_parser("step", help="Run a simulated worker step")
    step.add_argument("task_id")
    step.add_argument("actor", choices=["planner", "developer", "reviewer", "validator"])
    step.set_defaults(func=cmd_step)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

