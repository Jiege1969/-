# WSL 旧 Ollama 路径修正收口

时间：2026-05-06 07:10:00 +08:00

## 一、处理结论

已修正 `Ubuntu-24.04` 中 `/home/jiege/.bashrc` 的旧 Ollama 路径和旧容器别名。

修正前问题：

- `OLLAMA_MODELS` 指向旧 `/mnt/d/01杰哥智能系统/...`。
- `OLLAMA_HOST` 指向旧 `localhost:11435`。
- `alias ollama='docker exec ollama ollama'` 指向不存在或非主线容器名。
- Docker 安全包装函数引用不存在的 `cmd_validator.sh`。

修正后：

- `OLLAMA_MODELS=/mnt/d/杰哥智能化系统/01杰哥智能系统/03数据/ollama/models`
- `OLLAMA_HOST=127.0.0.1:29134`
- `alias ollama='docker exec jiege_v3_ollama ollama'`
- Docker 包装函数保留最小危险命令拦截，不再依赖不存在的 `cmd_validator.sh`。

## 二、证据

第一次修正证据目录：

`第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。`

LF 修复证据目录：

`第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。`

说明：第一次通过 Windows 写回后发现 `.bashrc` 行尾变为 CRLF，已立刻修回 LF，避免治理动作制造新债。

## 三、验收

- `.bashrc` 中 CRLF 命中数：0。
- `bash -n /home/jiege/.bashrc`：通过。
- 交互 shell 中环境变量可读：
  - `OLLAMA_HOST=127.0.0.1:29134`
  - `OLLAMA_API_KEY=ollama-local`
  - `OLLAMA_MODELS` 指向正式模型目录。
- `test -d "$OLLAMA_MODELS"`：通过。
- `ollama --version`：返回 `ollama version is 0.20.5`。
- 未触发 n8n，未发送企业微信，未调用券商接口，未自动交易，未删除正式数据。

## 四、规则补充

- WSL 交互环境里的旧路径也属于暗角资产，不应长期只登记不修。
- 修改 WSL shell 配置时必须验收行尾、语法、目标路径存在性和关键 alias 可用性。
- 若治理动作引入新问题，应立刻修复并在同一轮收口，不留给下一轮。

## 第30轮原始证据清债说明

- 第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。

