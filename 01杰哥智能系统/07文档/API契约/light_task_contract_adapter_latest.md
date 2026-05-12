# Light Task Contract Adapter

Scope: 01 smart system.  
Principle: learn the task orchestration and receipt loop ideas from OpenClaw/Hermes, without importing original artifacts or calling external services.

This is the ASCII-named mirror used by the PowerShell validator. The Chinese evidence document remains the primary human-readable contract.

Required behavior:

- Read a standard task JSON locally.
- Route only to model/middleware capability labels.
- Keep `dry_run=true`.
- Keep real actions disabled.
- Plan SQLite shadow ledger only.
- Plan Redis shadow mapping only.
- Keep n8n in dry-run planning mode only.
- Produce a receipt with selected route, shadow writes, empty external calls, blocked actions, and local evidence.

Hard blocks:

- No real model API calls.
- No n8n trigger.
- No Enterprise WeChat send.
- No formal database write.
- No broker API.
- No automatic trading.
- No external network request.
