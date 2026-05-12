# Dual System Ollama Governance Audit

Generated at: 2026-04-28 23:05:02

## Conclusion

Ollama governance must cover Windows scheduled tasks, Docker restart policy, and WSL2 cron/systemd/startup scripts together.

## Health

- v3 Ollama 29134: True, models=14
- protected stock Ollama 19134: True, models=11
- old base Ollama 11434: True, models=9

## Findings

- Windows scheduled task JiegeAgentOS_AutoStart can participate in old system startup


## Safety

Read-only audit only. No scheduled task, crontab, systemd unit, container, file, n8n workflow, WeWork message, DB, broker API, or trade was modified.
