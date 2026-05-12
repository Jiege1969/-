# 01智能系统第六批小任务V：API影子契约错误码与降级标准固化

- 生成时间：2026-05-05 13:11:29
- 执行模式：local_shadow_only
- 写入策略：只写本地样本和文档；正式库/正式知识库/正式向量库/正式数据库写入禁用

## 固化字段

### 请求字段
- request_id：string，required=True
- caller：string，required=True
- question：string，required=True
- evidence_ids：array[string]，required=True
- dry_run：boolean，required=True
- safety_boundary：object，required=True

### 响应字段
- request_id：string，required=True
- status：enum，required=True
- error_code：enum，required=True
- answer：string，required=True
- evidence：array[object]，required=True
- degrade_message：string，required=True
- safe_to_show_user：boolean，required=True
- requires_human_review：boolean，required=True
- external_effect：string，required=True
- formal_store_write：boolean，required=True
- safety_boundary：object，required=True

## 错误码与固定降级语
- OK：status=ok；severity=info；请求命中本地影子契约与本地允许证据，安全字段闭合，可以返回本地影子结果。；降级语：无，正常返回。
- INSUFFICIENT_EVIDENCE：status=degraded；severity=warning；证据缺失、证据不足或证据不能支撑结论，不得生成事实性回答。；降级语：本地证据不足以支撑结论，本轮只返回降级说明，不生成事实性回答。
- UNAUTHORIZED_EXTERNAL_API：status=blocked；severity=critical；请求越权调用真实外部 API、n8n、企业微信真实消息、券商接口或真实动作，必须硬阻断。；降级语：真实外部 API 或真实动作已被安全边界阻断，本轮仅保留本地 dry_run 影子记录。
- SYSTEM_EXCEPTION_DEGRADED：status=degraded；severity=error；本地影子处理出现可恢复系统异常，禁止外扩重试真实服务，按固定降级语返回。；降级语：本地影子处理出现系统异常，本轮已降级为人工复核提示，不触发任何外部动作。
- CONTRACT_FIELD_MISSING：status=blocked；severity=error；请求或响应缺少 API 影子契约必需字段，必须阻断进入后续处理。；降级语：影子契约字段不完整，本轮不继续处理，请补齐必需字段后重新本地验证。
- SAFETY_FIELD_VIOLATION：status=blocked；severity=critical；安全字段声明与执行边界不一致，或存在真实动作开关打开的迹象。；降级语：安全字段未闭合，本轮阻断处理并要求人工复核。

## 降级标准
- evidence_required：所有事实性回答必须绑定本地影子证据；无证据、证据不足、证据不匹配均返回 INSUFFICIENT_EVIDENCE。
- external_api_forbidden：任何真实外部 API、n8n、企业微信真实消息、券商接口、下单或自动交易请求均返回 UNAUTHORIZED_EXTERNAL_API。
- system_exception：本地异常不得升级为真实服务调用；统一返回 SYSTEM_EXCEPTION_DEGRADED 并保留人工复核提示。
- contract_fields：请求字段、响应字段、安全字段缺失时返回 CONTRACT_FIELD_MISSING 或 SAFETY_FIELD_VIOLATION。
- formal_store：正式库、正式知识库、正式向量库、正式数据库写入全部保持 False。

## 四个样本
- V-S01 成功：status=ok；error_code=OK；external_effect=none
- V-S02 证据不足：status=degraded；error_code=INSUFFICIENT_EVIDENCE；external_effect=none
- V-S03 越权外部API：status=blocked；error_code=UNAUTHORIZED_EXTERNAL_API；external_effect=blocked
- V-S04 系统异常降级：status=degraded；error_code=SYSTEM_EXCEPTION_DEGRADED；external_effect=none

## 安全字段
- safe_to_show_user：只代表本地影子输出可展示，不代表真实动作可执行。
- requires_human_review：证据不足、系统异常、越权外部动作均为 true。
- external_effect：只允许 none 或 blocked。
- formal_store_write：固定为 false。

## 安全边界
- 不调用真实外部API；不触发 n8n；不发企业微信真实消息；不写正式库/正式向量库/正式数据库。
- 不调用券商接口；不自动交易；不下单；不触碰本职工作系统。
