from agentic_customer_support.api import create_app
from agentic_customer_support.config import Settings


def test_api_registers_expected_routes(tmp_path) -> None:
    app = create_app(Settings(db_path=tmp_path / "support.sqlite3", api_key="x" * 32))

    routes = {route.path for route in app.routes}
    assert {
        "/health",
        "/v1/support",
        "/v1/approvals/{approval_id}",
        "/v1/traces/{trace_id}",
    } <= routes
    assert app.title == "Agentic Customer Support"
