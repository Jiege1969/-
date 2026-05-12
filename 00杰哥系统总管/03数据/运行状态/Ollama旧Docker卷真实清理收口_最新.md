# Ollama旧Docker卷真实清理收口

生成时间：2026-05-06 08:27:53 +08:00

## 结论

已删除 Docker named volume：ollama、ollama_data。

## 判定

- jiege_v3_ollama 当前使用 D 盘 bind mount：D:\杰哥智能化系统\01杰哥智能系统\03数据\ollama -> /root/.ollama。
- 所有容器均未挂载 ollama 或 ollama_data named volume。
- ollama 卷：35 个文件，约 25.825 GB；29 个 blob 与 6 个 manifest 均与 D 盘模型库重复，无唯一资产。
- ollama_data 卷：63 个文件，约 45.633 GB；含 3 个非当前模型 manifest、partial 残块和旧自动生成密钥；不属于当前模型清单，也不是不可再生数据。
- 模型权重来自公共 registry，属于可再生资产；旧自动生成密钥不应继续遗留在无依赖旧卷中。

## 处置

- 删除 ollama：完成。
- 删除 ollama_data：完成。
- 未使用 docker prune。

## 安全边界

未停止服务，未触发 Ollama 服务，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易，未删除 D 盘模型库或 F 盘备份。

## 证据目录

原始唯一性核实证据目录已于第30轮清债删除；卷删除判断、重复性结论、最终Docker/n8n/Ollama/Redis验收已固化在本_latest收口报告。

## 反退化修正

并行核实窗口在卷删除后又只读挂载 ollama_data，Docker 自动创建了同名空卷；已关闭窗口、核实空卷无引用并二次删除。最终 docker volume ls 为空。

## 最终验收

- Docker 容器：3 个主线容器运行中。
- Docker 卷：0 个。
- n8n healthz：200。
- Ollama /api/tags：200。
- Redis TCP 26379：可达。
- 血脉探针：ready=true，failed_count=0。


## 第30轮原始证据清债说明

- 原始唯一性核实证据目录已于第30轮清债删除；卷删除判断、重复性结论、最终Docker/n8n/Ollama/Redis验收已固化在本_latest收口报告。

