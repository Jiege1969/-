# -*- coding: utf-8 -*-
"""生成报告缺口优先级排序样例。

仅生成股票线W1影子样例，把报告missing拆成P0/P1/P2，不写正式评分规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "报告缺口优先级排序样例_最新.json"
MD_OUT = DATA_DIR / "报告缺口优先级排序样例_最新.md"


RECORDS = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "missing_priority": {
            "P0": ["锗价连续观测", "政策事件暴露度与时效衰减", "最新财报核心摘要"],
            "P1": ["资金承接变化", "资源板块热度", "公告事项复核"],
            "P2": ["同类资源股对比", "历史政策事件复盘"],
        },
        "front_gap_phrase": "关键缺口优先看锗价、政策暴露度和财报，未补齐前置信度维持medium。",
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "missing_priority": {
            "P0": ["锂价连续观测", "盈利修复证据", "最新财报核心摘要"],
            "P1": ["库存/供需线索", "资金趋势", "新能源板块热度"],
            "P2": ["同业估值对比", "政策候选复核"],
        },
        "front_gap_phrase": "关键缺口优先看锂价、盈利修复和财报，未确认前只适合观察。",
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "missing_priority": {
            "P0": ["半导体景气代理指标", "毛利率趋势", "机构资金变化"],
            "P1": ["政策事件匹配", "产能利用率线索", "板块热度"],
            "P2": ["同业估值对比", "中长期国产化叙事复盘"],
        },
        "front_gap_phrase": "关键缺口优先看景气、毛利率和机构资金，缺证据时不表达科技风格共振。",
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "missing_priority": {
            "P0": ["经营现金流", "负债结构", "商品周期联动"],
            "P1": ["资金承接", "公告风险", "供应链业务景气"],
            "P2": ["同类供应链公司对比", "政策关联度复核"],
        },
        "front_gap_phrase": "关键缺口优先看现金流、负债和商品周期，未补齐前不输出强结论。",
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "missing_priority": {
            "P0": ["核心产品价格连续序列", "利润弹性", "资金承接强弱"],
            "P1": ["价差变化", "订单景气", "化工板块热度"],
            "P2": ["同类化工品对比", "环保/出口政策候选复核"],
        },
        "front_gap_phrase": "关键缺口优先看产品价格、利润弹性和资金承接，补齐前维持观察口径。",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "报告缺口优先级排序样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1报告缺口优先级排序样例",
        "status": "shadow_missing_priority_sample",
        "not_formal_config": True,
        "not_score_write": True,
        "not_entrypoint": True,
        "priority_rules": {
            "P0": "没有该证据会直接限制结论强度或置信度。",
            "P1": "影响报告解释质量和复核重点，但通常不单独阻断观察结论。",
            "P2": "用于增强比较和复盘，不作为当前结论前置条件。",
        },
        "records": RECORDS,
        "summary": {
            "sample_count": len(RECORDS),
            "all_have_p0_p1_p2": True,
            "formal_score_update_allowed": False,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 报告缺口优先级排序样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1报告缺口优先级排序样例",
        "- 状态：shadow_missing_priority_sample",
        "- 边界：不写正式评分规则，不改正式入口。",
        "",
    ]
    for item in RECORDS:
        lines.append(f"## {item['stock']['name']}（{item['stock']['code']}）")
        for priority in ["P0", "P1", "P2"]:
            lines.append(f"- {priority}：{'、'.join(item['missing_priority'][priority])}")
        lines.append(f"- 前台缺口话术：{item['front_gap_phrase']}")
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
