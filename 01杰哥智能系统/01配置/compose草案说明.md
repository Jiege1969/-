# Compose 草案说明

创建日期：2026-04-26

## 一、状态

`docker-compose.v3草案.yml` 只是目标形态草案。

当前不得直接执行：

```powershell
docker compose -f docker-compose.v3草案.yml up -d
```

## 二、端口策略

草案使用 `2xxxx` 端口段，避免抢占当前运行系统：

| 服务 | 草案端口 |
|---|---:|
| agent_gateway | 28080 |
| agent_core | 28100 |
| postgres | 25432 |
| redis | 26379 |
| n8n | 28679 |
| ollama | 29134 |

## 三、正式使用前必须完成

1. 确认是否需要独立部署新 Ollama，或复用现有 `jiege_ollama`。
2. 确认模型数据目录迁移策略。
3. 确认 PostgreSQL 初始化策略。
4. 确认 n8n 工作流导入策略。
5. 确认企业微信密钥和消息出口策略。
6. 生成正式实施版 Compose。
7. 准备回滚方案。

## 四、当前建议

第一阶段不建议直接新起完整 v3 Compose。

更稳的路线是：

1. 先迁移代码副本。
2. 在非生产端口启动单个测试服务。
3. 验证通过后再逐步接入数据库、缓存和模型。

