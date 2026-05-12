# n8n 离线编排蓝图

- 生成时间：2026-05-08 17:39:42
- 范围：低风险实际能力前置；仅离线蓝图；不接 n8n。
- 全局模式：dry_run/offline
- 真实触发：false
- webhook：false

## 离线流程

收到消息 -> 分类 -> 只读脚本 -> 生成候选回传 -> 总管确认闸口

## 节点

### N01 收到消息

- 目的：登记来自企业微信或人工转录的消息样本，但只使用离线文本副本。
- mode：dry_run/offline
- real_trigger：false
- webhook_enabled：false
- 只读输入：离线消息样本；人工复制的只读文本
- 候选输出：标准化消息对象候选

### N02 分类

- 目的：按业务线、风险等级、是否触碰红线进行离线分类。
- mode：dry_run/offline
- real_trigger：false
- webhook_enabled：false
- 只读输入：标准化消息对象候选
- 候选输出：分类结果候选；红线命中说明候选

### N03 只读脚本

- 目的：仅指向本地只读核对脚本的执行设计，不实际调度、不连接外部服务。
- mode：dry_run/offline
- real_trigger：false
- webhook_enabled：false
- 只读输入：分类结果候选；本地只读资料路径
- 候选输出：只读核对摘要候选；异常阻断说明候选

### N04 生成候选回传

- 目的：生成可供人工审阅的回传草稿，保持候选态。
- mode：dry_run/offline
- real_trigger：false
- webhook_enabled：false
- 只读输入：只读核对摘要候选
- 候选输出：候选回传文本；禁止自动发送说明

### N05 总管确认闸口

- 目的：所有候选回传必须停在总管确认闸口，不自动放行。
- mode：dry_run/offline
- real_trigger：false
- webhook_enabled：false
- 只读输入：候选回传文本；红线命中说明候选
- 候选输出：待总管确认记录；人工处理建议
