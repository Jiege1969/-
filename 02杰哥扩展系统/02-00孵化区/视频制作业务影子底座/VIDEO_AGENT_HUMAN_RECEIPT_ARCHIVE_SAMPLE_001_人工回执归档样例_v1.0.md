# VIDEO_AGENT_HUMAN_RECEIPT_ARCHIVE_SAMPLE_001 人工回执归档样例

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子归档样例，不是真实档案库
> 日期：2026-05-08

## 目的

演示人工对三候选草案、局部修正草案或发布门禁草案的复核回执如何被影子层归档，形成可追溯链条。

## 归档字段

| 字段 | 示例 |
|:---|:---|
| `receipt_id` | `HR-VIDEO-SHADOW-YYYYMMDD-001` |
| `related_shadow_task_id` | 空白，待人工填写 |
| `reviewer` | 空白，待人工填写 |
| `review_time` | 空白，待人工填写 |
| `decision_type` | accept_shadow/revise_shadow/block_redline/need_more_info |
| `decision_note` | 空白，待人工填写 |
| `related_draft_assets` | 空白，待人工填写 |
| `next_shadow_action` | 空白，待人工填写 |

## 归档规则

- 人工回执只影响影子任务状态。
- 回执不能直接放行真实生成、渲染、发布或外发。
- 回执中出现可迁移经验时，只进入进化候选，不直接改正式规则。

## 边界

本样例不建立真实数据库，不读取真实用户，不覆盖历史审计记录。
