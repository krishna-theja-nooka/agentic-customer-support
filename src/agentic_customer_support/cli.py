from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

import uvicorn

from .api import create_app
from .config import Settings
from .database import initialize
from .evaluation import evaluate
from .service import SupportAgentService


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentic_customer_support")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-env", help="Create .env with a private local API key")
    commands.add_parser("seed", help="Create the synthetic support data")
    ask = commands.add_parser("ask", help="Run a support workflow locally")
    ask.add_argument("customer_email")
    ask.add_argument("message")
    evaluate_command = commands.add_parser("evaluate", help="Run deterministic evaluation cases")
    evaluate_command.add_argument("--output", default="reports/evaluation.json")
    serve = commands.add_parser("serve", help="Start the local FastAPI server")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.command == "init-env":
        target, template = Path(".env"), Path(".env.example")
        if target.exists():
            raise SystemExit("Error: .env already exists")
        target.write_text(
            template.read_text(encoding="utf-8").replace(
                "SUPPORT_AGENT_API_KEY=", f"SUPPORT_AGENT_API_KEY={secrets.token_urlsafe(32)}"
            ),
            encoding="utf-8",
        )
        print("Created .env with a private random API key.")
        return

    settings = Settings()
    if args.command == "seed":
        initialize(settings.db_path)
        print(f"Initialized {settings.db_path}")
        return
    if args.command == "ask":
        print(
            json.dumps(
                SupportAgentService(settings)
                .handle(args.customer_email, args.message)
                .model_dump(),
                indent=2,
            )
        )
        return
    if args.command == "evaluate":
        report = evaluate(SupportAgentService(settings), Path("eval/cases.jsonl"))
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {key: report[key] for key in ("total_cases", "passed_cases", "pass_rate")}, indent=2
            )
        )
        raise SystemExit(0 if report["passed_cases"] == report["total_cases"] else 1)
    uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port)
