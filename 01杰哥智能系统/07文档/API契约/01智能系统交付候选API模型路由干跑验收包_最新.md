# 01智能系统交付候选API/模型路由干跑验收包

批次：并行小任务H  
日期：2026-05-05  
范围：仅 01杰哥智能系统新增验收包文件；固定回收报告写入 00杰哥系统总管并行回收目录。

## 验收目标

本包用于验证 01智能系统交付候选 API/模型路由闭环，覆盖：

1. 标准任务单读取。
2. API契约字段与安全闸口校验。
3. 模型路由选择。
4. 中台能力计划。
5. 失败码降级。
6. receipt输出。

全流程均为 `dry_run`。真实模型调用、n8n触发、企业微信发送、正式库写入、券商接口、自动交易、下单和外部网络请求均保持关闭。

## 文件清单

- 主包 JSON：`D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\delivery_candidate_api_model_route_dry_run_package_latest.json`
- 链路 trace JSON：`D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\standard_task_to_receipt_trace_latest.json`
- 失败降级矩阵 JSON：`D:\杰哥智能化系统\01杰哥智能系统\03数据\交付候选API模型路由干跑验收\failure_fallback_matrix_latest.json`
- 只读验证脚本：`D:\杰哥智能化系统\01杰哥智能系统\02脚本\验证01智能系统交付候选API模型路由干跑验收包.ps1`

## 干跑链路

### 1. 标准任务单

标准任务单必须包含 `task_id`、`schema_version`、`source`、`intent`、`input`、`routing_hint`、`safety`、`dry_run`、`receipt_required`。

硬闸口：

- `dry_run=true`
- `safety.real_action_allowed=false`
- `safety.external_call_allowed=false`
- `safety.formal_write_allowed=false`
- `safety.model_call_allowed=false`
- `receipt_required=true`

### 2. API契约

API契约只作为本地干跑契约，不提供真实 HTTP 入口，不注册 webhook，不写正式库。请求契约和响应契约均在主包 JSON 中声明，验收脚本只做本地解析。

### 3. 模型路由选择

模型路由器为 `delivery_candidate_shadow_model_router`：

- `invocation=disabled`
- `selection_mode=label_only`
- `output_mode=planned_receipt_only`
- `real_model_call=false`

模型路由仅选择模型家族标签、提示词配置标签和降级标签，不发送 prompt，不拉起模型服务，不读取远程模型。

### 4. 中台能力计划

中台计划包含本地任务契约解析、影子模型路由标签选择、n8n干跑计划、统一消息 receipt 输出、SQLite/Redis 影子计划。所有步骤均为本地计划或回执，不触发外部服务。

### 5. 失败码降级

主要失败码：

- `DRYRUN_API_400_SCHEMA_INVALID`：任务单字段或版本不合法，输出 `VALIDATION_FAILED`。
- `DRYRUN_ROUTE_404_NO_SAFE_ROUTE`：无安全路由，输出 `BLOCKED_NO_SAFE_ROUTE`。
- `DRYRUN_MODEL_451_REAL_MODEL_DISABLED`：真实模型需求被关闭，降级为标签计划回执。
- `DRYRUN_MW_452_EXTERNAL_TRIGGER_DISABLED`：外部触发需求被关闭，降级为影子计划。
- `DRYRUN_DB_453_FORMAL_WRITE_DISABLED`：正式写入需求被关闭，降级为影子写入计划。

### 6. receipt输出

receipt 必须包含 `receipt_id`、`task_id`、`dry_run`、`status`、`selected_route`、`middleware_plan`、`fallback`、`external_calls`、`blocked_actions`、`evidence`、`created_at`。

验收要求：

- `external_calls=[]`
- `real_model_call=false`
- 不写正式库。
- 不连接真实 Redis。
- 高风险动作进入 `blocked_actions`。

## 验收命令

```powershell
powershell -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\01杰哥智能系统\02脚本\验证01智能系统交付候选API模型路由干跑验收包.ps1"
```

该脚本为只读本地解析：只读取本包 JSON/Markdown 并输出结果，不写文件、不联网、不触发模型或外部服务。
