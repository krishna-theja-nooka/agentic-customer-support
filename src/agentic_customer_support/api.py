from collections import defaultdict, deque
from time import monotonic

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from .config import Settings
from .models import ApprovalDecision, SupportRequest
from .service import SupportAgentService, get_trace
from .tools import ToolError


class Limiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.history: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, client: str) -> bool:
        now = monotonic()
        bucket = self.history[client]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= self.per_minute:
            return False
        bucket.append(now)
        return True


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    service = SupportAgentService(settings)
    limiter = Limiter(settings.requests_per_minute)
    app = FastAPI(title="Agentic Customer Support", version="0.1.0")

    def authenticate(x_api_key: str = Header(default="")) -> None:
        if len(settings.api_key) < 24 or x_api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

    def limit(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(client):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

    @app.get("/health")
    def health() -> dict[str, object]:
        return service.health()

    @app.post("/v1/support", dependencies=[Depends(authenticate), Depends(limit)])
    def support(body: SupportRequest):
        return service.handle(body.customer_email, body.message)

    @app.post("/v1/approvals/{approval_id}", dependencies=[Depends(authenticate), Depends(limit)])
    def approval(approval_id: str, body: ApprovalDecision):
        try:
            return service.decide_approval(approval_id, body.approved, body.reviewer)
        except ToolError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/traces/{trace_id}", dependencies=[Depends(authenticate)])
    def trace(trace_id: str):
        result = get_trace(settings.db_path, trace_id)
        if not result:
            raise HTTPException(status_code=404, detail="Trace not found")
        return result

    return app
