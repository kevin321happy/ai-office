from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import mimetypes
import urllib.parse

from app import storage
from app.local_workflows import load_index


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"


class AIRequestHandler(BaseHTTPRequestHandler):
    server_version = "AIOffice/0.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/tasks":
            self.write_json({"tasks": [task.__dict__ for task in storage.list_tasks()]})
            return
        if parsed.path == "/api/local-workflows":
            self.write_json({"local_workflows": load_index().to_dict()})
            return
        if parsed.path.startswith("/api/tasks/"):
            task_id = urllib.parse.unquote(parsed.path.removeprefix("/api/tasks/"))
            try:
                self.write_json(storage.task_payload(task_id))
            except FileNotFoundError:
                self.write_json({"error": "task not found"}, HTTPStatus.NOT_FOUND)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/tasks":
            payload = self.read_json()
            title = str(payload.get("title", "")).strip()
            source_url = str(payload.get("source_url", "")).strip()
            if not title:
                title = source_url
            if not title:
                self.write_json({"error": "title or source_url is required"}, HTTPStatus.BAD_REQUEST)
                return
            if source_url:
                task = storage.create_work_item_task(
                    source_url=source_url,
                    title=title if title != source_url else "",
                    description=str(payload.get("description", "")),
                    risk=str(payload.get("risk", "normal")),
                )
            else:
                task = storage.create_task(
                    title=title,
                    description=str(payload.get("description", "")),
                    risk=str(payload.get("risk", "normal")),
                    roles=payload.get("roles") if isinstance(payload.get("roles"), dict) else None,
                )
            self.write_json({"task": task.__dict__}, HTTPStatus.CREATED)
            return
        if parsed.path.startswith("/api/tasks/") and parsed.path.endswith("/step"):
            task_id = urllib.parse.unquote(parsed.path.removeprefix("/api/tasks/").removesuffix("/step"))
            payload = self.read_json()
            actor = str(payload.get("actor", "")).strip()
            try:
                task = storage.simulate_step(task_id, actor)
                self.write_json({"task": task.__dict__})
            except (FileNotFoundError, ValueError) as exc:
                self.write_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path: str) -> None:
        if request_path in {"", "/"}:
            relative = "index.html"
        else:
            relative = request_path.lstrip("/")
        target = (WEB_DIR / relative).resolve()
        if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Office local server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    storage.ensure_dirs()
    server = ThreadingHTTPServer((args.host, args.port), AIRequestHandler)
    print(f"AI Office dashboard: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
