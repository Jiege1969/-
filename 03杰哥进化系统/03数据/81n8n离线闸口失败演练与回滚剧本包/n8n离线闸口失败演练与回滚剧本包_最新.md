# n8n 离线闸口失败演练与回滚剧本包

- 生成时间：2026-05-08 18:17:28
- 状态：offline_failure_drill_rollback_ready
- 场景数：5
- 回滚剧本数：5
- 模式：offline/dry_run
- real_trigger：false
- webhook_enabled：false

| 场景 | 检测结果 | 阻断闸口 | 恢复后状态 |
| --- | --- | --- | --- |
| FD01 webhook误开 | blocked | G01 n8n连接阻断、G02 webhook启用阻断、G08 总管确认闸口 | recovered_to_blocked_offline_state |
| FD02 真实触发标志误开 | blocked | G01 n8n连接阻断、G03 网络请求阻断、G08 总管确认闸口 | recovered_to_blocked_offline_state |
| FD03 凭据字段出现 | blocked | G03 网络请求阻断、G09 配置与服务重载阻断、G10 正式规则变更阻断 | recovered_to_blocked_offline_state |
| FD04 总管确认缺失 | blocked | G08 总管确认闸口、G10 正式规则变更阻断 | recovered_to_blocked_offline_state |
| FD05 下游真实动作误放行 | blocked | G03 网络请求阻断、G04 企业微信真实发送阻断、G08 总管确认闸口 | recovered_to_blocked_offline_state |
