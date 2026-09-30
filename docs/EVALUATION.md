# Evaluation

The evaluation suite checks approved workflow selection, approval-gated refunds, escalation, and a prompt-injection rejection case.

```powershell
.\.venv\Scripts\python.exe -m agentic_customer_support evaluate --output reports/evaluation.json
```

GitHub Actions runs this command after linting and tests, then stores the report as an artifact.
