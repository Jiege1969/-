# n8n 工作流母样本提纯收口

时间：2026-05-06 07:43:00 +08:00

## 一、处理原则

按用户要求，n8n 工作流不再“全部留档观察”。保留有益的母样本，其余无母样本价值、重复、旧版本、被新版本替代的 inactive 工作流导出证据后删除。

## 二、删除前状态

- `workflow_entity=34`
- `shared_workflow=34`
- `workflow_history=34`
- `execution_entity=43`
- `execution_data=43`
- active 工作流：0

## 三、保留母样本

保留 5 个：

| id | 名称 | 母样本角色 | 风险 |
|---|---|---|---|
| `ZkzsB6MdxlC3VMxY` | 股票主动研究闭环_文件桥接未激活 | 股票主动研究文件桥接 | 中 |
| `h0xpxp9rPrUSqk1G` | 股票主动研究闭环_桥接未激活 | 股票主动研究桥接 | 中 |
| `un0S6SrQSCIsjuhn` | 股票助手企业微信Webhook桥接入口未激活v2 | 企业微信 Webhook 桥接入口 v2 | 高 |
| `JBVQ8osGXlHoSJfR` | 股票助手n8n本地执行回环测试 | 本地执行回环测试 | 低 |
| `urKB3BwGfDWQMKb5` | 股票助手企业微信查询适配器未激活导入件 | 企业微信查询适配器 | 高 |

## 四、已删除

删除 29 个：

- 旧版股票主动研究闭环 1 个。
- 旧企业微信 Webhook 灰度入口 1 个。
- 重复本地执行回环测试 27 个。

删除方式：

- 先导出完整 SQLite 和 34 个工作流 JSON。
- 停止 `jiege_v3_n8n`。
- 在 SQLite 中删除候选 workflow，开启外键级联。
- 写回数据库。
- 启动 `jiege_v3_n8n`。
- 重新验收。

## 五、删除后状态

- `workflow_entity=5`
- `shared_workflow=5`
- `workflow_history=5`
- `workflow_statistics=2`
- `execution_entity=3`
- `execution_data=3`
- active 工作流：0
- SQLite `integrity_check=ok`
- n8n 容器：running
- n8n HTTP：200
- 血脉分钟级探针：`ready=true`，`failed_count=0`

## 六、证据与回滚

证据目录：

`D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本导出_当前`

包含：

- 删除前数据库：`database.before.sqlite`
- 删除前 34 个工作流详情：`workflows.before.detail.json`
- 保留/删除计划：`keep_delete_plan.json`
- 保留母样本 JSON：`exports_keep`
- 删除项 JSON：`exports_delete`
- 删除结果：`prune_result.json`

回滚方式：

- 可用 `database.before.sqlite` 回滚整个 n8n 数据库。
- 也可从 `exports_delete` 中按需恢复单个工作流。

## 七、台账

已更新：

- `D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流资产台账_最新.md/json`
- `D:\杰哥智能化系统\01杰哥智能系统\03数据\工作流台账\n8n工作流母样本台账_最新.md/json`

## 八、安全边界

未触发 n8n 工作流，未调用 webhook，未发送企业微信，未调用券商接口，未自动交易，未删除凭据，未删除 Docker 卷/镜像/模型/数据库备份。

