# P2-S12 影子入口填写候选闸口

> 状态：只读填写前闸口，不是写入器。
> 日期：2026-05-09
> 边界：不读取真实材料，不写影子入口，不触发外部动作。

## 目的

P2-S11 已把人工复核结果分成填写候选、继续暂停和红线阻断。P2-S12 在影子入口真正填写之前增加只读闸口，确认候选是否仍具备填写资格。

该闸口只回答一个问题：候选是否可以进入“人工填写影子入口讨论”。它不写入口、不放行正式能力、不触发任何真实动作。

## 通过条件

填写候选必须同时满足：

1. `entry_fill_candidate=true`。
2. `reviewed_by_human=true`。
3. `human_review_result=review_pass_fill_candidate`。
4. `next_gate=shadow_entry_fill_candidate_gate`。
5. `auto_fill_shadow_entry=false`。
6. `write_target_entry=false`。
7. `release_form=false`。
8. `formal_capability_claim=false`。
9. 目标入口仍处于允许状态。
10. 目标业务线不是 `pause`，目标入口不是 `gap_or_redline_record`。

## 不通过条件

- 缺口封存继续留在缺口回收。
- 红线阻断继续留在问题回收或总管确认。
- 任何自动填写、写入口、放行单、正式能力声明均直接失败。

## 输出

P2-S12 只输出填写候选闸口预演报告和候选清单。候选清单只用于人工查看，不写目标入口。

