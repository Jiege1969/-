# VIDEO_AGENT_AI_LABEL_CONFIRMATION_RECEIPT_TEMPLATE_001 AI标识确认回执模板 v1.0

- 资产类型：人工确认回执模板
- 施工等级：W1/R0
- 适用范围：发布前 AI 生成内容标识确认
- 状态：草案模板

## 模板用途

在视频准备发布前，人工确认是否已在目标平台按要求勾选或标注“内容由 AI 生成”。该模板只记录确认结果，不操作平台。

## 回执字段

| 字段 | 填写说明 |
|---|---|
| receipt_id | 回执编号 |
| task_id | 视频任务编号 |
| platform | 平台名称 |
| ai_label_required | 是否需要 AI 标识 |
| ai_label_confirmed | 是否已人工确认 |
| confirmation_method | 勾选、文案标注、平台弹窗确认、其他 |
| confirmer | 确认人 |
| confirmation_time | 确认时间 |
| remaining_gap | 仍缺事项 |
| publish_gate_effect | 对发布放行的影响 |
| real_system_triggered | 必须为否 |

## 空白回执

| receipt_id | task_id | platform | ai_label_required | ai_label_confirmed | confirmation_method | confirmer | confirmation_time | remaining_gap | publish_gate_effect | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待确认 | 待确认 | 待填写 | 待填写 | 待填写 | 待填写 | 不单独构成发布放行 | 否 |

## 固定规则

1. AI 标识确认只是发布前条件之一，不等于发布放行。
2. 未确认 AI 标识时，发布命令必须拒绝。
3. 本模板不得触发平台操作。
