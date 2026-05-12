# n8n母样本保留与旧副本删除摘要

- 生成时间：2026-05-06 16:03:09
- 当前结论：当前运行 n8n 仅保留 5 个 inactive 母样本；旧 workflow 完整副本和旧 SQLite 回滚库已转为摘要后删除。
- 当前数据库：D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\database.sqlite
- 当前容器：jiege_v3_n8n
- 当前端口：127.0.0.1:28679 -> 5678

## 当前保留母样本

| 名称 | id | active | 节点数 | 结构 |
|---|---|---|---|---|
| 股票主动研究闭环_桥接未激活 | h0xpxp9rPrUSqk1G | False | 4 | n8n-nodes-base.manualTrigger -> n8n-nodes-base.executeCommand -> n8n-nodes-base.set -> n8n-nodes-base.stickyNote |
| 股票主动研究闭环_文件桥接未激活 | ZkzsB6MdxlC3VMxY | False | 4 | n8n-nodes-base.manualTrigger -> n8n-nodes-base.executeCommand -> n8n-nodes-base.set -> n8n-nodes-base.stickyNote |
| 股票助手n8n本地执行回环测试 | JBVQ8osGXlHoSJfR | False | 2 | n8n-nodes-base.executeWorkflowTrigger -> n8n-nodes-base.set |
| 股票助手企业微信Webhook桥接入口未激活v2 | un0S6SrQSCIsjuhn | False | 4 | n8n-nodes-base.webhook -> n8n-nodes-base.httpRequest -> n8n-nodes-base.respondToWebhook -> n8n-nodes-base.stickyNote |
| 股票助手企业微信查询适配器未激活导入件 | urKB3BwGfDWQMKb5 | False | 4 | n8n-nodes-base.manualTrigger -> n8n-nodes-base.set -> n8n-nodes-base.code -> n8n-nodes-base.stickyNote |

## 已删除旧副本摘要

- 旧 workflow 完整 JSON 数量：29
- 旧证据文件数量：5

## 保留的复用结构

- Manual Trigger -> Execute Command -> Set -> Sticky Note
- Manual Trigger -> Execute Command(HTTP bridge) -> Set -> Sticky Note
- Execute Workflow Trigger -> Set
- Webhook -> HTTP Request -> Respond to Webhook -> Sticky Note
- Manual Trigger -> Set -> Code -> Sticky Note

## 清债规则

- 5 个当前母样本 JSON 保留在 exports_keep。
- 已删除 workflow 的完整 JSON、旧 SQLite 整库、临时导出脚本、乱码旧计划和旧详细快照不保留。
- 如未来需要新 workflow，以母样本结构重新创建，不从旧删除池复活。
