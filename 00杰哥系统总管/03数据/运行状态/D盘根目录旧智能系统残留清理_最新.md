# D盘根目录旧智能系统残留清理

- 生成时间：2026-05-09 05:20:18
- 结论：通过
- 清理目标：D:\01杰哥智能系统
- 删除前存在：True
- 删除后存在：False

## 根因

- D:\01杰哥智能系统 为旧命名历史路径；本次残留内容为 ollama、n8n、redis、qdrant 等底座数据目录。
- 旧 Docker 容器或 Docker/WSL 重启窗口可能按历史 bind mount 或底座初始化动作自动补宿主目录。
- 当前运行中的 jiege_v3_ollama、jiege_v3_redis、jiege_v3_n8n 均挂载 D:\杰哥智能化系统\01杰哥智能系统\03数据，不依赖 D:\01杰哥智能系统。

## 已处理


## 安全边界

- 删除正式01系统：False
- 停止运行中容器：False
- 删除镜像：False
- 删除Docker卷：False
- 重启19300：False
- 重启19302：False
- 触发n8n：False
- 发送企业微信：False
- 写正式库：False
- 调用券商接口：False
- 自动交易：False
