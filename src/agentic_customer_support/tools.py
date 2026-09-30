from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from .database import connect


class ToolError(ValueError):
    pass


@dataclass
class SupportTools:
    db_path: Path
    max_refund_usd: int

    def customer_by_email(self, email: str) -> dict[str, object]:
        with connect(self.db_path) as db:
            row = db.execute(
                "SELECT customer_id, full_name, email, tier FROM customers WHERE email = ?",
                (email.lower(),),
            ).fetchone()
        if not row:
            raise ToolError("I could not verify that customer account.")
        return dict(row)

    def latest_order(self, customer_id: str, delivered_only: bool = False) -> dict[str, object]:
        condition = "AND status = 'delivered'" if delivered_only else ""
        with connect(self.db_path) as db:
            row = db.execute(
                "SELECT order_id, status, total_usd, created_at FROM orders "
                f"WHERE customer_id = ? {condition} ORDER BY created_at DESC LIMIT 1",
                (customer_id,),
            ).fetchone()
        if not row:
            raise ToolError("No eligible order was found for this customer.")
        return dict(row)

    def request_approval(self, order: dict[str, object], reason: str) -> str:
        amount = float(order["total_usd"])
        if amount > self.max_refund_usd:
            raise ToolError(f"This refund exceeds the ${self.max_refund_usd} approval limit.")
        approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
        with connect(self.db_path) as db:
            db.execute(
                "INSERT INTO approvals(approval_id, order_id, amount_usd, reason, status) VALUES (?, ?, ?, ?, ?)",
                (approval_id, order["order_id"], amount, reason[:300], "pending"),
            )
        return approval_id

    def create_ticket(self, customer_id: str, category: str, summary: str) -> str:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        priority = "high" if category == "human_escalation" else "normal"
        with connect(self.db_path) as db:
            db.execute(
                "INSERT INTO tickets(ticket_id, customer_id, category, priority, summary, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ticket_id, customer_id, category, priority, summary[:500], "open"),
            )
        return ticket_id

    def decide_approval(self, approval_id: str, approved: bool, reviewer: str) -> dict[str, object]:
        with connect(self.db_path) as db:
            row = db.execute(
                "SELECT approval_id, order_id, amount_usd, status FROM approvals WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
            if not row:
                raise ToolError("Approval request was not found.")
            if row["status"] != "pending":
                raise ToolError("Approval request was already decided.")
            status = "approved" if approved else "rejected"
            db.execute(
                "UPDATE approvals SET status = ?, reviewer = ?, decided_at = CURRENT_TIMESTAMP WHERE approval_id = ?",
                (status, reviewer, approval_id),
            )
        return {
            "approval_id": approval_id,
            "status": status,
            "order_id": row["order_id"],
            "amount_usd": row["amount_usd"],
        }
