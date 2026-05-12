# VIDEO_AGENT_STANDARD_HUMAN_REVIEW_QUESTION_TEMPLATE_001 标准人工复核问题模板

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子复核模板，不是正式审核意见
> 日期：2026-05-08

## 使用场景

当影子层形成三候选草案、局部修正草案、发布前检查草案或企业微信回执草案时，使用本模板生成待人工复核问题。

## 复核问题字段

| 字段 | 填写要求 |
|:---|:---|
| `review_item_id` | 复核项编号 |
| `related_shadow_task_id` | 关联影子任务编号 |
| `related_asset` | 关联草案或样例文件 |
| `question_type` | 内容/版权/平台规范/AI标识/隐私/放行/其他 |
| `question_text` | 需要人工判断的问题 |
| `evidence_pointer` | 指向影子文件、用户脱敏输入或规则卡 |
| `risk_level` | low/medium/high/blocking |
| `suggested_shadow_action` | 修改草案/补充信息/登记阻断/保持待复核 |
| `human_decision` | 空白，等待人工填写 |
| `decision_time` | 空白，等待人工填写 |

## 固定边界

- 不替代人工复核。
- 不输出正式发布意见。
- 不确认真实生成、真实渲染、真实发布或真实外发。
- 不读取企业微信凭据或真实消息。
