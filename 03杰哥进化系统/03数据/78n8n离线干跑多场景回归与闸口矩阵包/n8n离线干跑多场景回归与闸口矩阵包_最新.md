# n8n 离线干跑多场景回归与闸口矩阵包

- 生成时间：2026-05-08 18:03:26
- 状态：offline_multiscenario_gate_matrix_ready
- 模式：offline/dry_run
- 真实触发：false
- webhook_enabled：false
- 网络请求：false
- n8n 连接：false
- 企业微信真实发送：false

## 场景

### S01 税收消息转候选

- 最终状态：blocked_waiting_supervisor
- 阻断闸口：G04、G05、G08
- dry_run 节点数：4

### S02 股票展示巡检

- 最终状态：inspection_ready_blocked_before_trade
- 阻断闸口：G03、G06、G08
- dry_run 节点数：3

### S03 视频渲染阻断

- 最终状态：blocked_video_real_render
- 阻断闸口：G03、G07、G08
- dry_run 节点数：3

### S04 总管确认闸口

- 最终状态：blocked_waiting_supervisor
- 阻断闸口：G08、G10
- dry_run 节点数：3

### S05 异常失败分级

- 最终状态：blocked_failure_level_l4
- 阻断闸口：G01、G02、G03、G08、G09
- dry_run 节点数：3

## 验收要求

- 场景数不少于 5。
- 所有场景必须 offline/dry_run。
- real_trigger=false。
- webhook_enabled=false。
- 不写入真实接入敏感字段。
- error_count=0。
