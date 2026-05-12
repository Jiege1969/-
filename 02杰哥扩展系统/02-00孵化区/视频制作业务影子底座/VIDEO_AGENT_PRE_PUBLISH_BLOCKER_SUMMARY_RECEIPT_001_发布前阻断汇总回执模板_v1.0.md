# VIDEO_AGENT_PRE_PUBLISH_BLOCKER_SUMMARY_RECEIPT_001 发布前阻断汇总回执模板 v1.0

- 资产类型：阻断汇总回执模板
- 施工等级：W1/R0
- 适用范围：发布前四件套、多平台检查、门禁一致性检查后的阻断汇总
- 状态：草案模板

## 模板用途

当发布前检查发现多个缺口时，生成统一阻断汇总，告诉使用者为什么不能发布、缺口归属哪个队列、下一步该补什么。该模板不触发真实发布。

## 汇总字段

| 字段 | 填写说明 |
|---|---|
| summary_id | 汇总编号 |
| task_id | 视频任务编号 |
| checked_scope | 检查范围 |
| blocker_count | 阻断数量 |
| blockers | 阻断项列表 |
| mapped_review_queues | 已映射复核队列 |
| highest_risk_level | 最高风险等级 |
| publish_decision | 阻断、待补、可进入人工放行 |
| next_action | 下一步 |
| real_system_triggered | 必须为否 |

## 阻断项格式

| blocker_id | blocker_type | blocker_reason | review_queue | owner_role | close_condition |
|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 固定规则

1. 任一红线阻断存在时，发布决策必须为“阻断”。
2. 四件套缺失时，发布决策必须为“待补”或“阻断”。
3. 多平台检查未完成时，不能给出“一键全平台发布”结论。
4. 本模板只汇总阻断，不执行补齐、不发消息、不发布。
