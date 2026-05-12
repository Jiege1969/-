# 摸清家底找差距第三十七轮n8n周边旧流水清债收口

- 生成时间：2026-05-06 18:24:17 +08:00
- n8n 数据库结论：当前实际 workflow_entity 只有 5 个工作流，全部 inactive，与母样本台账一致。
- 34 个旧工作流已在前轮提纯为 5 个 inactive 母样本；本轮不再保留旧副本尾巴。
- 本轮删除：163 个 n8n 周边旧流水/空日志/非 venv pycache，约 1.32 MB。

## 本轮收口
- 04日志/灰度接入验收：删除 134 个 timestamp/export 旧流水，保留 25 个最新验收/观测资产，timestamp=0。
- 01智能/03数据/n8n：删除 4 个 0 字节事件日志轮转和 crash.journal，保留 database.sqlite、config、当前日志和目录说明。
- 非 venv 脚本 __pycache__：删除 25 个缓存文件。

## 源头防复发
- 检查n8n受控启用状态.py 已改为只写 n8n-controlled-enable-status-最新.json 和 n8n-controlled-enable-status-export-最新.json。
- 本轮只做只读导出和状态核验，不触发 n8n，不启用 workflow，不删除母样本。

## 后续
- n8n 工作流层面保持 5 个 inactive 母样本，不再围绕 34 个旧工作流留尾巴。
- 继续扫描剩余 timestamp 输出脚本和业务日志目录。
