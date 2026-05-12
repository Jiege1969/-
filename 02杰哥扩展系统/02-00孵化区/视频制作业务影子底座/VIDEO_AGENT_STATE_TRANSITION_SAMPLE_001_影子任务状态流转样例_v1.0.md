# VIDEO_AGENT_STATE_TRANSITION_SAMPLE_001 影子任务状态流转样例

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子样例，不是真实状态机
> 日期：2026-05-08

## 目的

演示一个脱敏视频想法在影子层如何从输入、澄清、三候选草案、人工选择、待复核、关闭或阻断之间流转。该样例不创建真实任务，不读取素材，不调用模型、渲染、发布或企业微信真实链路。

## 状态流转样例

| 步骤 | 输入条件 | 影子状态 | 输出 |
|:---|:---|:---|:---|
| 1 | 收到脱敏想法 | `draft_intake` | 建立影子输入记录 |
| 2 | 平台、时长、风格缺失 | `needs_clarification` | 生成澄清问题 |
| 3 | 用户补充关键信息 | `draft_ready` | 进入三候选草案生成准备 |
| 4 | 形成三候选文本草案 | `pending_review` | 输出待复核草案 |
| 5 | 人工选择其一并提出修改 | `revision_requested` | 记录局部修正范围 |
| 6 | 修正草案完成 | `human_review_needed` | 进入人工复核 |
| 7 | 复核通过影子闭环 | `shadow_closed` | 关闭影子任务 |
| 8 | 命中真实生成、发布、外发要求 | `blocked_by_redline` | 登记阻断和替代影子动作 |

## 追踪字段

- `shadow_task_id`
- `source_input_type`
- `current_shadow_status`
- `last_transition_reason`
- `missing_fields`
- `human_review_items`
- `redline_hit`
- `next_shadow_action`

## 边界

所有状态只属于影子试运行。任何涉及真实素材、真实生成、真实渲染、真实发布、真实企业微信、n8n、服务或端口的动作，只能进入阻断登记。
