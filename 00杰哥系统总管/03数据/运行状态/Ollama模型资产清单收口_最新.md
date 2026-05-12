# Ollama 模型资产清单收口

时间：2026-05-06 07:25:00 +08:00

## 一、完成事项

已只读生成 Ollama 模型清单与 D/F blob 差距清单。

产物：

- `D:\杰哥智能化系统\01杰哥智能系统\03数据\ollama\资产台账\Ollama模型清单_最新.txt`
- `D:\杰哥智能化系统\01杰哥智能系统\03数据\ollama\资产台账\Ollama模型与blob差距清单_最新.md/json`

## 二、当前模型

容器 `jiege_v3_ollama` 当前列出 14 个模型：

- `sam860/qwen3-reranker:0.6b-Q8_0`
- `qwen3-embedding:4b`
- `bge-m3:latest`
- `gemma3:27b`
- `qwen3-coder:30b`
- `deepseek-r1:32b`
- `qwen3:14b`
- `qwen3:30b`
- `tinyllama:latest`
- `mychen76/Fin-R1:Q5`
- `martain7r/finance-llama-8b:q4_k_m`
- `glm4:latest`
- `deepseek-r1:7b`
- `qwen2.5:7b`

## 三、D/F 差距

- D 盘 Ollama 总文件：117
- D 盘 Ollama 总大小：133.994 GB
- 去重 blob 数：54
- 去重 blob 总大小：105.944 GB
- F 盘已匹配 blob：29
- F 盘缺失 blob：25
- F 盘缺失大小：81.892 GB

## 四、判定

当前不复制或删除模型。Ollama 属于“可再生但恢复成本高”资产：

- 如果允许联网重拉：当前模型清单足够作为恢复入口。
- 如果要求离线恢复：应按缺失 blob 清单补 F 盘副本。

## 五、安全边界

本轮只读执行 `ollama list` 和文件元数据比对；未删除、移动、复制大模型，未重启 Ollama，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易。
