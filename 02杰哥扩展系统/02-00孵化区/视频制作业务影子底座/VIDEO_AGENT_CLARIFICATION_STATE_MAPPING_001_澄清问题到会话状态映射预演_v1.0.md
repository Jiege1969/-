# VIDEO_AGENT_CLARIFICATION_STATE_MAPPING_001_澄清问题到会话状态映射预演_v1.0

> 资产身份：视频创作智能体影子层澄清映射预演
> 阶段：W1/R0
> 状态：流程映射草案，不是真实路由器
> 边界：不改正式入口、不接企业微信、不触发 n8n、不调用模型。

## 样例用途

用于说明澄清问题回答后，应如何更新会话状态字段。该文件只做流程映射，不执行自动路由，不写正式任务。

## 映射表

| 澄清场景 | 需要追问 | 回答后更新字段 | 下一步状态 | 人工门禁 |
|:---|:---|:---|:---|:---|
| 目标不清 | 视频要达成什么目的 | `user_idea_summary`、`current_intent` | `draft_intake` | 否 |
| 平台不清 | 准备投放哪个平台 | `platform_rule_status`、`linked_materials` | `clarification_needed` 或 `option_draft` | 视平台规范缺口而定 |
| 修改范围不清 | 是改标题、开头、正文、分镜还是整体重做 | `current_intent`、`task_stage` | `partial_revision_pending` | 否 |
| 素材风险 | 素材来源和授权是否明确 | `asset_authorization_status`、`manual_review_items` | `human_review_pending` | 是 |
| 生成风险 | 是否要求直接生成视频/配音/封面/字幕 | `redline_hits`、`manual_review_items` | `blocked_for_manager_review` | 是 |
| 发布风险 | 是否要求上传、发布或外发 | `redline_hits`、`manual_review_items` | `blocked_for_manager_review` | 是 |

## 处理原则

1. 低风险澄清只更新影子会话字段。
2. 素材、生成、发布、外发相关澄清必须保留人工门禁。
3. 回答补齐不等于自动进入生成、渲染或发布。
