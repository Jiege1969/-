# VIDEO_AGENT_SHADOW_TRIAL_OPERATION_CARD_001_影子试运行操作卡_v1.0

> 资产身份：视频创作智能体影子试运行操作卡
> 阶段：W1/R0
> 状态：操作步骤卡，不是运行脚本
> 边界：只指导手工填写影子材料，不接企业微信、不调用模型、不生成媒体。

## 操作顺序

| 步骤 | 操作 | 使用文件 | 输出 |
|:---|:---|:---|:---|
| 1 | 登记脱敏输入 | `VIDEO_AGENT_DESENSITIZED_TRIAL_SAMPLE_TEMPLATE_001` | 脱敏视频想法样例 |
| 2 | 填写试运行包 | `VIDEO_AGENT_SHADOW_TRIAL_IO_PACKET_001` | 试运行输入输出包 |
| 3 | 执行字段检查 | `VIDEO_AGENT_SHADOW_RUN_CHECKLIST_001` | 通过、澄清或阻断 |
| 4 | 补澄清问题 | `VIDEO_AGENT_CLARIFICATION_TEMPLATE_001` | 一个澄清问题 |
| 5 | 更新会话状态 | `VIDEO_AGENT_CLARIFICATION_STATE_MAPPING_001` | 影子状态变更 |
| 6 | 生成文本候选结构 | `VIDEO_AGENT_THREE_OPTION_SAMPLE_001` | 最多三套待复核文本草案 |
| 7 | 承接人工意见 | `VIDEO_AGENT_HUMAN_RECEIPT_INTAKE_TEMPLATE_001` | 人工回执 |
| 8 | 记录状态变化 | `VIDEO_AGENT_STATE_CHANGE_LOG_TEMPLATE_001` | 状态变更日志 |
| 9 | 判断经验候选 | `VIDEO_AGENT_EVOLUTION_CANDIDATE_INTAKE_CHECKLIST_001` | 进化候选或保持待复核 |
| 10 | 命中红线时替代处理 | `VIDEO_AGENT_REDLINE_ALTERNATIVE_ACTION_TEMPLATE_001` | 替代影子动作 |

## 操作前检查

1. 用户想法必须脱敏。
2. 不读取任何真实素材路径。
3. 不填写账号、密钥、webhook 或企业微信凭据。
4. 不把候选草案当成正式脚本。

## 操作后收口

1. 记录使用过的影子文件。
2. 记录未确认字段和人工复核问题。
3. 生成对齐回传。
4. 不进入生成、渲染、发布或外发。
