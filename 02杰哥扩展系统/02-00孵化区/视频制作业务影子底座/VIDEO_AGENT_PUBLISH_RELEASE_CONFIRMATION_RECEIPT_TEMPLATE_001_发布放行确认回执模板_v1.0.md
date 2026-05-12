# VIDEO_AGENT_PUBLISH_RELEASE_CONFIRMATION_RECEIPT_TEMPLATE_001 发布放行确认回执模板

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子回执模板，不是真实发布许可
> 日期：2026-05-08

## 目的

为未来人工讨论“是否具备发布放行条件”预留影子回执格式。该模板不代表发布被批准，不触发上传、发布、外发或企业微信真实发送。

## 回执字段

| 字段 | 说明 |
|:---|:---|
| `release_receipt_id` | 影子放行回执编号 |
| `related_shadow_task_id` | 关联影子任务编号 |
| `four_piece_check_reference` | 四件套检查引用 |
| `human_reviewer` | 空白，等待人工填写 |
| `review_time` | 空白，等待人工填写 |
| `release_decision_type` | ready_for_human_publish_discussion / not_ready / blocked |
| `blocking_items` | 阻断事项 |
| `not_real_publish_statement` | 固定边界说明 |

## 固定边界说明

本回执只说明影子层发布前条件是否可进入人工讨论，不代表真实发布许可，不执行上传、发布、外发、群发或平台操作。

## 边界

本模板不接平台、不接账号、不接企业微信、不触发 n8n。
