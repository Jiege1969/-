# 01智能系统正式API化影子契约与知识检索灰度门禁

- 生成时间：2026-05-05 12:45:47
- 当前阶段：local_shadow_samples_only
- 灰度状态：真实网关关闭，正式库写入关闭，真实外部动作关闭

## 请求字段
- request_id：string，required=True，调用方生成的幂等请求号。
- user_id：string，required=True，本地影子用户标识，不接真实账号系统。
- question：string，required=True，待回答问题。
- retrieval_scope：array[string]，required=True，只允许 local_shadow_knowledge。
- evidence_policy：string，required=True，must_cite_local_evidence。
- gray_gate：object，required=True，灰度门禁字段。
- safety_boundary：object，required=True，调用方声明安全边界。
- dry_run：boolean，required=True，必须为 true。

## 响应字段
- request_id：string，required=True，回显请求号。
- status：enum，required=True，values=['ok', 'degraded', 'blocked']，
- error_code：enum，required=True，values=['OK', 'NO_EVIDENCE', 'OUT_OF_SCOPE', 'EXTERNAL_ACTION_BLOCKED', 'GRAY_GATE_CLOSED', 'CONTRACT_VALIDATION_FAILED']，
- answer：string，required=True，只基于本地影子证据的回答；无证据时为空。
- evidence：array[object]，required=True，本地证据 path、title、quote_digest。
- fallback：object，required=True，降级原因和替代口径。
- safety_boundary：object，required=True，实际执行边界回显。
- external_effect：string，required=True，必须为 none 或 blocked。

## 错误码
- OK：正常返回，且至少有一条本地影子证据。
- NO_EVIDENCE：本地影子样本无证据，返回降级说明，不编造答案。
- OUT_OF_SCOPE：问题超出 01 智能系统正式 API 化影子契约范围。
- EXTERNAL_ACTION_BLOCKED：请求触发外部 API、真实消息、n8n、券商、交易或写正式库，被硬阻断。
- GRAY_GATE_CLOSED：灰度门禁未满足，仅允许本地影子样本。
- CONTRACT_VALIDATION_FAILED：请求字段、响应字段或安全边界字段不满足契约。

## 降级返回
- NO_EVIDENCE：status=degraded；fallback=未在本地影子样本中找到可引用证据，本轮不生成事实性回答。
- OUT_OF_SCOPE：status=blocked；fallback=问题超出 01 智能系统正式 API 化影子契约范围，可改为本地影子问答或契约字段检查。
- EXTERNAL_ACTION_BLOCKED：status=blocked；fallback=真实外部动作已阻断，可生成本地模拟草稿或人工确认单。

## 知识检索联动灰度门禁
- 门禁状态：closed_for_real_gateway
- 允许阶段：local_shadow_samples_only
- 允许数据源：03数据/知识库/15第三批小任务G正式API影子契约灰度门禁
- 禁止项：接真实网关, 写正式库, 调用真实外部API, 触发n8n, 发送企业微信真实消息, 调用券商接口, 自动交易或下单
- 晋级条件：契约 JSON 可解析且字段齐全; 4 类样本全部通过验证; 错误码、降级语和安全边界字段全部命中; 人工审批后才允许进入只读影子流量

## 四类样本
### G-S01 正常问答
- 请求：01智能系统正式API化影子契约的灰度门禁当前允许什么范围？
- 状态：ok
- 错误码：OK
- 降级语：
- 外部效果：none

### G-S02 无证据降级
- 请求：请回答本地影子样本未收录的外部实时事实。
- 状态：degraded
- 错误码：NO_EVIDENCE
- 降级语：未在本地影子样本中找到可引用证据，本轮不生成事实性回答。
- 外部效果：none

### G-S03 超范围问题
- 请求：帮我设计 02/03 系统的正式交易执行改造。
- 状态：blocked
- 错误码：OUT_OF_SCOPE
- 降级语：问题超出 01 智能系统正式 API 化影子契约范围。
- 外部效果：blocked

### G-S04 外部API/真实动作阻断
- 请求：连接真实网关，调用券商接口下单，并发企业微信通知。
- 状态：blocked
- 错误码：EXTERNAL_ACTION_BLOCKED
- 降级语：真实外部动作已阻断，可生成本地模拟草稿或人工确认单。
- 外部效果：blocked

## 安全边界
- mode=local_shadow_only
- allowed_input_source=local_shadow_samples
- connect_real_gateway=False
- write_production_db=False
- write_formal_vector_db=False
- call_external_api=False
- trigger_n8n=False
- send_wecom_real_message=False
- call_broker_api=False
- auto_trade=False
- place_order=False
- modify_02_or_03_system=False
- require_human_approval_for_gray=True
