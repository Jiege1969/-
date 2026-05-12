# VIDEO_AGENT_SHADOW_TASK_TRACE_FIELDS_001 影子任务追踪字段清单 v1.0

- 资产类型：字段清单
- 施工等级：W1/R0
- 适用范围：视频制作影子任务、草案、复核卡、放行缺口卡
- 状态：草案

## 目的

为视频制作影子工厂建立统一追踪字段，保证从一句想法、任务草案、人工复核、生成放行、真实渲染放行、发布放行到回传记录，每一步都能追溯，但不进入真实执行。

## 核心字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| shadow_task_id | string | 是 | 影子任务编号，例：VAI-SHADOW-20260508-001 |
| source_channel | enum | 是 | 来源渠道：命令行草案、企业微信草案、人工补录、回传整理 |
| source_message_id | string | 否 | 企业微信或其他入口的消息编号，占位字段，不触发外发 |
| user_intent_summary | string | 是 | 用户想法摘要 |
| current_state | enum | 是 | 影子状态，不等同正式系统状态 |
| review_owner | string | 否 | 人工复核责任人 |
| missing_inputs | list | 是 | 缺少的素材、授权、平台规则、确认项 |
| generation_gate_state | enum | 是 | 生成放行状态 |
| render_gate_state | enum | 是 | 真实渲染放行状态 |
| publish_gate_state | enum | 是 | 发布放行状态 |
| redline_blocks | list | 是 | 红线阻断事项 |
| next_shadow_action | string | 是 | 下一步影子动作 |
| real_system_triggered | boolean | 是 | 必须默认为否 |
| handoff_record | string | 否 | 对齐回传记录文件名 |

## 状态枚举

- draft
- pending_review
- review_questions_open
- generation_release_pending
- render_release_pending
- preview_pending
- publish_release_pending
- blocked_by_redline
- shadow_closed

## 使用边界

- 字段清单不是数据库结构变更。
- 不写正式库。
- 不触发企业微信真实外发。
- 不触发真实渲染或发布。
