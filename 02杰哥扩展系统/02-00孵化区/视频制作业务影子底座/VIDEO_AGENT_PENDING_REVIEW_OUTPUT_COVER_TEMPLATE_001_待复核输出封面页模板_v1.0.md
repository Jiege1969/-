# VIDEO_AGENT_PENDING_REVIEW_OUTPUT_COVER_TEMPLATE_001 待复核输出封面页模板

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子封面模板，不是正式交付封面
> 日期：2026-05-08

## 目的

为三候选草案、状态查询回执草案、人工复核问题清单和影子试运行报告统一加上待复核封面，防止被误认为正式视频制作结果、正式发布意见或真实企业微信回复。

## 封面字段

| 字段 | 填写说明 |
|:---|:---|
| `output_id` | 影子输出编号 |
| `output_type` | 三候选草案/状态回执草案/复核问题/试运行报告 |
| `related_shadow_task_id` | 关联影子任务编号 |
| `review_status` | 固定为 `pending_human_review` |
| `formal_execution_allowed` | 固定为 `false` |
| `redline_status` | 是否命中红线 |
| `missing_fields` | 待补字段 |
| `human_review_items` | 待人工复核项 |
| `boundary_statement` | 固定边界说明 |

## 固定边界说明

本输出仅为视频制作业务影子底座的待复核草案，不代表真实生成、渲染、发布、上传、外发、企业微信真实发送或正式业务结论。

## 边界

本模板不生成正式文档、不外发、不触发企业微信或 n8n。
