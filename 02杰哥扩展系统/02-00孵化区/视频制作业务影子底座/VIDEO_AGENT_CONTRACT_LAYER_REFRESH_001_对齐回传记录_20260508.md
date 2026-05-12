# VIDEO_AGENT_CONTRACT_LAYER_REFRESH_001 对齐回传记录

- 记录时间：2026-05-08 10:35:00 +08:00
- 施工范围：视频制作业务影子底座
- 施工模式：W1/R0 影子升级蓝图与契约层
- 总管裁定执行：不做大脑移植，不接真实大模型，不改 `video_factory_chat.py`

## 1. 本轮做了什么

按总管裁定，在 `D:\杰哥智能化系统\02杰哥扩展系统\02-00孵化区\视频制作业务影子底座\` 内完成 5 份视频创作智能体影子契约草案的规范化补强。

核验时发现原 5 个 JSON 文件存在编码显示和机器解析风险，本轮已在同名文件上重写为 UTF-8 可读、可由 Python 和 PowerShell `-Encoding UTF8` 解析的规范 JSON，并同步补强 Markdown 正文。

## 2. 改了哪些文件

- `VIDEO_AGENT_CONVERSATION_STATE_CONTRACT_001_会话状态契约草案_v1.0.md`
- `VIDEO_AGENT_CONVERSATION_STATE_CONTRACT_001_会话状态契约草案_v1.0.json`
- `VIDEO_AGENT_INTENT_ROUTING_001_意图路由分类表草案_v1.0.md`
- `VIDEO_AGENT_INTENT_ROUTING_001_意图路由分类表草案_v1.0.json`
- `VIDEO_AGENT_PARTIAL_REVISION_CONTRACT_001_局部修正契约草案_v1.0.md`
- `VIDEO_AGENT_PARTIAL_REVISION_CONTRACT_001_局部修正契约草案_v1.0.json`
- `VIDEO_AGENT_ENGINE_ADAPTER_CONTRACT_001_外部引擎适配契约草案_v1.0.md`
- `VIDEO_AGENT_ENGINE_ADAPTER_CONTRACT_001_外部引擎适配契约草案_v1.0.json`
- `VIDEO_AGENT_HUMAN_GATE_UPGRADE_001_人工门禁升级清单_v1.0.md`
- `VIDEO_AGENT_HUMAN_GATE_UPGRADE_001_人工门禁升级清单_v1.0.json`

新增本回传记录：

- `VIDEO_AGENT_CONTRACT_LAYER_REFRESH_001_对齐回传记录_20260508.md`
- `VIDEO_AGENT_CONTRACT_LAYER_REFRESH_001_对齐回传记录_20260508.json`

## 3. 核心字段

- 会话状态契约：会话ID、会话来源、用户原始想法、当前任务ID、已确认内容、可修改内容、等待用户确认项、合规阻断项、生成放行状态、真实渲染放行状态、发布放行状态。
- 意图路由分类表：新建任务、改文案、改分镜、改风格、改受众、改配音、改封面、生成预检、发布预检、人工复核、复盘进化、无法判断。
- 局部修正契约：任务ID、修改对象、修改范围、锁定内容、变更理由、修正前、修正后、影响范围、需人工确认项。
- 外部引擎适配契约：MoneyPrinterTurbo、HappyHorse、Qwen-TTS、PostBot 的输入字段、输出字段、调用前门禁、调用后回执和失败回滚字段。
- 人工门禁升级清单：创意确认、文案确认、分镜确认、素材授权、AI标识、生成放行、真实渲染放行、成品预览、发布放行。

## 4. 风险等级

低风险。

本轮只改影子草案和契约层文档，不涉及正式执行。

## 5. 是否触发真实系统

否。

本轮未执行：

- 真实大模型调用；
- MoneyPrinterTurbo / HappyHorse / Qwen-TTS / PostBot 调用；
- 真实素材读取；
- 渲染、上传、发布；
- n8n；
- 企业微信真实外发；
- 19310 / 19302 修改或重启。

## 6. 是否需要总管整合

当前不需要总管立即整合。

未来若要把这些契约接入真实模型、企业微信真实路由、n8n、真实渲染或发布，必须交回总管裁定。

## 7. 下一步 W1/R0 建议

1. 基于这 5 份契约生成“影子试运行输入输出包”，只跑脱敏想法到路由和待复核字段，不调用模型。
2. 生成“人工复核回执承接模板”，用于记录用户确认、驳回、局部修改意见。
3. 生成“契约层 R0 自检清单”，检查 JSON 可解析、边界字段为 false、生成/渲染/发布放行拆分。

## 自验收

- [x] 5 个 JSON 已用 Python `json.loads` 验证通过。
- [x] 5 个 JSON 已用 PowerShell `Get-Content -Encoding UTF8 | ConvertFrom-Json` 验证通过。
- [x] 5 个 Markdown 文件均存在。
- [x] 未修改正式视频脚本。
- [x] 未触发真实系统。
- [x] 生成、真实渲染、发布放行已拆分。
