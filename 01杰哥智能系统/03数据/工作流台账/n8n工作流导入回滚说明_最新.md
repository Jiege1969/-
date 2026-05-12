# n8n 工作流导入回滚说明

时间：2026-05-06 08:10:00 +08:00

依据：
- `n8n工作流母样本台账_最新.json/md`：当前保留 5 个母样本，均 inactive，SQLite integrity_check=ok。
- `n8n逐工作流归属风险回滚台账_最新.json/md`：提纯前 34 个工作流均 inactive，误启用时优先恢复 inactive 并回滚 SQLite 快照。
- 本说明只写文档，不触发 n8n，不调用 webhook，不发送企业微信。

## 导入前门禁

- 导入对象必须先进入草案清单或注册表，补齐业务归属、风险等级、负责人、回滚来源和启用条件。
- 导入件默认 `active=false`，不得携带 execution 数据、真实 Webhook URL、企业微信凭证、token、cookie、密钥或真实生产命令。
- Webhook、HTTP Request、企业微信、Execute Command、Code 节点属于重点复核项，必须人工检查参数。
- 不允许在导入检查阶段调用 n8n 运行接口、触发 webhook 或发送企业微信测试消息。

## 全量回滚：database.before.sqlite

适用边界：
- 适用于提纯、导入、批量删除、批量修改后发现 SQLite 层面整体不可接受的情况。
- 适用于需要把 n8n 数据库恢复到操作前完整状态的情况，包括 workflow_entity、shared_workflow、workflow_history、workflow_statistics、execution_entity、execution_data 等表。
- 适用于无法逐项确认变更影响，或误启用、误删、误改范围不清的情况。

使用边界：
- 这是全量数据库快照回滚，会覆盖快照之后的全部 n8n 数据库变化。
- 回滚前必须确认 n8n 已停止或数据库未被进程写入，避免热替换造成损坏。
- 回滚前应保留当前故障现场副本，便于后续比对和审计。
- 回滚后必须做 SQLite integrity_check，并确认工作流 active 状态符合台账要求。
- 不应用于只想找回单个导出 JSON 的场景；单个工作流找回优先看 `exports_delete`。

建议步骤：
1. 停止会写入 n8n SQLite 的进程或服务。
2. 复制当前 `database.sqlite` 为故障现场备份。
3. 用 `database.before.sqlite` 覆盖当前 `database.sqlite`。
4. 执行 SQLite integrity_check。
5. 按母样本台账核对工作流数量、active=0、inactive 数量和关键表计数。
6. 仍保持不触发 n8n、不调用 webhook、不发企业微信，待人工确认后再进入启用流程。

## 选择性恢复：exports_delete

适用边界：
- 适用于 34 个提纯前导出件中，某个被删除或归档的工作流需要作为草案、参考件或新母样本候选找回。
- 适用于只恢复 JSON 导出文件层面的结构，不希望覆盖整个 SQLite 数据库的情况。
- 适用于人工确认某个 deleted/exported 工作流仍有复用价值，但必须重新登记归属、风险和回滚方式的情况。

使用边界：
- `exports_delete` 不是数据库全量回滚；它只能提供已删除/归档工作流的导出 JSON 参考。
- 从 `exports_delete` 恢复出的工作流不得直接启用，必须作为新导入件或草案处理，并保持 `active=false`。
- 恢复前必须去除或替换真实 Webhook、企业微信、HTTP、命令、代码、凭证和业务参数。
- 同名工作流不得直接覆盖现有 5 个母样本；需要新名称、新 id 或明确版本标识。
- 如果恢复件与现有母样本重复，应优先复用现有母样本结构，不再扩大 SQLite 工作流数量。

建议步骤：
1. 在 `exports_delete` 中按 id/name 找到目标 JSON。
2. 复制到草案区或待审目录，不直接导入生产 n8n。
3. 人工清理敏感参数和股票业务语义。
4. 补齐注册表、草案清单、业务归属、风险等级、回滚来源。
5. 如确需导入，先导入为 inactive，并记录来源为 `exports_delete`。
6. 导入后只做静态核对，不触发 webhook、不运行 Execute Command、不发送企业微信。

## 选择建议

| 场景 | 优先方式 | 原因 |
|---|---|---|
| 批量提纯后整体状态错误 | `database.before.sqlite` | 需要恢复完整数据库一致性。 |
| 误删范围不清 | `database.before.sqlite` | 选择性恢复无法保证表间一致性。 |
| 只想找回某个旧工作流结构 | `exports_delete` | 避免覆盖当前 5 个母样本状态。 |
| 只想参考某个旧节点结构 | `exports_delete` | 作为草案参考即可，不需要数据库回滚。 |
| 误启用 Webhook/企业微信类工作流 | 先停用，再评估 `database.before.sqlite` | 高风险链路优先阻断触发，再恢复可信快照。 |

## 禁止事项

- 禁止为验证导入结果而触发 n8n、调用 webhook 或发送企业微信。
- 禁止把 `exports_delete` 中的股票业务语义、投研判断、企业微信参数、Webhook 参数直接恢复到生产。
- 禁止在 n8n 运行写库时替换 SQLite 数据库。
- 禁止绕过门禁直接启用从 `exports_delete` 找回的工作流。
- 禁止用选择性 JSON 恢复代替需要数据库一致性的全量回滚。
