# 摸清家底找差距第二十四轮n8n母样本复核与旧副本收口

- 生成时间：2026-05-06 16:04:47
- 当前结论：5个n8n workflow均可作为母样本保留；29个已删除旧workflow完整导出、旧SQLite回滚库、临时导出脚本和旧详细快照已删除，只保留当前母样本与删除摘要。
- 当前n8n数据库：D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\database.sqlite
- 当前容器：jiege_v3_n8n
- 当前端口：127.0.0.1:28679 -> 5678

## 保留母样本

| 名称 | id | active | 节点数 | 复用价值 |
|---|---|---|---|---|
| 股票主动研究闭环_桥接未激活 | h0xpxp9rPrUSqk1G | False | 4 | HTTP桥接骨架：手动触发、受控桥接服务、标准输出。 |
| 股票主动研究闭环_文件桥接未激活 | ZkzsB6MdxlC3VMxY | False | 4 | 文件桥接骨架：手动触发、本地命令、结构化输出、安全说明。 |
| 股票助手n8n本地执行回环测试 | JBVQ8osGXlHoSJfR | False | 2 | 最小子工作流/回环测试结构。 |
| 股票助手企业微信Webhook桥接入口未激活v2 | un0S6SrQSCIsjuhn | False | 4 | Webhook入站闭环：Webhook、HTTP Request、Respond to Webhook。 |
| 股票助手企业微信查询适配器未激活导入件 | urKB3BwGfDWQMKb5 | False | 4 | 输入契约、Code适配、安全占位输出。 |

## 删除旧副本

- 旧 workflow 完整导出：29 个，已转摘要后删除。
- 旧 SQLite 回滚库：已删除。
- 临时导出脚本、乱码旧计划、旧详细快照：已删除。

| 路径 | 仍存在 |
|---|---|
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\exports_delete | False |
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\database.before.sqlite | False |
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\export_workflows.py | False |
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\keep_delete_plan.json | False |
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\prune_result.json | False |
| D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\workflows.before.detail.json | False |

## 保留证据

- exports_keep：保留5个当前母样本JSON。
- 删除摘要：D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前\n8n母样本保留与旧副本删除摘要_最新.md

## 安全边界

- 未触发 n8n，未启用 workflow，未调用 webhook/API，未发送企业微信，未调用券商接口，未自动交易。

## 最终只读验收

- JSON 可读：通过。
- Required HTTP：4/4。
- 历史注册 HTTP：7/7。
- n8n 只读探测：TCP True，health True。
- Redis：PONG。
- 开工上下文：缺失 0。

