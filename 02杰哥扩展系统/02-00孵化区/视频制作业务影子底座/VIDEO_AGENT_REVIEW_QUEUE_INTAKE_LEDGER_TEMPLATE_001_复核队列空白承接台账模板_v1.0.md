# VIDEO_AGENT_REVIEW_QUEUE_INTAKE_LEDGER_TEMPLATE_001 复核队列空白承接台账模板 v1.0

- 资产类型：空白台账模板
- 施工等级：W1/R0
- 适用范围：视频制作影子复核队列
- 状态：草案模板，不连接真实台账

## 台账字段

| 字段 | 填写说明 |
|---|---|
| intake_id | 承接编号 |
| shadow_task_id | 影子任务编号 |
| source_gap_id | 来源缺口编号 |
| review_queue | 复核队列 |
| primary_owner_role | 主责任角色 |
| intake_time | 承接时间，占位 |
| expected_output | 预期输出：问题、回执、草案、阻断记录 |
| current_status | 待承接、处理中、待人工补充、已关闭、红线阻断 |
| blocker_reason | 阻断原因 |
| real_system_triggered | 必须为否 |
| handoff_record | 对齐回传记录 |

## 空白模板

| intake_id | shadow_task_id | source_gap_id | review_queue | primary_owner_role | current_status | expected_output | blocker_reason | real_system_triggered | handoff_record |
|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待承接 | 待填写 | - | 否 | 待填写 |

## 使用边界

- 不写真实数据库。
- 不创建真实工单。
- 不分派真实人员。
- 不外发企业微信。
- 不触发 n8n。
