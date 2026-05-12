# -*- coding: utf-8 -*-
"""生成 L3 证据缺口统一刷新验收样例。

该脚本只生成股票线影子验收资产，不接入真实行情、企业微信、n8n、服务或交易接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "L3证据缺口统一刷新验收样例_最新.json"
MD_OUT = DATA_DIR / "L3证据缺口统一刷新验收样例_最新.md"


SOURCE_VALIDATIONS = [
    {
        "key": "front_output_gate",
        "label": "标准前台报告输出门禁",
        "path": DATA_DIR / "标准前台报告输出门禁样例验收结果_最新.json",
        "required_for_frontend": True,
    },
    {
        "key": "fundamentals_capital",
        "label": "财报资金证据",
        "path": DATA_DIR / "财报资金证据字段化补齐样例验收结果_最新.json",
        "required_for_frontend": True,
    },
    {
        "key": "industry_price",
        "label": "行业价格连续观测",
        "path": DATA_DIR / "行业价格连续观测字段化补齐样例验收结果_最新.json",
        "required_for_frontend": True,
    },
    {
        "key": "policy_events",
        "label": "政策事件库字段化",
        "path": DATA_DIR / "政策事件库字段化补齐样例验收结果_最新.json",
        "required_for_frontend": True,
    },
    {
        "key": "market_style",
        "label": "市场风格日表字段化",
        "path": DATA_DIR / "市场风格日表字段化补齐样例验收结果_最新.json",
        "required_for_frontend": True,
    },
    {
        "key": "replay_rule_gate",
        "label": "复盘结果到规则候选二次门禁",
        "path": DATA_DIR / "复盘结果到规则候选二次门禁样例验收结果_最新.json",
        "required_for_frontend": False,
    },
]


SAMPLES = [
    {
        "stock_name": "云南锗业",
        "stock_code": "002428",
        "stock_type": "资源/半导体材料",
        "frontend_first_line": "云南锗业（002428）：当前只能纳入观察，不能给强结论。",
        "ready_evidence": ["对象识别", "前台短答门禁", "政策事件字段框架", "行业价格观测字段框架"],
        "key_missing": [
            "锗产品价格连续数据未接入真实日度来源",
            "最新财报与资金证据未形成自动结构化得分",
            "政策事件来源仍是样例/候选状态，未替换为真实可核验链接",
            "市场风格日表未接入真实交易日数据",
        ],
        "conclusion_cap": "可纳入观察",
        "confidence_cap": "medium",
        "frontend_output_guard": "先给结论，再用一句话说明主要原因和缺口，不展开技术指标堆叠。",
        "backend_required_fields": ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"],
    },
    {
        "stock_name": "正丹股份",
        "stock_code": "300641",
        "stock_type": "化工",
        "frontend_first_line": "正丹股份（300641）：结论上限为观察，等待产品价格和资金证据确认。",
        "ready_evidence": ["对象识别", "前台短答门禁", "新增样本验收", "行业价格观测字段框架"],
        "key_missing": [
            "TMA/PTA等关键产品价格连续观测未接入真实来源",
            "财报弹性与资金流向未结构化",
            "政策事件未发现直接强驱动样例",
            "市场风格对化工股的日度适配未接入真实数据",
        ],
        "conclusion_cap": "可纳入观察",
        "confidence_cap": "medium",
        "frontend_output_guard": "不得用短期涨跌代替产品价格和财报弹性证据。",
        "backend_required_fields": ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"],
    },
    {
        "stock_name": "浙商中拓",
        "stock_code": "000906",
        "stock_type": "供应链/大宗商品服务",
        "frontend_first_line": "浙商中拓（000906）：目前偏低置信观察，核心缺口是财报质量和商品景气证据。",
        "ready_evidence": ["对象识别", "前台短答门禁", "新增样本验收"],
        "key_missing": [
            "营收、利润、现金流和负债质量未自动结构化",
            "黑色/有色/大宗商品景气字段未形成连续观测",
            "直接政策事件暴露度缺少可核验记录",
            "市场风格日表未形成真实交易日适配",
        ],
        "conclusion_cap": "可纳入观察",
        "confidence_cap": "low",
        "frontend_output_guard": "若基本面和大宗景气缺口未补齐，不输出强推荐式表达。",
        "backend_required_fields": ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"],
    },
    {
        "stock_name": "三花智控",
        "stock_code": "002050",
        "stock_type": "制造/机器人/热管理",
        "frontend_first_line": "三花智控（002050）：可观察，重点看业绩兑现和制造成长风格配合。",
        "ready_evidence": ["对象识别", "前台短答门禁", "财报资金字段框架"],
        "key_missing": [
            "机构资金和最新财报字段未形成自动复核记录",
            "机器人/热管理产业证据仍缺真实来源连续更新",
            "市场风格对制造成长股的适配未接入真实数据",
        ],
        "conclusion_cap": "可纳入观察",
        "confidence_cap": "medium",
        "frontend_output_guard": "可以说明产业逻辑，但必须同步提示业绩和风格证据缺口。",
        "backend_required_fields": ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"],
    },
    {
        "stock_name": "上纬新材",
        "stock_code": "688585",
        "stock_type": "新材料",
        "frontend_first_line": "上纬新材（688585）：暂不建议强关注，证据缺口较多。",
        "ready_evidence": ["对象识别", "前台短答门禁"],
        "key_missing": [
            "财报资金证据不足",
            "核心产品价格和行业景气缺少连续来源",
            "政策事件暴露度未形成有效样例",
            "市场风格日表未接入真实数据",
        ],
        "conclusion_cap": "暂不建议关注",
        "confidence_cap": "low",
        "frontend_output_guard": "缺口较多时前台优先给风险和待补，不用概念标签抬高结论。",
        "backend_required_fields": ["evidence", "missing", "confidence", "next_review_date", "replay_candidate"],
    },
]


def load_validation(item: dict[str, object]) -> dict[str, object]:
    path = item["path"]
    assert isinstance(path, Path)
    if not path.exists():
        return {
            "key": item["key"],
            "label": item["label"],
            "exists": False,
            "passed": False,
            "required_for_frontend": item["required_for_frontend"],
            "path": str(path),
            "missing_effect": "来源验收文件不存在，相关证据必须标为 missing",
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {
            "key": item["key"],
            "label": item["label"],
            "exists": True,
            "passed": False,
            "required_for_frontend": item["required_for_frontend"],
            "path": str(path),
            "missing_effect": f"来源验收文件无法解析：{exc}",
        }
    return {
        "key": item["key"],
        "label": item["label"],
        "exists": True,
        "passed": data.get("passed") is True,
        "required_for_frontend": item["required_for_frontend"],
        "path": str(path),
        "metrics": data.get("metrics", {}),
        "missing_effect": "若未通过，前台结论必须降级，后台 missing 必须显式列出",
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_validations = [load_validation(item) for item in SOURCE_VALIDATIONS]
    all_sources_present = all(item["exists"] for item in source_validations)
    all_required_sources_passed = all(
        item["passed"] for item in source_validations if item["required_for_frontend"]
    )
    asset = {
        "name": "L3证据缺口统一刷新验收样例",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2 L3证据缺口统一刷新验收样例",
        "status": "shadow_refresh_acceptance",
        "purpose": "统一刷新前台门禁、财报资金、行业价格、政策事件、市场风格和复盘门禁的证据缺口状态，防止后台缺证据时前台仍输出强结论。",
        "not_formal_config": True,
        "not_formal_entry": True,
        "not_external_send": True,
        "not_real_market_data": True,
        "not_score_write": True,
        "not_rule_update": True,
        "refresh_contract": {
            "frontend_rule": "第一行必须明确股票名称和代码，随后给结论；证据过程只作一句话原因，不堆指标。",
            "backend_rule": "后台必须保留 evidence、missing、confidence、next_review_date、replay_candidate。",
            "missing_rule": "任一关键证据缺失时必须写入 missing；关键缺口未关闭时 confidence 不得为 high。",
            "score_rule": "L3评分只能读取结构化证据；样例状态不得写入正式评分。",
            "replay_rule": "人工修正和复盘只进入经验候选，不能自动改正式规则。",
        },
        "source_validations": source_validations,
        "samples": SAMPLES,
        "summary": {
            "source_validation_count": len(source_validations),
            "source_validation_exists_count": len([item for item in source_validations if item["exists"]]),
            "source_validation_passed_count": len([item for item in source_validations if item["passed"]]),
            "all_sources_present": all_sources_present,
            "all_required_sources_passed": all_required_sources_passed,
            "sample_count": len(SAMPLES),
            "high_confidence_allowed_count": 0,
            "formal_score_write_allowed": False,
            "real_external_send_allowed": False,
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
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# L3证据缺口统一刷新验收样例",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W2 L3证据缺口统一刷新验收样例",
        "- 状态：shadow_refresh_acceptance",
        "- 正式评分写入：否",
        "- 企业微信真实外发：否",
        "",
        "## 来源验收",
        "",
        "| 来源 | 文件存在 | 验收通过 | 前台必需 |",
        "| --- | --- | --- | --- |",
    ]
    for item in source_validations:
        lines.append(
            f"| {item['label']} | {item['exists']} | {item['passed']} | {item['required_for_frontend']} |"
        )
    lines.extend(["", "## 样本缺口刷新", ""])
    for sample in SAMPLES:
        lines.extend(
            [
                f"### {sample['stock_name']}（{sample['stock_code']}）",
                "",
                f"- 前台第一行：{sample['frontend_first_line']}",
                f"- 结论上限：{sample['conclusion_cap']}",
                f"- 置信度上限：{sample['confidence_cap']}",
                f"- 前台约束：{sample['frontend_output_guard']}",
                "- 关键缺口：",
            ]
        )
        lines.extend([f"  - {item}" for item in sample["key_missing"]])
        lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
