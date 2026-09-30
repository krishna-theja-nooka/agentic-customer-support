# Security and safety model

## Safeguards included

- The agent accepts only a small allow-listed intent catalog.
- Prompt-injection phrases are rejected before any business tool runs.
- Customer lookup requires a supplied email that matches a stored account.
- Refunds never execute automatically; they create a pending approval record.
- Refund requests above the configured threshold are rejected for human handling.
- API-key authentication and per-client rate limiting protect write-capable routes.
- Agent traces record the selected intent, tools, status, and rejection reasons.
- The repository ships only fictional deterministic data.

## Production hardening roadmap

Use identity-provider authentication, verified customer sessions, account-level authorization, payment-provider idempotency keys, signed webhook verification, secret management, distributed rate limiting, centralized traces, PII redaction, and a real human-work queue before deployment.
