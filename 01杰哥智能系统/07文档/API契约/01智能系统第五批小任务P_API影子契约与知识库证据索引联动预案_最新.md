# 01智能系统第五批小任务P：API影子契约与知识库证据索引联动预案

- 生成时间：2026-05-05 13:03:07
- 执行模式：local_preview_only
- 写入策略：只写本地样本文件，正式库/正式向量库/正式数据库写入禁用

## 影子契约字段

### 请求字段
- request_id：string，required=True
- question：string，required=True
- evidence_query：object，required=True
- evidence_policy：string，required=True
- staleness_threshold_days：integer，required=True
- dry_run：boolean，required=True
- safety_boundary：object，required=True

### 响应字段
- request_id：string，required=True
- status：enum，required=True
- error_code：enum，required=True
- answer：string，required=True
- evidence_hits：array[object]，required=True
- degrade_message：string，required=True
- external_effect：string，required=True
- formal_store_write：boolean，required=True
- safety_boundary：object，required=True

## 错误码与降级语
- OK：命中本地证据索引，证据未过期，可以按影子契约返回。
- STALE_EVIDENCE：命中本地证据索引，但证据超过时效阈值，只能降级返回。；降级语：命中的本地证据已超过时效阈值，本轮只返回降级说明，不把旧证据当作当前事实。
- NO_EVIDENCE：未命中本地证据索引，不得编造答案，只能降级返回。；降级语：未在本地证据索引中找到可引用证据，本轮不生成事实性回答。
- EXTERNAL_API_BLOCKED：请求越权调用真实外部 API 或真实动作，被安全边界硬阻断。；降级语：真实外部 API 或真实动作已被阻断，仅允许输出本地 dry_run 影子结果。
- CONTRACT_FIELD_MISSING：请求或响应缺少影子契约必需字段。
- FORMAL_STORE_DISABLED：正式库、正式向量库或正式数据库写入被禁用。；降级语：正式库写入保持禁用，本轮只写本地样本文件。

## 本地证据索引样本
- P-EV-001：01智能API影子契约本地执行边界；freshness=fresh；age_days=0
- P-EV-002：旧版知识库证据索引说明；freshness=stale；age_days=65

## 四类联动样本
### P-S01 证据命中
- 状态：ok
- 错误码：OK
- 降级语：
- 外部效果：none
- 正式库写入：False

### P-S02 证据过旧降级
- 状态：degraded
- 错误码：STALE_EVIDENCE
- 降级语：命中的本地证据已超过时效阈值，本轮只返回降级说明，不把旧证据当作当前事实。
- 外部效果：none
- 正式库写入：False

### P-S03 无证据降级
- 状态：degraded
- 错误码：NO_EVIDENCE
- 降级语：未在本地证据索引中找到可引用证据，本轮不生成事实性回答。
- 外部效果：none
- 正式库写入：False

### P-S04 越权真实外部API阻断
- 状态：blocked
- 错误码：EXTERNAL_API_BLOCKED
- 降级语：真实外部 API 或真实动作已被阻断，仅允许输出本地 dry_run 影子结果。
- 外部效果：blocked
- 正式库写入：False

## 安全边界
- 不调用真实外部API；不触发n8n；不发送企业微信真实消息。
- 不写正式库、正式向量库、正式数据库。
- 不调用券商接口；不自动交易；不下单。
- 不触碰本职工作系统。
- 仅允许本地 dry_run 影子样本与本地证据索引联动。
