# VIDEO_AGENT_SHADOW_STATE_ENUM_001 影子任务状态枚举对照表

> 版本：v1.0  
> 生成时间：2026-05-08 11:22:00 +08:00  
> 资产身份：视频制作线 W1/R0 影子任务状态枚举  
> 风险等级：低风险  
> 边界声明：只定义影子状态枚举，不修改正式任务状态机。

## 状态枚举

| 状态 | 含义 | 可进入下一步 |
|---|---|---|
| shadow_intake | 已接收影子输入 | 意图路由 |
| shadow_routed | 已完成影子路由 | 任务草案或澄清 |
| shadow_draft_ready | 草案已生成 | 人工复核 |
| shadow_review_pending | 等待人工复核 | 回执承接 |
| shadow_revision_needed | 需要局部修正 | 局部修正草案 |
| shadow_blocked | 命中阻断 | 红线登记或缺口卡 |
| shadow_generation_gate_pending | 生成放行待确认 | 生成放行门禁 |
| shadow_render_gate_pending | 真实渲染放行待确认 | 真实渲染缺口卡 |
| shadow_preview_pending | 成品预览待确认 | 成品预览回执 |
| shadow_publish_gate_pending | 发布放行待确认 | 发布前门禁缺口卡 |
| shadow_closed | 影子任务本地闭环 | 回传记录 |

## 约束

1. 任何状态都不能直接触发真实渲染或发布。
2. `shadow_closed` 不代表正式上线或真实完成。
3. 命中红线时必须进入 `shadow_blocked`。
4. 放行待确认状态必须拆分生成、真实渲染、发布。

## 自检

- [x] 只定义影子状态。
- [x] 不改正式状态机。
- [x] 不触发真实系统。
