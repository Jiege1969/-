# VIDEO_AGENT_GAP_TO_REVIEW_QUEUE_MAPPING_001 缺口到复核队列映射

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子映射表，不是真实队列
> 日期：2026-05-08

## 目的

把状态查询缺口、草案缺口、平台规范缺口、素材授权缺口和红线阻断缺口映射到对应的人工复核队列，避免缺口被误写成结论。

## 映射规则

| 缺口类型 | 进入队列 | 默认风险 | 影子动作 |
|:---|:---|:---|:---|
| `missing_shadow_task_id` | 输入澄清队列 | medium | 请求补充任务编号或上下文 |
| `missing_platform_rule` | 平台规范复核队列 | high | 补平台规则来源卡 |
| `missing_asset_authorization` | 素材授权复核队列 | high | 补素材授权字段 |
| `missing_human_decision` | 人工复核队列 | medium | 等待人工回执 |
| `release_gate_unclear` | 发布门禁复核队列 | blocking | 只登记阻断，不放行 |
| `real_system_request` | 红线阻断队列 | blocking | 登记红线并转影子替代动作 |

## 输出字段

- `gap_id`
- `gap_type`
- `source_asset`
- `target_review_queue`
- `risk_level`
- `shadow_action`
- `human_review_required`
- `formal_execution_allowed`

## 边界

本映射表不创建真实队列，不推送企业微信，不写正式任务库，不自动升级正式规则。
