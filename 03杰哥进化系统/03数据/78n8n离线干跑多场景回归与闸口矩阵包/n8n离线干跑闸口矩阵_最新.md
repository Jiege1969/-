# n8n 离线干跑闸口矩阵

- 生成时间：2026-05-08 18:03:26
- 场景数：5
- 闸口数：10
- 模式：offline/dry_run
- 真实触发：false
- webhook_enabled：false

| 场景 | 命中闸口 | 结果 | 最终状态 |
| --- | --- | --- | --- |
| S01 税收消息转候选 | G04 企业微信真实发送阻断 | blocked | blocked_waiting_supervisor |
| S01 税收消息转候选 | G05 税务真实账号阻断 | blocked | blocked_waiting_supervisor |
| S01 税收消息转候选 | G08 总管确认闸口 | blocked | blocked_waiting_supervisor |
| S02 股票展示巡检 | G03 网络请求阻断 | blocked | inspection_ready_blocked_before_trade |
| S02 股票展示巡检 | G06 股票交易链路阻断 | blocked | inspection_ready_blocked_before_trade |
| S02 股票展示巡检 | G08 总管确认闸口 | blocked | inspection_ready_blocked_before_trade |
| S03 视频渲染阻断 | G03 网络请求阻断 | blocked | blocked_video_real_render |
| S03 视频渲染阻断 | G07 视频真实渲染发布阻断 | blocked | blocked_video_real_render |
| S03 视频渲染阻断 | G08 总管确认闸口 | blocked | blocked_video_real_render |
| S04 总管确认闸口 | G08 总管确认闸口 | blocked | blocked_waiting_supervisor |
| S04 总管确认闸口 | G10 正式规则变更阻断 | blocked | blocked_waiting_supervisor |
| S05 异常失败分级 | G01 n8n连接阻断 | blocked | blocked_failure_level_l4 |
| S05 异常失败分级 | G02 webhook启用阻断 | blocked | blocked_failure_level_l4 |
| S05 异常失败分级 | G03 网络请求阻断 | blocked | blocked_failure_level_l4 |
| S05 异常失败分级 | G08 总管确认闸口 | blocked | blocked_failure_level_l4 |
| S05 异常失败分级 | G09 配置与服务重载阻断 | blocked | blocked_failure_level_l4 |
