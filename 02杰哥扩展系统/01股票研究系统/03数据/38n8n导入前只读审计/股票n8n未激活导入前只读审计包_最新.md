# 股票n8n未激活导入前只读审计包

生成时间：2026-05-09 13:26:44

## 一、结论

- 是否通过导入前只读审计：False
- 当前结论：工作流草案存在导入前审计风险，不能提交导入评审。

## 二、工作流草案审计

- active：False
- 节点数量：4
- 节点类型：['n8n-nodes-base.manualTrigger', 'n8n-nodes-base.executeCommand', 'n8n-nodes-base.set', 'n8n-nodes-base.stickyNote']
- 非允许节点类型：[]
- 含credentials字段：False
- 命中禁止关键词：['webhook', '交易', '券商']
- 需要人工确认导入：True
- 需要人工确认启用：True
- 必须保持未激活：True
- 安全检查：{}

## 三、预案审计

- 预案文件存在：True
- 明确active_false：True
- 明确不执行手动触发：True
- 明确不接OpenClaw：False
- 明确不接企业微信真实发送：True
- 明确回滚保持未激活：False

## 四、审计项目

- 工作流草案必须active=false。
- 工作流草案不得包含credentials字段。
- 工作流草案不得包含企业微信真实发送节点。
- 工作流草案不得包含券商、交易、下单相关节点。
- 工作流草案不得包含自动Webhook触发节点。
- 工作流草案必须保留安全边界说明节点。
- 工作流草案必须声明requires_manual_confirm_before_import=true。
- 工作流草案必须声明requires_manual_confirm_before_enable=true。
- 导入预案必须明确导入后仍保持active=false。
- 导入预案必须明确不执行手动触发、不接OpenClaw、不接企业微信真实发送。

## 五、实际动作

- 调用n8nAPI：False
- 导入n8n：False
- 启用Webhook：False
- 触发n8n：False
- 调用OpenClaw：False
- 发送企业微信：False
- 写正式库：False
- 写旧系统：False
- 调用券商接口：False
- 自动交易：False
