# OpenClaw股票消息桥接禁用态契约

生成时间：2026-04-30 10:02:05

## 一、结论

- 当前结论：OpenClaw桥接契约已固化为禁用态；后续真实接入必须先经过人工确认、未激活导入和小流量灰度。
- OpenClaw只做南北向消息代理，不写业务判断。
- n8n是唯一逻辑编排中心。
- 当前只生成禁用态契约，不调用真实OpenClaw、不启用Webhook、不发送企业微信。

## 二、角色定位

- OpenClaw：南北向消息代理，只负责接收企业微信消息、转发n8n、接收n8n回复、返回企业微信。
- n8n：唯一逻辑编排中心，负责业务路由、调用股票助手、调用统一消息出口。
- 股票助手：只提供股票识别、研究报告、短回复和禁用态响应包。
- 统一消息出口：后续唯一企业微信发送出口，当前只生成禁用态发送包。

## 三、禁止事项

- OpenClaw内不得写if...else业务判断。
- OpenClaw不得直接调用股票分析脚本。
- OpenClaw不得直接调用大模型。
- OpenClaw不得直接写股票正式库。
- OpenClaw不得直接写旧系统。
- 当前契约不得触发真实企业微信发送。
- 当前契约不得启用n8n Webhook。

## 四、入站字段

- source：wecom
- message_id：企业微信原始消息ID或禁用态模拟ID
- sender：用户或群成员标识
- message_type：text|voice|voice_confirm
- text：文本内容或语音转写文本
- voice_text：语音确认场景的原语音文本
- timestamp：消息时间

## 五、OpenClaw转发n8n字段

- gateway：openclaw
- business：stock
- mode：disabled_contract
- payload：入站消息字段原样承载
- safety：{'real_send': False, 'trade': False, 'write_official_db': False}

## 六、n8n返回OpenClaw字段

- reply_text：待发送回复文本
- need_clarification：是否需要追问
- confidence：理解置信度
- real_send：False
- trade：False
- trace_id：链路追踪ID

## 七、实际动作

- 调用OpenClaw：False
- 触发n8n：False
- 启用Webhook：False
- 企业微信真实发送：False
- 写正式库：False
- 写旧系统：False
- 调用券商接口：False
- 自动交易：False
- 重启服务：False
