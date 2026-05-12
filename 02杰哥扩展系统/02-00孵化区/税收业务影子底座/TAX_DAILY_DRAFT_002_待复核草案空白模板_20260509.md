# TAX_DAILY_DRAFT_002 待复核草案空白模板

- 生成时间：2026-05-09
- 来源入口：`TAX_DAILY_INTAKE_002`
- 状态：空白模板
- 性质：待复核草案，不是正式税务意见

## 一、草案字段

| 字段 | 内容 |
|:---|:---|
| draft_id | TAX_DAILY_DRAFT_002 |
| related_intake | TAX_DAILY_INTAKE_002 |
| user_question_summary | 待填写 |
| scenario_classification | 待填写 |
| applicable_policy_candidates | 待填写 |
| non_applicable_policy_candidates | 待填写 |
| analysis_draft | 待填写 |
| missing_facts | 待填写 |
| risk_points | 待填写 |
| review_questions | 待填写 |
| confidence_level | 待填写 |
| human_review_status | 待复核 |

## 二、输出约束

- 必须区分“政策候选”“适用判断”“待补事实”。
- 缺少关键事实时，只能输出缺口问题，不能强行结论。
- 草案必须保留人工复核入口。
- 草案不得直接用于纳税申报、退税、开票、合同或对外承诺。

## 三、边界声明

不触发 n8n，不发送企业微信，不写正式库，不调用税务办理接口，不形成正式税务意见。
