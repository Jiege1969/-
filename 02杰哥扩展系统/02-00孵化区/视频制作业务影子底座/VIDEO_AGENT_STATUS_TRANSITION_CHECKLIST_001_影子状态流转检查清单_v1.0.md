# VIDEO_AGENT_STATUS_TRANSITION_CHECKLIST_001_影子状态流转检查清单_v1.0

> 资产身份：视频创作智能体影子状态流转检查清单
> 阶段：W1/R0
> 状态：检查清单，不是真实状态机

## 流转检查

| 变更 | 允许条件 | 禁止误解 |
|:---|:---|:---|
| `intake_pending` -> `intake_checked` | 已完成脱敏和红线检查 | 不是接入真实入口 |
| `intake_checked` -> `clarification_needed` | 缺关键字段 | 不是失败 |
| `intake_checked` -> `option_draft_ready` | 字段足够且无红线 | 不是生成放行 |
| `option_draft_ready` -> `human_review_pending` | 已形成待复核文本草案 | 不是发布审核 |
| `human_review_pending` -> `revision_pending` | 人工要求修改 | 不是自动改稿 |
| 任意状态 -> `redline_blocked` | 命中红线 | 不是总管批准 |
| `human_review_pending` -> `evolution_candidate_pending` | 人工回执含可复用经验 | 不是正式规则 |
| 任意状态 -> `shadow_closed` | 满足影子关闭条件 | 不是关闭真实任务 |

## 记录要求

每次状态变化必须填写状态变更日志，且不得自动触发模型、素材读取、渲染、发布、企业微信发送或 n8n。
