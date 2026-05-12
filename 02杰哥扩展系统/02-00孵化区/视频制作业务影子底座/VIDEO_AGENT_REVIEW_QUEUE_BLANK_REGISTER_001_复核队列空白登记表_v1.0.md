# VIDEO_AGENT_REVIEW_QUEUE_BLANK_REGISTER_001 复核队列空白登记表

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子登记表，不是真实队列表
> 日期：2026-05-08

## 目的

为缺口、草案、回执和红线阻断提供统一的人工复核登记格式。该表不接真实任务流，不通知真实人员。

## 登记字段

| 字段 | 说明 |
|:---|:---|
| `queue_item_id` | 复核队列项编号 |
| `source_gap_id` | 来源缺口编号 |
| `source_asset` | 来源影子资产 |
| `review_queue_type` | 输入澄清/平台规范/素材授权/人工复核/发布门禁/红线阻断 |
| `risk_level` | low/medium/high/blocking |
| `assigned_reviewer` | 空白，等待人工填写 |
| `created_time` | 空白，等待人工填写 |
| `review_due_note` | 空白，等待人工填写 |
| `current_status` | pending_review |
| `human_decision` | 空白，等待人工填写 |

## 边界

本表只作为影子登记模板，不创建真实排队任务，不接企业微信通知，不写正式库。
