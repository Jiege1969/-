# n8n 离线编排本地干跑执行器包

- 生成时间：2026-05-08 17:52:29
- 包状态：offline_local_dryrun_executor_ready
- 执行模式：offline/dry_run
- 真实触发：false
- webhook_enabled：false
- 网络请求：false
- n8n 连接：false
- 企业微信真实发送：false

## 本地干跑节点

### N01 收到离线消息样本

- mode：offline/dry_run
- real_trigger：false
- webhook_enabled：false
- 模拟输入：离线消息文本副本；本地只读蓝图摘要
- 模拟输出：标准化消息对象候选

### N02 离线分类与红线识别

- mode：offline/dry_run
- real_trigger：false
- webhook_enabled：false
- 模拟输入：标准化消息对象候选
- 模拟输出：离线分类结果候选；红线命中说明候选

### N03 只读脚本核对模拟

- mode：offline/dry_run
- real_trigger：false
- webhook_enabled：false
- 模拟输入：离线分类结果候选；本地只读资料路径摘要
- 模拟输出：只读核对摘要候选；异常阻断说明候选

### N04 候选回传草稿生成

- mode：offline/dry_run
- real_trigger：false
- webhook_enabled：false
- 模拟输入：只读核对摘要候选
- 模拟输出：候选回传草稿；禁止自动发送说明

### N05 总管确认闸口

- mode：offline/dry_run
- real_trigger：false
- webhook_enabled：false
- 模拟输入：候选回传草稿；红线命中说明候选
- 模拟输出：待总管确认记录；人工处理建议

## 红线

- 不接 n8n
- 不触发 webhook
- 不请求网络
- 不改配置
- 不重载服务
- 不真实发送企业微信
