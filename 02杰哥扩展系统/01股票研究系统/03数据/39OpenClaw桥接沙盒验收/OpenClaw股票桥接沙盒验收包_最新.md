# OpenClaw股票桥接沙盒验收包

生成时间：2026-04-30 10:02:07

## 一、结论

- 是否通过沙盒验收：True
- 当前结论：OpenClaw股票桥接沙盒链路通过，可作为真实桥接前的本地验收材料；当前未调用真实OpenClaw、未触发n8n、未发送企业微信。

## 二、沙盒输入

```json
{
  "source": "wecom",
  "message_id": "sandbox-stock-001",
  "sender": "local-sandbox-user",
  "message_type": "text",
  "text": "分析新易盛",
  "voice_text": "",
  "timestamp": "2026-04-30 10:02:07"
}
```

## 三、n8n标准输入

```json
{
  "gateway": "openclaw",
  "business": "stock",
  "mode": "sandbox_disabled",
  "payload": {
    "source": "wecom",
    "message_id": "sandbox-stock-001",
    "sender": "local-sandbox-user",
    "message_type": "text",
    "text": "分析新易盛",
    "voice_text": "",
    "timestamp": "2026-04-30 10:02:07"
  },
  "safety": {
    "real_send": false,
    "trade": false,
    "write_official_db": false,
    "write_old_system": false
  }
}
```

## 四、脚本运行

- 统一路由返回码：0
- 统一出口返回码：0

## 五、输出文件

- 统一路由最新：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\25企业微信统一路由\企业微信股票消息统一路由禁用态_最新.json
- 统一出口最新：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\34统一消息出口禁用态\股票统一消息出口禁用态回复包_最新.json

## 六、实际动作

- 调用真实OpenClaw：False
- 调用n8nAPI：False
- 导入n8n：False
- 启用Webhook：False
- 触发n8n：False
- 发送企业微信：False
- 写正式库：False
- 写旧系统：False
- 调用券商接口：False
- 自动交易：False
- 重启服务：False
