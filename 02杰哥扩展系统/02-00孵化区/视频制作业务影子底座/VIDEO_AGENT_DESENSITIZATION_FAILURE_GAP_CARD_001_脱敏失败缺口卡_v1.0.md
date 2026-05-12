# VIDEO_AGENT_DESENSITIZATION_FAILURE_GAP_CARD_001 脱敏失败缺口卡

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子缺口卡，不是真实数据处理记录
> 日期：2026-05-08

## 目的

当输入包含敏感信息且无法进入影子试运行时，记录脱敏失败原因和下一步人工处理要求。

## 缺口字段

| 字段 | 说明 |
|:---|:---|
| `gap_id` | 缺口编号 |
| `source_input_id` | 来源输入编号 |
| `failure_category` | 个人信息/凭据/真实素材/客户信息/发布指令/其他 |
| `sensitive_summary` | 只写类别，不摘录敏感原文 |
| `required_action` | 要求用户重提脱敏版本或人工确认 |
| `redline_hit` | 是否命中红线 |
| `allowed_next_step` | 允许的下一步影子动作 |
| `not_saved_content_statement` | 不保存敏感原文声明 |

## 处理规则

- 不摘录敏感原文。
- 不保存凭据、cookie、token 或真实素材路径。
- 不能脱敏时，停止进入草案链路。
- 需要真实系统处理时，只登记阻断。

## 边界

本卡不处理真实个人信息，不做真实数据清洗，不写正式隐私台账。
