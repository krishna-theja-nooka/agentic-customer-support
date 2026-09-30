import sqlite3
from pathlib import Path

CUSTOMERS = [
    ("CUST-100", "Ava Patel", "ava@example.com", "premium"),
    ("CUST-200", "Marcus Lee", "marcus@example.com", "standard"),
]
ORDERS = [
    ("ORD-1001", "CUST-100", "delivered", 84.50, "2026-09-20"),
    ("ORD-1002", "CUST-100", "processing", 135.00, "2026-09-27"),
    ("ORD-2001", "CUST-200", "delivered", 310.00, "2026-09-10"),
]


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
              customer_id TEXT PRIMARY KEY, full_name TEXT NOT NULL,
              email TEXT UNIQUE NOT NULL, tier TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
              order_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL,
              status TEXT NOT NULL, total_usd REAL NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            );
            CREATE TABLE IF NOT EXISTS approvals (
              approval_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, amount_usd REAL NOT NULL,
              reason TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              decided_at TEXT, reviewer TEXT
            );
            CREATE TABLE IF NOT EXISTS tickets (
              ticket_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, category TEXT NOT NULL,
              priority TEXT NOT NULL, summary TEXT NOT NULL, status TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS agent_traces (
              trace_id TEXT PRIMARY KEY, customer_id TEXT, intent TEXT NOT NULL,
              outcome TEXT NOT NULL, steps_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        if db.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
            db.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", CUSTOMERS)
            db.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", ORDERS)
