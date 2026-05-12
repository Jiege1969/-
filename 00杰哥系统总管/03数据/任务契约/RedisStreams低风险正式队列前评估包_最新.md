# Redis Streams低风险正式队列前评估包

施工批次：并行小任务E  
生成日期：2026-05-05  
负责范围：仅在 `D:\杰哥智能化系统\00杰哥系统总管` 下新增静态评估文件与只读验证脚本。  
当前状态：`shadow_mapping_only`  
目标候选状态：`low_risk_formal_candidate`

## 安全边界

本评估包不连接真实Redis，不启动服务，不触发n8n，不发送企业微信，不写正式库，不调用券商接口，不自动交易。允许动作只有读取本地JSON/Markdown、生成静态评估文档、运行只读字段校验脚本。

## Stream字段

候选stream为 `jiego:task:formal:low_risk:candidate`，仅作为正式升级前设计目标，不在本轮创建。必填字段包括 `task_id`、`schema_version`、`task_type`、`risk_level`、`source_system`、`target_system`、`priority`、`created_at`、`deadline_at`、`idempotency_key`、`payload_json`、`safety_flags_json`、`sqlite_ledger_key`、`trace_id`。

`risk_level` 只允许 `L0_READONLY` 或 `L1_LOW_RISK`。`payload_json` 必须是标准任务单JSON字符串，不能包含密钥、券商凭据、企业微信发送目标或n8n webhook执行地址。`safety_flags_json` 必须明确关闭 n8n、企业微信、券商接口、自动交易和正式库写入。

## 消费组

候选消费组为 `jiego-low-risk-formal-workers`，消费者命名建议为 `worker-{system}-{slot}`。消费组创建只能在正式升级门槛全部满足后，由人工变更单执行。初始consumer数量为1，复评前最多2个。

读取策略候选为 `XREADGROUP COUNT 1 BLOCK 5000`。扩容条件是连续2小时无pending积压，且CPU、内存、GPU排队和SQLite busy率均低于阈值。

## ACK、PENDING、重试、死信

ACK只能发生在幂等锁确认、SQLite落账完成、receipt生成、安全审计通过之后。禁止在SQLite落账前或幂等检查前ACK。

PENDING每60秒检查一次，候选接管阈值为300000毫秒。单组pending超过50条触发人工关注，超过100条阻断扩容。

可重试错误包括 worker超时、本地资源临时繁忙、SQLite busy、GPU队列繁忙。最大重试3次，退避为30秒、120秒、600秒。字段错误、幂等冲突、禁止动作、风险等级超过L1直接进入死信候选。

死信stream候选为 `jiego:task:formal:low_risk:dead_letter`。死信payload必须带原始stream id、task_id、idempotency_key、retry_count、最后错误、死信原因、SQLite ledger key和trace id。

## 幂等与SQLite落账

Redis只作为队列，不作为唯一事实源。SQLite本地台账作为幂等与状态事实源，候选表为 `task_queue_ledger`。同一 `idempotency_key` 处于 queued、processing、completed 时，不允许重复执行业务动作；重复消息只补充审计receipt。

状态流转为 queued、processing、completed、failed_recoverable、dead_lettered、cancelled。状态变更与receipt路径写入必须在同一个SQLite事务中完成。

## 失败回收

worker崩溃时，pending超过接管阈值后由同组健康worker接管，接管前重新读取SQLite状态。SQLite busy按重试策略退避，超过上限进入死信，不允许改写正式库。发现禁止动作时立即安全阻断，不重试。

人工回收只能修正字段后生成新task_id、追加人工确认ticket后重放候选流，或标记cancelled归档receipt。禁止直接改Redis消息、跳过SQLite落账、跳过幂等检查或绕过风险等级门槛。

## GPU排队

低风险正式队列默认 `gpu_required=false`。只允许非交易、非外发、非正式库写入的本地推理辅助任务进入GPU排队。GPU pending上限为2，显存占用阈值为70%，必须保留CPU fallback。GPU队列超过阈值时不扩容consumer。

## 资源占用评估

初始consumer数量为1。CPU阈值60%，内存阈值70%，磁盘剩余不低于20GB，SQLite busy率不高于1%。初始预估低风险流量为每小时30条，10分钟突发20条，payload最大64KB。

必须观测 stream length、pending count、oldest pending idle、ACK P95延迟、retry count、dead letter count、SQLite写入P95延迟、GPU pending count。

## 正式升级门槛

1. 静态契约完整：字段、消费组、ACK/PENDING/重试/死信、幂等、SQLite落账、失败回收、GPU排队、资源评估全部文档化。
2. 评估阶段零真实副作用：未连接Redis、未启动服务、未触发n8n/企业微信/正式库/券商/自动交易。
3. shadow replay通过：本地样例不少于100条，重复幂等键不重复执行业务动作。
4. pending和dead-letter演练通过：接管、三次重试、死信归档、人工回收路径失败项为0。
5. SQLite台账审计通过：字段、事务边界、状态流转、receipt路径可追溯。
6. 资源预算确认：CPU/内存/磁盘/GPU/PENDING阈值已确认，初始consumer不超过1。
7. 人工变更单签字：正式创建stream/group和放开XADD前必须有回滚计划。

## 当前结论

本包可将设计状态标记为 `low_risk_formal_candidate`，但不能启用正式队列，不能连接Redis，不能启动服务。下一步必须先做离线shadow replay、pending/dead-letter演练、资源观测和人工变更单。
