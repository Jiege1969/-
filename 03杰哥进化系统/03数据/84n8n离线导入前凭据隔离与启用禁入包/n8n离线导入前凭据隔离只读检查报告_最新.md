# n8n 离线导入前凭据隔离只读检查报告

- 检查时间：2026-05-08 18:31:06
- 状态：pass
- import_allowed=false
- activation_allowed=false
- credential_values_present=false
- webhook_enabled=false
- real_trigger=false
- error_count=0

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 凭据字段隔离清单齐全 | True | slot_count=5 |
| webhook禁用清单齐全 | True | webhook_count=3 |
| 导入前禁入条件齐全 | True | condition_count=6 |
| 启用前总管确认项齐全 | True | confirmation_count=7 |
| 回滚要求齐全 | True | rollback_count=5 |
| 红线开关保持关闭 | True | credential_values_present=false webhook_enabled=false real_trigger=false |
