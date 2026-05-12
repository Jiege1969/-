# VIDEO_AGENT_FINAL_CONFIRMATION_MISSING_MATERIAL_CHECKLIST_001 发布前最终确认缺口清单模板 v1.0

- 资产类型：缺口清单模板
- 施工等级：W1/W2 低风险影子施工
- 适用范围：发布前最终人工确认之前的材料缺口核对
- 状态：草案模板

## 模板用途

当最终人工确认质量检查未通过时，用本清单列出缺失材料、对应复核队列、责任角色和关闭条件，避免笼统地说“还不能发布”。

## 缺口字段

| 字段 | 填写说明 |
|---|---|
| gap_id | 缺口编号 |
| task_id | 视频任务编号 |
| missing_material | 缺失材料 |
| related_gate | 关联门禁 |
| review_queue | 复核队列 |
| owner_role | 责任角色 |
| required_output | 所需输出物 |
| close_condition | 关闭条件 |
| blocker_level | 普通缺口、重大缺口、红线阻断 |
| real_system_triggered | 必须为否 |

## 空白清单

| gap_id | task_id | missing_material | related_gate | review_queue | owner_role | required_output | close_condition | blocker_level | real_system_triggered |
|---|---|---|---|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 普通缺口 | 否 |

## 固定规则

1. 每个缺口必须能追溯到一个门禁。
2. 每个缺口必须有复核队列和所需输出物。
3. 红线缺口不得由视频线自行关闭。
4. 缺口清单补齐不等于真实发布。

## 边界

本模板不创建真实工单、不分派真实人员、不触发企业微信或发布工具。
