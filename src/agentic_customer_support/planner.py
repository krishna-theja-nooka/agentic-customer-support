"""Deterministic intent and tool planning layer.

An LLM can later classify into this same restricted intent schema, but cannot
choose arbitrary tools or execute arbitrary instructions.
"""

from dataclasses import dataclass


class PlanningError(ValueError):
    pass


@dataclass(frozen=True)
class Plan:
    intent: str
    tools: tuple[str, ...]


def plan_message(message: str) -> Plan:
    normalized = " ".join(message.lower().split())
    blocked = ("ignore previous", "system prompt", "reveal secret", "delete customer")
    if any(phrase in normalized for phrase in blocked):
        raise PlanningError("This request cannot be handled by the support agent.")
    if "refund" in normalized or "money back" in normalized:
        return Plan("refund_request", ("lookup_customer", "lookup_order", "request_approval"))
    if "where" in normalized and "order" in normalized or "order status" in normalized:
        return Plan("order_status", ("lookup_customer", "lookup_order"))
    if any(word in normalized for word in ("human", "agent", "complaint", "angry", "cancel")):
        return Plan("human_escalation", ("lookup_customer", "create_ticket"))
    if any(word in normalized for word in ("invoice", "receipt", "charge")):
        return Plan("billing_question", ("lookup_customer", "lookup_order"))
    raise PlanningError("I could not safely map this to an approved support workflow.")
