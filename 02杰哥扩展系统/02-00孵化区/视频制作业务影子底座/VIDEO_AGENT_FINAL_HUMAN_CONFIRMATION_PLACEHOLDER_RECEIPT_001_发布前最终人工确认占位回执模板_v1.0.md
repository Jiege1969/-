# VIDEO_AGENT_FINAL_HUMAN_CONFIRMATION_PLACEHOLDER_RECEIPT_001 发布前最终人工确认占位回执模板 v1.0

- 资产类型：最终人工确认占位回执模板
- 施工等级：W1/W2 低风险影子施工
- 适用范围：发布前所有门禁齐备后的最终人工确认
- 状态：草案模板

## 模板用途

当发布前门禁总览显示全部材料齐备时，用本模板记录人工是否同意进入下一步总管判断或正式发布链路评估。该模板不触发真实发布。

## 回执字段

| 字段 | 填写说明 |
|---|---|
| receipt_id | 回执编号 |
| task_id | 视频任务编号 |
| gate_overview_record | 发布前门禁总览记录 |
| blocker_summary_record | 发布前阻断汇总记录 |
| all_gates_complete | 是否全部门禁齐备 |
| final_human_decision | 同意提交总管判断、待补、驳回 |
| decision_person | 确认人 |
| decision_time | 确认时间 |
| remaining_notes | 备注 |
| real_system_triggered | 必须为否 |

## 空白回执

| receipt_id | task_id | gate_overview_record | blocker_summary_record | all_gates_complete | final_human_decision | decision_person | decision_time | remaining_notes | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待确认 | 待确认 | 待填写 | 待填写 | 待填写 | 否 |

## 固定规则

1. 最终人工确认只允许进入“提交总管判断/待补/驳回”，不直接发布。
2. 门禁总览或阻断汇总缺失时，本回执不得标记为通过。
3. 本模板不得触发发布工具、平台操作、企业微信真实外发或 n8n。
