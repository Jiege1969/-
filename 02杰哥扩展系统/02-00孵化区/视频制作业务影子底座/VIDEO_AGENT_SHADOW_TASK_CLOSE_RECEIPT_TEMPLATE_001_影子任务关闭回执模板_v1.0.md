# VIDEO_AGENT_SHADOW_TASK_CLOSE_RECEIPT_TEMPLATE_001 影子任务关闭回执模板

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子关闭模板，不关闭真实任务
> 日期：2026-05-08

## 使用场景

当影子任务完成待复核草案、被人工确认影子闭环，或命中红线后转为阻断关闭时，使用本模板生成关闭回执。

## 关闭回执字段

| 字段 | 说明 |
|:---|:---|
| `close_receipt_id` | 关闭回执编号 |
| `shadow_task_id` | 影子任务编号 |
| `close_type` | completed_shadow_loop/blocked_by_redline/cancelled_shadow/incomplete_gap |
| `close_reason` | 关闭原因 |
| `final_shadow_status` | 最终影子状态 |
| `related_assets` | 关联影子资产 |
| `human_review_reference` | 人工复核引用 |
| `not_formal_release_statement` | 固定边界说明 |

## 固定说明

影子任务关闭不代表真实视频任务完成，不代表生成、渲染、发布、上传、外发或企业微信真实发送完成。

## 边界

本模板只关闭影子任务，不关闭真实任务，不写正式业务库，不删除历史资料。
