# REVIEW RECEIPT STOCK POLICY EVIDENCE 001 空白复核回执

> 版本：v1.0  
> 日期：2026-05-07  
> 资产身份：股票政策证据调用人工复核回执影子模板  
> 风险等级：W1  
> 边界：复核回执模板，不改股票正式配置，不生成买卖建议，不触发前台或外发。  

## 一、复核对象

| 字段 | 内容 |
|:---|:---|
| sample_id | STOCK 001 |
| sample_file | `共享政策证据只读调用样例_STOCK_001_锗出口管制政策事件_v1.0.md/json` |
| evidence_source | 股票政策事件库 |
| policy_event | 锗出口管制政策事件 |

## 二、证据复核

| 复核项 | 结果 | 说明 |
|:---|:---|:---|
| source_url 是否可追溯 | 待填写 |  |
| source_level 是否保留 | 待填写 |  |
| status 是否保留 | 待填写 |  |
| risk_counterpoint 是否保留 | 待填写 |  |
| 是否误写成买卖建议 | 待填写 |  |
| 是否替代财报/行情/技术证据 | 待填写 |  |

## 三、人工意见

| 字段 | 内容 |
|:---|:---|
| human_feedback | 待填写 |
| correction_needed | 待填写 |
| correction_type | 证据缺失 / 状态误读 / 风险反例缺失 / 越权结论 / 其他 |
| next_action | 待填写 |

## 四、复核结论

请选择：

- [ ] pass_shadow：影子样例结构通过。
- [ ] pass_with_notes：有问题但不越界。
- [ ] fail_boundary：出现越权结论或边界问题。
- [ ] need_more_evidence：证据不足。
- [ ] evolution_candidate：可作为后续经验候选。

## 五、硬边界

- 不得把政策利好直接写成买入建议。
- 不得替代财报、行情、技术结构证据。
- 不得触发企业微信、n8n、前台推送或交易。
- 人工意见只进入复盘或经验候选，不自动改正式规则。
