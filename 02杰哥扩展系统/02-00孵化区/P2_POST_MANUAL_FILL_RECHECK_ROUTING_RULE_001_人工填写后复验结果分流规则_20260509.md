# P2-S16 人工填写后复验结果分流规则

> 状态：只读分流规则，不是草案生成器，不是放行单。
> 日期：2026-05-09
> 边界：不读取真实材料，不写影子入口，不生成业务草案，不触发外部动作。

## 目的

P2-S15 已建立人工填写后的复验回执模板。P2-S16 规定复验结果如何分流，避免空白回执、失败回执或阻断回执被系统误推进到影子草案候选。

## 分流规则

| 条件 | 分流结果 |
|:---|:---|
| `human_filled=false` | `waiting_manual_fill` |
| 任一复验项为 `pending_manual_fill` | `waiting_manual_fill` |
| 任一复验项为 `fail` | `problem_recovery` |
| 任一复验项为 `blocked` | `blocked_redline_recovery` |
| `human_filled=true` 且四项复验均为 `pass` | `shadow_draft_candidate_discussion` |

## 硬边界

- `shadow_draft_candidate_discussion` 只表示可讨论影子草案候选。
- 不自动生成税收意见、办公材料、视频草案或政策适用结论。
- 不自动写入口。
- 不触发 n8n、企业微信、正式库、交易、税务办理、视频渲染或发布。

