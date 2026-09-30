from typing import Any

from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    customer_email: str = Field(min_length=5, max_length=254)
    message: str = Field(min_length=3, max_length=1000)


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=2, max_length=100)


class AgentResponse(BaseModel):
    trace_id: str
    intent: str
    reply: str
    status: str
    approval_id: str | None = None
    ticket_id: str | None = None
    steps: list[dict[str, Any]]
