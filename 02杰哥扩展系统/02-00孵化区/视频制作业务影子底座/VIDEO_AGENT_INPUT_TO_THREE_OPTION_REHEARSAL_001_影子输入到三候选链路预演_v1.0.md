# VIDEO_AGENT_INPUT_TO_THREE_OPTION_REHEARSAL_001_影子输入到三候选链路预演_v1.0

> 资产身份：视频创作智能体影子链路预演
> 阶段：W1/R0
> 状态：文本链路预演，不是真实执行流
> 边界：不调用模型、不生成媒体、不读取真实素材、不发布、不接企业微信。

## 链路目标

演示一条手工影子输入如何经过检查、澄清和路由，形成最多三套待复核文本候选。该链路只描述文件关系，不执行自动生成。

## 预演链路

| 步骤 | 输入 | 使用文件 | 输出 |
|:---|:---|:---|:---|
| 1 | 手工影子输入 | `VIDEO_AGENT_SHADOW_INPUT_INTAKE_SAMPLE_001` | 脱敏输入记录 |
| 2 | 脱敏输入记录 | `VIDEO_AGENT_SHADOW_RUN_CHECKLIST_001` | 通过、澄清或阻断 |
| 3 | 待澄清字段 | `VIDEO_AGENT_CLARIFICATION_TEMPLATE_001` | 一个澄清问题 |
| 4 | 澄清回答 | `VIDEO_AGENT_CLARIFICATION_STATE_MAPPING_001` | 更新影子会话状态 |
| 5 | 会话状态 | `VIDEO_AGENT_CONVERSATION_STATE_SAMPLE_001` | 待输出状态 |
| 6 | 待输出状态 | `VIDEO_AGENT_THREE_OPTION_OUTPUT_TEMPLATE_001` | 三候选文本草案结构 |
| 7 | 三候选结构 | `VIDEO_AGENT_THREE_OPTION_SAMPLE_001` | 待人工选择和复核 |

## 出口状态

| 出口 | 条件 | 后续 |
|:---|:---|:---|
| 澄清继续 | 字段不足但未命中红线 | 只追问一个澄清问题 |
| 三候选草案 | 字段足够且无红线 | 输出文本候选，进入人工选择 |
| 阻断 | 命中生成、发布、外发、凭据、真实素材读取等红线 | 生成红线样例卡或阻断记录 |

## 禁止解释

1. 链路预演不代表真实自动化流程上线。
2. 三候选草案不代表脚本定稿。
3. 人工选择候选不代表生成、渲染或发布放行。
