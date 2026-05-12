# P2-S15 人工填写后复验回执模板

> 状态：复验回执模板，不是填写结果，不是放行单。
> 日期：2026-05-09
> 边界：不读取真实材料，不写影子入口，不触发外部动作。

## 目的

P2-S14 已生成 4 份人工填写任务包。P2-S15 规定人工填写完成后，必须如何回执和复验，避免“已人工填写”被系统误解成业务通过或正式放行。

## 必填字段

| 字段 | 含义 | 要求 |
|:---|:---|:---|
| recheck_receipt_id | 复验回执编号 | 必填 |
| source_manual_fill_task_id | 来源人工填写任务包编号 | 必填 |
| target_line | 目标业务线 | 必填 |
| target_entry | 目标入口 | 必填 |
| target_path | 目标入口路径 | 必填 |
| human_filled | 是否已人工填写 | 必填 |
| json_parse_check | JSON 解析检查 | 必填 |
| redline_false_check | 红线字段保持 false 检查 | 必填 |
| target_entry_status_check | 入口状态检查 | 必填 |
| readonly_shadow_regression | 只读影子回归 | 必填 |
| ready_for_shadow_draft_candidate | 是否可进入影子草案候选 | 可为 true，但不等于正式能力 |
| write_target_entry | 是否写目标入口 | 必须为 false |
| auto_generate_business_conclusion | 是否自动生成业务结论 | 必须为 false |
| release_form | 是否放行单 | 必须为 false |
| formal_capability_claim | 是否声明正式能力 | 必须为 false |

## 通过口径

即使 4 项复验全部通过，也只表示“可进入下一步影子草案候选讨论”。不代表：

- 自动生成税收意见。
- 自动形成办公材料。
- 自动生成、渲染或发布视频。
- 自动调用共享政策证据形成业务结论。
- 触发 n8n、企业微信、正式库或其他真实动作。

