# VIDEO_AGENT_REVIEW_QUEUE_STATE_TRANSITION_SAMPLE_001 复核队列状态迁移样例 v1.0

- 资产类型：状态迁移样例
- 施工等级：W1/R0
- 适用范围：视频制作影子复核队列
- 状态：草案样例

## 目的

规定缺口进入复核队列后的影子状态迁移，避免“已进入队列”被误认为“已复核通过”。

## 状态迁移

| 当前状态 | 触发条件 | 下一状态 | 输出物 | 是否真实执行 |
|---|---|---|---|---|
| pending_intake | 缺口卡生成 | queued | 队列承接记录 | 否 |
| queued | 人工认领 | in_review | 复核进行中记录 | 否 |
| in_review | 人工提出补充问题 | waiting_human_input | 待补充问题清单 | 否 |
| waiting_human_input | 补充材料到位 | in_review | 补充说明记录 | 否 |
| in_review | 复核通过 | review_passed_shadow | 复核通过回执草案 | 否 |
| in_review | 复核驳回 | rejected_shadow | 驳回原因回执草案 | 否 |
| review_passed_shadow | 三段门禁仍不齐 | gate_pending | 放行缺口卡 | 否 |
| gate_pending | 总管红线出现 | blocked_by_redline | 红线阻断登记 | 否 |
| review_passed_shadow | 影子任务满足关闭条件 | shadow_closed | 关闭回执 | 否 |

## 固定规则

1. `review_passed_shadow` 只是影子复核通过，不等于真实生成、真实渲染或真实发布放行。
2. 任意状态出现红线，立即进入 `blocked_by_redline`。
3. `shadow_closed` 只代表影子任务关闭，不代表正式系统结论。
4. 队列状态不直接触发工具调用。

## 边界

本样例不连接任务系统、不创建真实工单、不分派真实人员。
