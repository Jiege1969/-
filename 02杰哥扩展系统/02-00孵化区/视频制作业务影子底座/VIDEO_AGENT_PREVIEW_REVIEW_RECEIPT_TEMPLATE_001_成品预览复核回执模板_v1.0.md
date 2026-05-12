# VIDEO_AGENT_PREVIEW_REVIEW_RECEIPT_TEMPLATE_001 成品预览复核回执模板 v1.0

- 资产类型：人工复核回执模板
- 施工等级：W1/R0
- 适用范围：成品视频预览后的人工复核
- 状态：草案模板

## 模板用途

记录人工对成品预览的复核结果。该模板只记录复核意见，不触发重新渲染、上传或发布。

## 回执字段

| 字段 | 填写说明 |
|---|---|
| receipt_id | 回执编号 |
| task_id | 视频任务编号 |
| preview_version | 预览版本 |
| aspect_ratio | 画幅，如 9:16 或 16:9 |
| script_match | 文案与成片是否一致 |
| subtitle_check | 字幕是否正确 |
| audio_check | 配音/音量是否可接受 |
| material_check | 素材是否合规、无侵权风险 |
| ai_label_check | AI 标识是否已确认 |
| review_result | 通过、待修改、驳回 |
| required_revision | 需要修改的内容 |
| reviewer | 复核人 |
| real_system_triggered | 必须为否 |

## 空白回执

| receipt_id | task_id | preview_version | aspect_ratio | script_match | subtitle_check | audio_check | material_check | ai_label_check | review_result | required_revision | reviewer | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待确认 | 待填写 | 待填写 | 否 |

## 固定规则

1. 成品预览通过不等于发布放行。
2. 若素材、字幕、配音、AI 标识任一项待确认，发布仍阻断。
3. 本模板不得触发重新渲染或发布。
