# VIDEO_AGENT_MULTI_PLATFORM_PRE_PUBLISH_CHECK_RECEIPT_TEMPLATE_001 多平台发布前检查回执模板 v1.0

- 资产类型：人工检查回执模板
- 施工等级：W1/R0
- 适用范围：多平台发布前差异化人工复核
- 状态：草案模板

## 模板用途

记录每个平台发布前检查结果。该模板只记录人工复核意见，不连接平台、不读取账号、不执行发布。

## 回执字段

| 字段 | 填写说明 |
|---|---|
| receipt_id | 回执编号 |
| task_id | 视频任务编号 |
| platform | 平台名称 |
| title_check | 标题是否适配 |
| tag_check | 标签是否适配 |
| cover_check | 封面是否适配 |
| ai_label_check | AI 标识是否确认 |
| aspect_duration_check | 画幅/时长是否适配 |
| material_note_check | 素材说明是否需要补充 |
| platform_rule_check | 平台规则是否已核对 |
| review_result | 通过、待补、驳回 |
| blocker_reason | 阻断原因 |
| reviewer | 复核人 |
| real_system_triggered | 必须为否 |

## 空白回执

| receipt_id | task_id | platform | title_check | tag_check | cover_check | ai_label_check | aspect_duration_check | material_note_check | platform_rule_check | review_result | blocker_reason | reviewer | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待填写 | 待填写 | 否 |

## 固定规则

1. 每个平台必须单独出具检查结果。
2. 一个平台通过不代表其他平台通过。
3. 平台规则或 AI 标识未确认时，该平台保持发布阻断。
4. 本模板不得触发平台连接、账号读取、上传或发布。
