# n8n 禁用态离线导入包草案

- 生成时间：2026-05-08 18:49:53
- 状态：draft_disabled_static_scan_ready
- disabled=true
- active=false
- webhook_enabled=false
- real_trigger=false
- credential_values_present=false
- import_allowed=false
- activation_allowed=false
- error_count=0

| 节点 | 类型 | 动作 | disabled | active |
| --- | --- | --- | --- | --- |
| 离线入队占位 | disabled.placeholder | manual_review_only | True | False |
| 凭据隔离占位 | disabled.placeholder | strip_values_before_import | True | False |
| 业务处理占位 | disabled.placeholder | disabled_noop | True | False |
| 企业微信通知占位 | disabled.placeholder | manual_note_only | True | False |
| 收口记录占位 | disabled.placeholder | local_draft_only | True | False |

红线：不接 n8n；不触发 webhook；不请求网络；不改配置；不重载服务；不真实发送企业微信。
