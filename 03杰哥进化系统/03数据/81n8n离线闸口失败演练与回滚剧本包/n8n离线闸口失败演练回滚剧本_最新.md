# n8n 离线闸口失败演练回滚剧本

- 生成时间：2026-05-08 18:17:28
- 剧本数：5
- 执行方式：documented_local_recovery_only
- real_trigger：false
- webhook_enabled：false

## RB-FD01 webhook误开回滚剧本
- FD01-RB01：冻结本地演练证据；仅保留离线样例、检测结果和阻断原因，不写入任何外部系统
- FD01-RB02：强制恢复离线护栏；确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false
- FD01-RB03：隔离风险候选；将 webhook误开候选 标记为 blocked_candidate，只允许人工复核
- FD01-RB04：回到总管确认；恢复为待总管确认状态，禁止自动放行
- FD01-RB05：本地复验；只读取本包 JSON，复验 error_count=0 且无真实动作开关

## RB-FD02 真实触发标志误开回滚剧本
- FD02-RB01：冻结本地演练证据；仅保留离线样例、检测结果和阻断原因，不写入任何外部系统
- FD02-RB02：强制恢复离线护栏；确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false
- FD02-RB03：隔离风险候选；将 真实触发误开候选 标记为 blocked_candidate，只允许人工复核
- FD02-RB04：回到总管确认；恢复为待总管确认状态，禁止自动放行
- FD02-RB05：本地复验；只读取本包 JSON，复验 error_count=0 且无真实动作开关

## RB-FD03 凭据字段出现回滚剧本
- FD03-RB01：冻结本地演练证据；仅保留离线样例、检测结果和阻断原因，不写入任何外部系统
- FD03-RB02：强制恢复离线护栏；确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false
- FD03-RB03：隔离风险候选；将 凭据字段风险候选 标记为 blocked_candidate，只允许人工复核
- FD03-RB04：回到总管确认；恢复为待总管确认状态，禁止自动放行
- FD03-RB05：本地复验；只读取本包 JSON，复验 error_count=0 且无真实动作开关

## RB-FD04 总管确认缺失回滚剧本
- FD04-RB01：冻结本地演练证据；仅保留离线样例、检测结果和阻断原因，不写入任何外部系统
- FD04-RB02：强制恢复离线护栏；确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false
- FD04-RB03：隔离风险候选；将 缺失确认候选 标记为 blocked_candidate，只允许人工复核
- FD04-RB04：回到总管确认；恢复为待总管确认状态，禁止自动放行
- FD04-RB05：本地复验；只读取本包 JSON，复验 error_count=0 且无真实动作开关

## RB-FD05 下游真实动作误放行回滚剧本
- FD05-RB01：冻结本地演练证据；仅保留离线样例、检测结果和阻断原因，不写入任何外部系统
- FD05-RB02：强制恢复离线护栏；确认 mode=offline/dry_run、real_trigger=false、webhook_enabled=false
- FD05-RB03：隔离风险候选；将 下游真实动作候选 标记为 blocked_candidate，只允许人工复核
- FD05-RB04：回到总管确认；恢复为待总管确认状态，禁止自动放行
- FD05-RB05：本地复验；只读取本包 JSON，复验 error_count=0 且无真实动作开关
