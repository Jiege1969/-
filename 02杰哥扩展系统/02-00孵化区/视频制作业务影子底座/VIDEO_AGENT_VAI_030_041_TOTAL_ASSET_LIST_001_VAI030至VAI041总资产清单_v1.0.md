# VIDEO_AGENT_VAI_030_041_TOTAL_ASSET_LIST_001 VAI030至VAI041总资产清单

> 版本：v1.0  
> 生成时间：2026-05-08 11:35:00 +08:00  
> 资产身份：视频制作线 VAI030 至 VAI041 影子资产清单  
> 风险等级：低风险  
> 边界声明：只列资产清单，不声明正式上线能力。

## 总资产清单

| 编号 | 文件前缀 | 作用 | 真实系统触发 |
|---|---|---|---|
| VAI030 | VIDEO_AGENT_CONTINUATION_STATE_CARD_001 | 连续施工状态卡 | 否 |
| VAI031 | VIDEO_AGENT_REDLINE_BLOCK_REGISTER_001 | 红线阻断登记簿模板 | 否 |
| VAI032 | VIDEO_AGENT_ASSET_MAP_UPDATE_RULE_001 | 影子资产地图更新规则 | 否 |
| VAI033 | VIDEO_AGENT_PUBLISH_GATE_GAP_CARD_001 | 发布前门禁缺口卡 | 否 |
| VAI034 | VIDEO_AGENT_RENDER_RELEASE_GAP_CARD_001 | 真实渲染放行缺口卡 | 否 |
| VAI035 | VIDEO_AGENT_WECOM_REPLY_DRAFT_TEMPLATE_001 | 企业微信回执草案模板 | 否 |
| VAI036 | VIDEO_AGENT_RELEASE_STATE_CONSISTENCY_CHECK_001 | 放行状态一致性检查清单 | 否 |
| VAI037 | VIDEO_AGENT_REVIEW_PRIORITY_RULE_001 | 人工复核问题优先级规则 | 否 |
| VAI038 | VIDEO_AGENT_SHADOW_TASK_CLOSE_CONDITION_001 | 影子任务关闭条件清单 | 否 |
| VAI039 | VIDEO_AGENT_SHADOW_STATE_ENUM_001 | 影子任务状态枚举对照表 | 否 |
| VAI040 | VIDEO_AGENT_COMMAND_STATE_CHANGE_REHEARSAL_001 | 命令到状态变更预演表 | 否 |
| VAI041 | VIDEO_AGENT_STAGE_COMPLETION_REPORT_001 | 本阶段资产补齐收口报告 | 否 |

## 共性边界

- 不接真实模型。
- 不读取真实素材。
- 不调用执行器。
- 不渲染、不上传、不发布。
- 不真实发送企业微信。
- 不触发 n8n。
- 不改总管、公共组件、服务端口或正式库。

## 自检

- [x] 资产均为 W1/R0 影子资产。
- [x] 未声明正式能力。
- [x] 未触发真实系统。
