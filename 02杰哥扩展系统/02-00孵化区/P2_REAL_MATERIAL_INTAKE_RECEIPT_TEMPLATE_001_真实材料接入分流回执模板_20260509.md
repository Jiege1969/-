# P2_REAL_MATERIAL_INTAKE_RECEIPT_TEMPLATE_001 真实材料接入分流回执模板

- 生成时间：2026-05-09
- 所属阶段：P2-S6
- 所属层级：扩展系统孵化区横向能力
- 状态：空白回执模板，不是正式业务回执

## 一、用途

真实脱敏材料进入 P2 分流门后，必须用本模板记录分流结论。它记录的是“材料能否进入影子、进入哪条线、为什么暂停、下一步允许什么”，不是税务意见、办公审批、视频发布许可或正式政策适用结论。

## 二、回执字段

| 字段 | 内容 |
|:---|:---|
| receipt_id | 待生成 |
| material_id | 待填写 |
| received_at | 待填写 |
| source_type | 用户提供 / 官方公开 / 历史样例 / 人工经验 / 待核验 |
| source_path_or_url | 待填写；不主动扫描未指定目录 |
| authorization_status | 已授权 / 仅参考 / 禁止使用 / 待确认 |
| sensitivity | 无敏感 / 财务 / 人事 / 合同 / 客户 / 素材版权 / 账号 / 待判 |
| desensitized_status | 已脱敏 / 未脱敏 / 不适用 / 待确认 |
| target_line | tax / office_work / video_production / shared_policy_evidence / pause |
| target_entry | 对应影子入口或 `gap_or_redline_record` |
| can_enter_shadow | 是 / 否 / 待确认 |
| pause_reasons | 无 / 未授权 / 来源不清 / 敏感内容未脱敏 / 命中真实执行请求 / 其他 |
| next_allowed_action | 登记资料 / 生成待复核草案 / 只记录缺口 / 暂停 |
| human_review_required | 是 |
| human_review_status | 待复核 |
| redline_status | pass / blocked |
| redline_reasons | 无 / 待填写 |
| formal_capability_claim | 否 |
| receipt_status | blank_template / draft / reviewed |

## 三、红线确认

| 红线 | 状态 |
|:---|:---|
| trigger_n8n | false |
| send_wecom | false |
| write_formal_database | false |
| scan_unspecified_directory | false |
| copy_sensitive_material | false |
| tax_filing | false |
| invoice_action | false |
| tax_refund_action | false |
| trade | false |
| connect_real_office_system | false |
| render_upload_or_publish_video | false |
| claim_formal_capability | false |

## 四、使用规则

- 没有本回执，不得把真实材料推进到影子入口卡。
- `human_review_required` 必须为“是”。
- `formal_capability_claim` 必须为“否”。
- 命中暂停条件时，只能写 `pause_reasons` 和缺口，不得生成业务草案。
- 可进入影子的材料，也只能进入对应影子入口或待复核链。
