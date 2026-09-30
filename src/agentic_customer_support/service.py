from __future__ import annotations

import json
import uuid
from pathlib import Path

from .config import Settings
from .database import connect, initialize
from .models import AgentResponse
from .planner import PlanningError, plan_message
from .tools import SupportTools, ToolError


class SupportAgentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        initialize(settings.db_path)
        self.tools = SupportTools(settings.db_path, settings.max_refund_usd)

    def handle(self, customer_email: str, message: str) -> AgentResponse:
        trace_id = f"TRC-{uuid.uuid4().hex[:10].upper()}"
        steps: list[dict[str, object]] = []
        customer_id: str | None = None
        try:
            selected = plan_message(message)
            steps.append({"tool": "intent_router", "status": "success", "intent": selected.intent})
            customer = self.tools.customer_by_email(customer_email)
            customer_id = str(customer["customer_id"])
            steps.append(
                {"tool": "lookup_customer", "status": "success", "customer_id": customer_id}
            )

            if selected.intent in {"refund_request", "order_status", "billing_question"}:
                order = self.tools.latest_order(
                    customer_id, delivered_only=selected.intent == "refund_request"
                )
                steps.append(
                    {"tool": "lookup_order", "status": "success", "order_id": order["order_id"]}
                )

                if selected.intent == "refund_request":
                    approval_id = self.tools.request_approval(order, message)
                    steps.append(
                        {
                            "tool": "request_approval",
                            "status": "pending",
                            "approval_id": approval_id,
                        }
                    )
                    response = AgentResponse(
                        trace_id=trace_id,
                        intent=selected.intent,
                        reply=(
                            f"I verified order {order['order_id']}. A ${float(order['total_usd']):.2f} refund "
                            "request was sent for human approval."
                        ),
                        status="awaiting_approval",
                        approval_id=approval_id,
                        steps=steps,
                    )
                elif selected.intent == "order_status":
                    response = AgentResponse(
                        trace_id=trace_id,
                        intent=selected.intent,
                        reply=f"Your latest order {order['order_id']} is currently {order['status']}.",
                        status="completed",
                        steps=steps,
                    )
                else:
                    response = AgentResponse(
                        trace_id=trace_id,
                        intent=selected.intent,
                        reply=(
                            f"Your latest order is {order['order_id']} for ${float(order['total_usd']):.2f}. "
                            f"Its current status is {order['status']}."
                        ),
                        status="completed",
                        steps=steps,
                    )
            else:
                ticket_id = self.tools.create_ticket(customer_id, selected.intent, message)
                steps.append({"tool": "create_ticket", "status": "success", "ticket_id": ticket_id})
                response = AgentResponse(
                    trace_id=trace_id,
                    intent=selected.intent,
                    reply="I created a support ticket and routed it to a human support specialist.",
                    status="escalated",
                    ticket_id=ticket_id,
                    steps=steps,
                )
            self._write_trace(trace_id, customer_id, selected.intent, response.status, steps)
            return response
        except (PlanningError, ToolError) as exc:
            steps.append({"tool": "agent_guard", "status": "rejected", "reason": str(exc)})
            self._write_trace(trace_id, customer_id, "rejected", "rejected", steps)
            return AgentResponse(
                trace_id=trace_id,
                intent="rejected",
                reply=str(exc),
                status="rejected",
                steps=steps,
            )

    def decide_approval(self, approval_id: str, approved: bool, reviewer: str) -> dict[str, object]:
        result = self.tools.decide_approval(approval_id, approved, reviewer)
        result["message"] = (
            "Refund approved and queued for processing."
            if approved
            else "Refund request was declined; a human specialist can follow up."
        )
        return result

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "tools": ["lookup_customer", "lookup_order", "request_approval", "create_ticket"],
            "approval_required_for_refunds": True,
            "data": "synthetic demo data",
        }

    def _write_trace(
        self,
        trace_id: str,
        customer_id: str | None,
        intent: str,
        outcome: str,
        steps: list[dict[str, object]],
    ) -> None:
        with connect(self.settings.db_path) as db:
            db.execute(
                "INSERT INTO agent_traces(trace_id, customer_id, intent, outcome, steps_json) VALUES (?, ?, ?, ?, ?)",
                (trace_id, customer_id, intent, outcome, json.dumps(steps)),
            )


def get_trace(db_path: Path, trace_id: str) -> dict[str, object] | None:
    with connect(db_path) as db:
        row = db.execute(
            "SELECT trace_id, customer_id, intent, outcome, steps_json, created_at FROM agent_traces WHERE trace_id = ?",
            (trace_id,),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["steps"] = json.loads(str(result.pop("steps_json")))
    return result
