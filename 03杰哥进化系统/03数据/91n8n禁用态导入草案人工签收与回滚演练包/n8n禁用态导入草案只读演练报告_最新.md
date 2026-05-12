# n8n禁用态导入草案只读演练报告

- 演练时间：2026-05-08 19:00:55
- 状态：pass
- disabled=true
- active=false
- webhook_enabled=false
- real_trigger=false
- credential_values_present=false
- network_request=false
- rollback_executed=false
- error_count=0

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 人工签收单默认未签收 | True | status=unsigned signed=false |
| 导入与激活保持禁止 | True | import_allowed=false activation_allowed=false |
| 主管确认为必需 | True | requires_supervisor_confirmation=true |
| 四类回滚演练场景齐全 | True | 通过 |
| 全链路只读仿真 | True | 通过 |
| 凭据值不存在 | True | credential_values_present=false |
| 签收与回滚演练MD存在 | True | signoff_md=True rollback_md=True |
