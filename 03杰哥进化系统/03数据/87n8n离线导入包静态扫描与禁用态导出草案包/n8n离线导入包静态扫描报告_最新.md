# n8n 离线导入包静态扫描报告

- 扫描时间：2026-05-08 18:50:24
- 状态：pass
- disabled=true
- active=false
- webhook_enabled=false
- real_trigger=false
- credential_values_present=false
- import_allowed=false
- activation_allowed=false
- scan_error_count=0
- error_count=0

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| 草案文件存在 | True | json=True md=True |
| 草案顶层禁用态完整 | True | disabled=true active=false |
| 工作流禁用态完整 | True | workflow.disabled=true workflow.active=false |
| webhook与触发器禁用 | True | webhook_enabled=false real_trigger=false |
| 凭据值缺席 | True | credential_values_present=false |
| 导入启用双禁 | True | import_allowed=false activation_allowed=false |
| 布尔开关无越界 | True | 通过 |
| 无真实URL或密钥形态 | True | 通过 |
| 无外部网络动作 | True | 通过 |
| 无真实企业微信发送动作 | True | 通过 |
| 节点均为禁用占位 | True | node_count=5 |
| 静态扫描规则存在 | True | rule_count=7 |
