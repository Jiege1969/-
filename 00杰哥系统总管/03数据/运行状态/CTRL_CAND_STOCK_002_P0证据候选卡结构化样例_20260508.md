# CTRL-CAND-STOCK-002 P0证据候选卡结构化样例

- 执行时间：2026-05-08 09:33:44 +08:00
- 资产身份：总管侧 W1/R0 股票 L3 P0 证据候选卡结构化样例
- 来源候选：`D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\受控试用第二批候选清单_20260508.md`
- 来源报告：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\245L3评分基础资产\L3五样本证据缺口优先级报告_最新.md`
- 来源路线：`D:\杰哥智能化系统\00杰哥系统总管\03数据\运行状态\CTRL_TRIAL_STOCK_001_L3五样本证据缺口P0补齐路线_20260508.md`
- 当前定位：证据候选卡字段样例，不是交易建议，不是正式前台入口，不是股票评分自动更新规则

## 一、边界扫描结论

| 扫描项 | 结论 | 说明 |
|---|---|---|
| 是否 W1/R0 | 是 | 仅做证据候选卡结构化样例 |
| 是否真实接入 | 否 | 不接券商、不接交易账号、不调用实盘接口 |
| 是否外发 | 否 | 不发送企业微信、不生成外发荐股文本 |
| 是否 n8n | 否 | 不配置、不触发 n8n |
| 是否服务变更 | 否 | 不改服务脚本、不重启 `19310/19302` |
| 是否删除移动覆盖 | 否 | 不删除、不移动、不归档旧资产 |
| 是否正式结论 | 否 | 不输出买入、卖出、下单、调仓或仓位建议 |
| 是否越权施工 | 否 | 总管只给候选卡结构，不改股票正式配置或入口 |

允许继续：是。

允许范围：基于既有五样本 P0 缺口，生成资金、机构、减持解禁、行业价格观测的候选卡字段样例。

## 二、P0证据候选卡通用字段

| 字段 | 必填 | 说明 |
|---|---|---|
| card_id | 是 | 候选卡编号 |
| stock_name | 是 | 股票名称 |
| stock_code | 是 | 股票代码 |
| evidence_type | 是 | `industry_price` / `fund_flow` / `institution_holding` / `reduction_unlock` |
| priority | 是 | 当前为 `P0` |
| source_name | 是 | 来源名称，必须可复核 |
| source_url_or_path | 是 | 公开链接或本地证据路径 |
| observation_date | 是 | 证据日期或观测日期 |
| collected_at | 是 | 登记时间 |
| value_fields | 否 | 价格、单位、变动、持仓、资金方向等字段 |
| evidence_status | 是 | `missing` / `candidate` / `single_observation` / `source_registered` / `confirmed` |
| l3_missing_link | 是 | 对应 L3 missing 字段 |
| confidence_effect | 是 | 对置信度的影响，只能写 `none` / `raise_candidate` / `needs_more_observations` |
| can_update_score | 是 | 当前必须为 `false`，人工复核前不得改分 |
| can_generate_trade_action | 是 | 必须为 `false` |
| review_questions | 是 | 人工复核问题 |
| boundary_note | 是 | 不交易、不下单、不调仓、不改正式入口 |

## 三、五样本候选卡样例

### 1. 云南锗业：行业价格连续观测候选卡

| 字段 | 内容 |
|---|---|
| card_id | `STOCK_P0_YNGY_INDUSTRY_PRICE_001` |
| stock_name | 云南锗业 |
| stock_code | `sz002428` |
| evidence_type | `industry_price` |
| priority | `P0` |
| source_name | 待填：公开可复核锗价格来源 |
| source_url_or_path | 待填 |
| observation_date | 待填，需形成至少5个连续观测点 |
| value_fields | `price`, `unit`, `currency`, `change_rate`, `source_label` |
| evidence_status | `source_registered` -> `needs_more_observations` |
| l3_missing_link | 行业价格尚未形成可用观测 |
| confidence_effect | `needs_more_observations` |
| can_update_score | `false` |
| can_generate_trade_action | `false` |
| review_questions | 来源是否公开可复核？单位是否一致？是否达到5个连续观测点？ |

### 2. 天齐锂业：行业价格连续观测候选卡

| 字段 | 内容 |
|---|---|
| card_id | `STOCK_P0_TQLY_INDUSTRY_PRICE_001` |
| stock_name | 天齐锂业 |
| stock_code | `sz002466` |
| evidence_type | `industry_price` |
| priority | `P0` |
| source_name | 待填：公开可复核锂盐/锂矿价格来源 |
| source_url_or_path | 待填 |
| observation_date | 已有 `single_observation`，需补连续观测 |
| value_fields | `price`, `unit`, `currency`, `product_type`, `source_label` |
| evidence_status | `single_observation` -> `needs_more_observations` |
| l3_missing_link | 行业价格不足5个连续观测点 |
| confidence_effect | `needs_more_observations` |
| can_update_score | `false` |
| can_generate_trade_action | `false` |
| review_questions | 单点观测是否同口径可延续？产品类型是否与业务暴露一致？ |

### 3. 华虹公司：半导体景气候选卡

| 字段 | 内容 |
|---|---|
| card_id | `STOCK_P0_HHGS_INDUSTRY_PRICE_001` |
| stock_name | 华虹公司 |
| stock_code | `sh688347` |
| evidence_type | `industry_price` |
| priority | `P0` |
| source_name | 待填：公开可复核半导体/晶圆景气或价格来源 |
| source_url_or_path | 待填 |
| observation_date | 待填 |
| value_fields | `indicator_name`, `indicator_value`, `unit`, `period`, `source_label` |
| evidence_status | `missing` |
| l3_missing_link | 行业价格或景气观测缺失 |
| confidence_effect | `needs_more_observations` |
| can_update_score | `false` |
| can_generate_trade_action | `false` |
| review_questions | 指标是否能代表公司业务景气？是否可连续跟踪？ |

### 4. 浙商中拓：大宗供应链景气候选卡

| 字段 | 内容 |
|---|---|
| card_id | `STOCK_P0_ZSZT_INDUSTRY_PRICE_001` |
| stock_name | 浙商中拓 |
| stock_code | `sz000906` |
| evidence_type | `industry_price` |
| priority | `P0` |
| source_name | 待填：公开可复核大宗供应链或主营景气来源 |
| source_url_or_path | 待填 |
| observation_date | 待填 |
| value_fields | `indicator_name`, `indicator_value`, `unit`, `period`, `source_label` |
| evidence_status | `missing` |
| l3_missing_link | 行业价格或业务景气观测缺失 |
| confidence_effect | `needs_more_observations` |
| can_update_score | `false` |
| can_generate_trade_action | `false` |
| review_questions | 该指标与主营收入是否相关？是否存在公开连续数据？ |

### 5. 正丹股份：TMA相关价格连续观测候选卡

| 字段 | 内容 |
|---|---|
| card_id | `STOCK_P0_ZDGF_INDUSTRY_PRICE_001` |
| stock_name | 正丹股份 |
| stock_code | `sz300641` |
| evidence_type | `industry_price` |
| priority | `P0` |
| source_name | 待填：公开可复核 TMA 相关价格来源 |
| source_url_or_path | 待填 |
| observation_date | 待填，需形成至少5个连续观测点 |
| value_fields | `price`, `unit`, `currency`, `product_type`, `source_label` |
| evidence_status | `source_registered` -> `needs_more_observations` |
| l3_missing_link | 行业价格尚未形成可用观测 |
| confidence_effect | `needs_more_observations` |
| can_update_score | `false` |
| can_generate_trade_action | `false` |
| review_questions | 价格口径是否稳定？是否能持续取得？是否与公司主营相关？ |

## 四、资金/机构/减持解禁通用候选卡

| 字段 | 资金候选卡 | 机构候选卡 | 减持解禁候选卡 |
|---|---|---|---|
| evidence_type | `fund_flow` | `institution_holding` | `reduction_unlock` |
| source_name | 待填：公开行情/资金来源 | 待填：公告/定期报告/公开披露 | 待填：公告/交易所披露 |
| value_fields | `net_inflow`, `period`, `rank`, `source_label` | `holder_name`, `holding_ratio`, `change`, `period` | `share_count`, `ratio`, `date`, `holder`, `plan_status` |
| evidence_status | `candidate` 或 `missing` | `candidate` 或 `missing` | `candidate` 或 `missing` |
| can_update_score | `false` | `false` | `false` |
| can_generate_trade_action | `false` | `false` | `false` |
| review_questions | 是否连续？是否异常？是否可复核？ | 是否最新？是否同口径？是否公告来源？ | 是否已执行？是否已过期？是否与流通盘相关？ |

适用五个样本：

- 云南锗业 `sz002428`
- 天齐锂业 `sz002466`
- 华虹公司 `sh688347`
- 浙商中拓 `sz000906`
- 正丹股份 `sz300641`

## 五、股票线回传要求

股票线后续如按本候选卡补证据，只回传以下内容：

1. 新增候选卡文件路径。
2. 每张卡的 `card_id`、`stock_code`、`evidence_type`、`evidence_status`。
3. 仍然 missing 的字段。
4. 是否达到人工复核条件。
5. 边界确认：不交易、不接券商、不改正式入口、不生成买卖/仓位动作。

## 六、R0 自检

- 只新增总管侧结构化样例。
- 未改股票正式配置。
- 未改股票正式脚本。
- 未改股票前台入口。
- 未抓取新增行情。
- 未调用券商接口。
- 未输出交易建议。
- 未发送企业微信。
- 未触发 n8n。
- 未改服务脚本。
- 未重启 `19310/19302`。

`[自检: CTRL-CAND-STOCK-002已完成, 风险等级: W1/R0, 产物: CTRL_CAND_STOCK_002_P0证据候选卡结构化样例_20260508.md/json, 边界: 守住了。]`
