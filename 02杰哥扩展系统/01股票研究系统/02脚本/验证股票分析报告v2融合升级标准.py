# -*- coding: utf-8 -*-
"""
名称：验证股票分析报告v2融合升级标准.py
作用：只读验收股票分析报告v2.1融合升级标准是否已纳入配置、文档和复盘规则。
触发方式：python 验证股票分析报告v2融合升级标准.py
安全边界：只读配置和文档；只写03数据/运行验收报告；不改运行入口；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {
        "项目": name,
        "通过": bool(condition),
        "说明": detail,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票分析报告v2融合升级标准验收 - {report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 验收项",
        "",
    ]
    for item in report["验收项"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['项目']}：{mark}。{item.get('说明', '')}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 只读验收配置和文档。",
        "- 不修改股票运行入口。",
        "- 不发送企业微信。",
        "- 不触发n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    frontend_path = ROOT / "01配置" / "股票前台输出标准_v2.json"
    report_template_path = ROOT / "01配置" / "股票报告模板.json"
    review_rule_path = ROOT / "01配置" / "研究决策复盘闭环规则.json"
    standard_doc_path = ROOT / "07文档" / "股票分析报告v2融合升级执行标准_20260504.md"
    strategy_doc_path = ROOT / "07文档" / "股票前台策略结论输出标准_v1.0_20260502.md"
    method_doc_path = ROOT / "07文档" / "股票分析方法与报告标准_v2_结合现有系统.md"
    loop_doc_path = ROOT / "07文档" / "股票分析报告v2与轻量学习闭环施工方案_v1.0_20260502.md"

    frontend = load_json(frontend_path)
    template = load_json(report_template_path)
    review_rule = load_json(review_rule_path)
    standard_doc = load_text(standard_doc_path)
    strategy_doc = load_text(strategy_doc_path)
    method_doc = load_text(method_doc_path)
    loop_doc = load_text(loop_doc_path)

    short_template = frontend.get("融合报告短文模板", {})
    upgrade = template.get("v2融合升级", {})
    review_short = review_rule.get("微信短文复盘接入", {})

    required_short_fields = [
        "股票名称与一句话结论",
        "逻辑：行业逻辑+公司卡位+主要矛盾",
        "财务：最少数字验证，说明支持/部分支持/不支持",
        "观察条件：价格区间+N日M次收盘条件+成交额阈值实际数值",
        "转强条件：突破价格+连续天数+成交额阈值实际数值",
        "失败条件：风险线+跌破后的修复期限+观察降级处理",
        "风险：一句话说明最大风险和不适合的人群",
    ]
    required_min_dataset = [
        "行业景气判断及来源",
        "近三年营收与净利润及增速",
        "最新季度营收与净利润",
        "毛利率",
        "净利率",
        "ROE",
        "经营现金流净额",
        "当前PE",
        "当前PB或行业估值对比",
        "支撑/观察区",
        "压力/转强线",
        "风险线",
        "截至昨日近5日平均成交额",
        "20日均额或成交活跃对比",
    ]

    checks = [
        check(bool(short_template), "前台输出标准已新增融合报告短文模板", str(frontend_path)),
        check(
            all(field in short_template.get("六段式字段顺序", []) for field in required_short_fields),
            "微信短文6+1段式字段完整",
            "结论、逻辑、财务、观察、转强、失败、风险",
        ),
        check(
            "截至昨日、不含当天" in json.dumps(short_template, ensure_ascii=False),
            "成交额均额基准已明确不含当天",
            "避免循环定义",
        ),
        check(
            "当前近5日均额：XX亿元" in json.dumps(short_template, ensure_ascii=False),
            "微信短文要求展开阈值实际数字",
            "样例保留系统填数占位",
        ),
        check(bool(upgrade), "股票报告模板已新增v2融合升级", str(report_template_path)),
        check(
            all(field in upgrade.get("最小数据集", {}).get("缺一不可字段", []) for field in required_min_dataset),
            "最小数据集字段完整",
            "关键数据缺失时必须降级",
        ),
        check(
            "利润下滑主因待核验" in json.dumps(upgrade, ensure_ascii=False),
            "利润下滑原因缺失时必须提示待核验",
            "避免只写利润下滑不解释",
        ),
        check(bool(review_short), "复盘闭环规则已接入微信短文复盘字段", str(review_rule_path)),
        check(
            "观察条件" in json.dumps(review_short, ensure_ascii=False)
            and "转强条件" in json.dumps(review_short, ensure_ascii=False)
            and "失败条件" in json.dumps(review_short, ensure_ascii=False),
            "复盘账包含观察/转强/失败条件",
            "可验证、可复盘",
        ),
        check("三层输出机制" in standard_doc, "融合升级执行标准文档存在三层输出机制", str(standard_doc_path)),
        check("最小数据集" in standard_doc, "融合升级执行标准文档存在最小数据集", str(standard_doc_path)),
        check("模糊表达禁用" in standard_doc, "融合升级执行标准文档存在模糊表达禁用", str(standard_doc_path)),
        check("融合升级补充规则" in strategy_doc, "前台策略结论标准已补充融合升级规则", str(strategy_doc_path)),
        check("融合升级标准接入" in method_doc, "股票分析方法标准已登记融合升级", str(method_doc_path)),
        check("融合报告短文接入学习闭环" in loop_doc, "轻量学习闭环已登记微信短文接入", str(loop_doc_path)),
    ]

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票分析报告v2融合升级标准验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "验收项": checks,
        "安全边界": {
            "是否修改运行入口": False,
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = ROOT / "03数据" / "运行验收"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"股票分析报告v2融合升级标准验收_{stamp}.json"
    output_md = output_dir / f"股票分析报告v2融合升级标准验收_{stamp}.md"
    latest_json = output_dir / "股票分析报告v2融合升级标准验收_最新.json"
    latest_md = output_dir / "股票分析报告v2融合升级标准验收_最新.md"

    text = json.dumps(report, ensure_ascii=False, indent=2)
    output_json.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    markdown = build_markdown(report)
    output_md.write_text(markdown, encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
