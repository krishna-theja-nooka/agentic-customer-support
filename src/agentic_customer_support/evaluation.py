from __future__ import annotations

import json
from pathlib import Path

from .service import SupportAgentService


def evaluate(service: SupportAgentService, dataset: Path) -> dict[str, object]:
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    results: list[dict[str, object]] = []
    for case in cases:
        response = service.handle(case["customer_email"], case["message"])
        passed = (
            response.intent == case["expected_intent"]
            and response.status == case["expected_status"]
        )
        results.append({"id": case["id"], "passed": passed, "actual": response.model_dump()})
    passed_cases = sum(item["passed"] for item in results)
    return {
        "total_cases": len(results),
        "passed_cases": passed_cases,
        "pass_rate": passed_cases / len(results) if results else 0.0,
        "results": results,
    }
