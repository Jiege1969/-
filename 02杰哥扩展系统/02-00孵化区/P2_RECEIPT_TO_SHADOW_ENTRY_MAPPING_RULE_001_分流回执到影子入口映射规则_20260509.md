# P2_RECEIPT_TO_SHADOW_ENTRY_MAPPING_RULE_001 分流回执到影子入口映射规则

- 生成时间：2026-05-09
- 所属阶段：P2-S8
- 所属层级：扩展系统孵化区横向能力
- 状态：映射预演规则，不是自动写入器

## 一、目的

P2-S7 已证明分流回执可以生成。P2-S8 规定分流回执如何映射到影子入口字段，确保真实材料后续进入时，只形成“入口预填建议”和“待复核缺口”，不直接改写入口卡、不生成业务结论、不触发真实动作。

## 二、映射路线

| target_line | 目标入口 | 映射动作 |
|:---|:---|:---|
| tax | `TAX_DAILY_INTAKE_002` | 映射为税收脱敏问题接入字段建议 |
| office_work | `OFFICE_SHADOW_002` | 映射为流程资料登记影子样例字段建议 |
| video_production | `VIDEO_P2_REVIEW_CHAIN_NEXT_001` | 映射为脚本/分镜/素材授权/平台规范复核链字段建议 |
| shared_policy_evidence | `P2_SHARED_POLICY_READONLY_NEXT_001` | 映射为政策证据只读调用字段建议 |
| pause | `gap_or_redline_record` | 只映射暂停原因、红线状态和下一步人工确认，不进入影子入口 |

## 三、硬规则

- 只生成映射预演，不改写目标入口 JSON。
- 目标入口必须保持空白或待复核状态。
- `pause` 路线不得进入业务入口。
- `redline_status=blocked` 时只能生成阻断记录建议。
- `human_review_required` 必须保持 true。
- `formal_capability_claim` 必须保持 false。

## 四、禁止动作

- 不读取真实材料。
- 不扫描用户目录。
- 不触发 n8n。
- 不发送企业微信。
- 不写正式库。
- 不重启服务。
- 不交易。
- 不办理税务。
- 不渲染或发布视频。
