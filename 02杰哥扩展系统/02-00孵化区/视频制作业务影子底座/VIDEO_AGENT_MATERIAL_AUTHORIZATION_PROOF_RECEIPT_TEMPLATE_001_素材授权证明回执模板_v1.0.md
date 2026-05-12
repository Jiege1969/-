# VIDEO_AGENT_MATERIAL_AUTHORIZATION_PROOF_RECEIPT_TEMPLATE_001 素材授权证明回执模板 v1.0

- 资产类型：人工复核回执模板
- 施工等级：W1/R0
- 适用范围：视频素材、图片、音乐、字体、音效等授权证明复核
- 状态：草案模板

## 模板用途

记录素材是否具备可追溯授权证明。该模板只记录复核结果，不读取素材库、不下载素材、不调用外部素材 API。

## 回执字段

| 字段 | 填写说明 |
|---|---|
| receipt_id | 回执编号 |
| task_id | 视频任务编号 |
| material_id | 素材编号 |
| material_type | 视频、图片、音乐、字体、音效、其他 |
| source_name | 来源名称 |
| source_url_or_note | 来源链接或线下说明 |
| license_type | 授权类型 |
| commercial_use_allowed | 是否允许商业使用 |
| attribution_required | 是否需要署名 |
| proof_archived | 证明是否已归档 |
| reviewer | 复核人 |
| review_result | 通过、待补、驳回 |
| blocker_reason | 阻断原因 |
| real_system_triggered | 必须为否 |

## 空白回执

| receipt_id | task_id | material_id | material_type | source_name | source_url_or_note | license_type | commercial_use_allowed | attribution_required | proof_archived | reviewer | review_result | blocker_reason | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待确认 | 待确认 | 待确认 | 待确认 | 待填写 | 待确认 | 待填写 | 否 |

## 固定规则

1. 素材授权证明缺失时，真实渲染和发布均保持阻断。
2. 仅有素材来源名称不等于授权证明。
3. 需要署名但未确认署名方式时，发布保持阻断。
4. 本模板不得触发素材读取、下载、上传、渲染或发布。
