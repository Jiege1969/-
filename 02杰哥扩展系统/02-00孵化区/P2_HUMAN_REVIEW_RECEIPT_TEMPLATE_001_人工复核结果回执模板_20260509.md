# P2-S11 人工复核结果回执模板

> 状态：回执模板，不是放行单，不是自动写入器。
> 日期：2026-05-09
> 边界：不读取真实材料，不写影子入口，不触发外部动作。

## 目的

P2-S10 已把封存项转成人工复核工作包。P2-S11 规定人工复核结果如何回执，防止“人工复核通过”被系统误解成“自动填写入口”或“正式业务放行”。

## 回执字段

| 字段 | 含义 | 要求 |
|:---|:---|:---|
| review_receipt_id | 复核回执编号 | 必填 |
| source_receipt_id | 来源分流回执编号 | 必填 |
| material_id | 材料编号 | 必填 |
| target_line | 目标业务线 | 必填 |
| target_entry | 目标入口 | 必填 |
| seal_bucket | 封存类型 | 必填 |
| human_review_result | 人工复核结果 | 必填 |
| reviewed_by_human | 是否已人工复核 | 必须为 true 才能进入候选 |
| entry_fill_candidate | 是否成为影子入口填写候选 | 可为 true，但不等于自动填写 |
| auto_fill_shadow_entry | 是否自动填写影子入口 | 必须为 false |
| write_target_entry | 是否写目标入口 | 必须为 false |
| release_form | 是否放行单 | 必须为 false |
| formal_capability_claim | 是否声明正式能力 | 必须为 false |
| next_gate | 下一闸口 | 必填 |

## 允许结果

### 待复核影子封存

- `review_pass_fill_candidate`：可成为影子入口填写候选，但仍需下一闸口检查。
- `needs_more_info`：继续补材料或补字段。
- `review_reject`：退回问题回收。

### 缺口封存

- `continue_pause`：继续暂停。
- `gap_resolved_return_to_intake_gate`：缺口解决后回到分流门，不直接进入入口。

### 红线阻断封存

- `maintain_block`：保持阻断。
- `escalate_to_supervisor`：升级给总管或人工确认。

## 禁止解释

- 人工复核通过不等于正式业务结论。
- 人工复核通过不等于自动填写影子入口。
- 人工复核通过不等于 n8n、企业微信、正式库、交易、税务办理、视频渲染或发布放行。

