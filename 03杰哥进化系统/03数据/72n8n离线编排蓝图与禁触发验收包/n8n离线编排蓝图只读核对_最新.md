# n8n 离线编排蓝图只读核对

- 核对时间：2026-05-08 17:39:42
- 总体状态：pass
- 错误数：0

| 核对项 | 结果 | 说明 |
| --- | --- | --- |
| 流程覆盖收到消息到总管确认闸口 | pass | 收到消息 -> 分类 -> 只读脚本 -> 生成候选回传 -> 总管确认闸口 |
| 节点数量不少于 5 | pass | 5 |
| 所有节点禁触发字段正确 | pass | 全部节点通过 |
| 所有边禁触发字段正确 | pass | 全部边通过 |
| 全局禁触发与离线模式正确 | pass | {"mode": "dry_run/offline", "real_trigger": false, "webhook_enabled": false, "network_call_enabled": false, "n8n_connection_enabled": false, "external_delivery_enabled": false, "production_rule_enabled": false} |
| 无 URL/token/凭据/真实动作字段 | pass | 未发现禁用字段和值 |
| 离线蓝图与验收包文件存在 | pass | 4 |
