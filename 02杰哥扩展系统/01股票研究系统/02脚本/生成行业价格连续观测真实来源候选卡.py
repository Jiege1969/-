# -*- coding: utf-8 -*-
"""生成行业价格连续观测真实来源候选卡。

本脚本只产出影子候选资产，不接生产数据源、不写正式配置、不触发外发。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "行业价格连续观测真实来源候选卡_最新.json"
MD_OUT = DATA_DIR / "行业价格连续观测真实来源候选卡_最新.md"


OBSERVATION_DOMAINS = [
    {
        "domain": "germanium_materials",
        "display_name": "锗及小金属",
        "priority": "P0",
        "candidate_sources": ["行业协会/公开报价快照", "主流资讯终端人工摘录", "上市公司公告中的价格描述"],
        "candidate_fields": ["产品名称", "报价日期", "报价区间", "单位", "同比/环比变化", "来源链接或人工记录"],
        "frontend_gate": "缺少连续两期价格观测时，前台不得声称价格趋势已确认。",
    },
    {
        "domain": "chemical_materials",
        "display_name": "化工材料",
        "priority": "P0",
        "candidate_sources": ["公开商品价格快照", "行业网站人工摘录", "公司公告/调研纪要中的价格线索"],
        "candidate_fields": ["产品名称", "地区/规格", "报价日期", "价格", "涨跌幅", "来源可信度"],
        "frontend_gate": "缺少规格口径时，只能提示价格线索，不能做强趋势判断。",
    },
    {
        "domain": "new_energy_materials",
        "display_name": "新能源材料",
        "priority": "P0",
        "candidate_sources": ["公开锂电材料价格快照", "行业周报人工摘录", "交易所/公司公告线索"],
        "candidate_fields": ["材料品类", "规格", "报价日期", "均价", "周/月变化", "库存或供需备注"],
        "frontend_gate": "缺少价格与库存/供需备注时，不得把价格波动直接解释为业绩变化。",
    },
    {
        "domain": "logistics_bulk",
        "display_name": "物流与大宗相关",
        "priority": "P1",
        "candidate_sources": ["公开运价指数", "大宗商品价格快照", "公司经营公告"],
        "candidate_fields": ["指数名称", "观察日期", "指数值", "变化方向", "关联业务说明"],
        "frontend_gate": "缺少业务关联说明时，不得将指数变化直接映射到单股结论。",
    },
]


SAMPLE_MAPPING = [
    {"stock_name": "云南锗业", "stock_code": "002428", "domains": ["germanium_materials"]},
    {"stock_name": "正丹股份", "stock_code": "300641", "domains": ["chemical_materials"]},
    {"stock_name": "天齐锂业", "stock_code": "002466", "domains": ["new_energy_materials"]},
    {"stock_name": "浙商中拓", "stock_code": "000906", "domains": ["logistics_bulk", "chemical_materials"]},
]


def build_markdown(asset: dict) -> str:
    lines = [
        "# 行业价格连续观测真实来源候选卡",
        "",
        f"- 生成时间：{asset['generated_at']}",
        "- 资产身份：W2 低风险影子候选卡",
        "- 真实数据源接入：否",
        "- 正式配置：否",
        "- 交易能力：否",
        "",
        "## 观察域",
        "",
        "| 观察域 | 优先级 | 候选来源 | 候选字段 | 前台门禁 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in asset["observation_domains"]:
        lines.append(
            f"| {item['display_name']} | {item['priority']} | {'；'.join(item['candidate_sources'])} | "
            f"{'、'.join(item['candidate_fields'])} | {item['frontend_gate']} |"
        )
    lines.extend(["", "## 样本映射", "", "| 股票 | 代码 | 观察域 |", "| --- | --- | --- |"])
    name_by_domain = {item["domain"]: item["display_name"] for item in asset["observation_domains"]}
    for item in asset["sample_mapping"]:
        lines.append(f"| {item['stock_name']} | {item['stock_code']} | {'、'.join(name_by_domain.get(domain, domain) for domain in item['domains'])} |")
    lines.extend(["", "## 接入前约束", ""])
    lines.extend([f"- {item}" for item in asset["acceptance_rules"]])
    return "\n".join(lines)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "行业价格连续观测真实来源候选卡",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2_shadow_candidate_card",
        "status": "candidate_only_not_connected",
        "purpose": "登记行业价格连续观测的候选来源、字段和前台门禁，避免单点价格线索被误当作确定趋势。",
        "observation_domains": OBSERVATION_DOMAINS,
        "sample_mapping": SAMPLE_MAPPING,
        "acceptance_rules": [
            "必须保留来源、日期、规格、单位和连续观察期字段。",
            "候选来源未人工核验前，不得写入正式数据源配置。",
            "缺少连续两期观察时，前台不得使用趋势已确认类表达。",
            "行业价格只能作为证据链字段，不能直接触发推荐或交易判断。",
        ],
        "summary": {
            "domain_count": len(OBSERVATION_DOMAINS),
            "sample_stock_count": len(SAMPLE_MAPPING),
            "candidate_only": True,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(asset), encoding="utf-8")
    print(json.dumps({"status": "ok", "path": str(JSON_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
