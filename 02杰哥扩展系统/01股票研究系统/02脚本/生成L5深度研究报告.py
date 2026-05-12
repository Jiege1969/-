# -*- coding: utf-8 -*-
"""
名称：生成L5深度研究报告.py
作用：基于重点关注池候选池生成L5深度研究报告和候选池日报。
触发方式：python 生成L5深度研究报告.py
依赖：Python标准库；L5深度研究报告规则.json；重点关注池候选池_最新.json；重点关注池公开行情快照_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读新系统候选池、行情和指标；只写新系统报告；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建L5深度研究报告生成脚本。
标识：stock-l5-deep-research-report-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def quote_map(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    return {str(item.get("代码", "")).zfill(6): item for item in data.get("行情", [])}


def load_data_health(root: Path) -> dict[str, Any]:
    indicators = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json", {})
    history = load_json(root / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json", {})
    indicator_rows = indicators.get("技术指标", [])
    total = len(indicator_rows)
    success = sum(1 for item in indicator_rows if item.get("状态") == "成功" or item.get("计算状态") == "成功")
    rate = round(success / total * 100, 2) if total else 0
    if rate >= 95:
        level = "优秀"
        suggestion = "数据链路健康，可按常规强度使用L5日报。"
    elif rate >= 85:
        level = "可用"
        suggestion = "数据链路可用，少量缺口不影响候选池整体观察。"
    elif rate > 0:
        level = "降级"
        suggestion = "数据链路处于降级状态，适合做观察和复盘，不宜单独作为强化判断依据。"
    else:
        level = "暂停"
        suggestion = "数据链路不可用，应先恢复行情或历史K线来源，再生成研究结论。"
    return {
        "股票数量": total,
        "指标成功数量": success,
        "成功率": rate,
        "健康等级": level,
        "历史行情降级说明": history.get("降级说明", ""),
        "建议": suggestion,
    }


def normalize_code(code: str) -> str:
    code = str(code or "")
    if code.startswith(("sh", "sz")):
        return code[2:]
    return code.zfill(6)


def enrich_items(items: list[dict[str, Any]], quotes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for item in items:
        quote = quotes.get(normalize_code(item.get("代码", "")), {})
        enriched.append({
            **item,
            "行情": quote,
            "研究摘要": build_summary(item, quote),
            "人工确认建议": build_confirm_hint(item),
        })
    return enriched


def build_summary(item: dict[str, Any], quote: dict[str, Any]) -> str:
    price_text = ""
    if quote:
        price_text = f"公开行情显示最新价{quote.get('最新价')}，涨跌幅{quote.get('涨跌幅')}%，行业{quote.get('行业')}。"
    basis = "；".join(item.get("依据", []))
    risks = "；".join(item.get("风险", []))
    return f"{price_text}系统评分{item.get('系统评分')}，当前层级{item.get('层级')}。主要依据：{basis}。主要风险：{risks}。"


def build_confirm_hint(item: dict[str, Any]) -> str:
    if item.get("层级") == "L5深度研究":
        return f"可回复：继续观察：{item.get('名称')}，原因；或确认L4：{item.get('名称')}，原因。"
    if item.get("层级") == "L6轻度关注":
        return f"可回复：继续观察：{item.get('名称')}，原因；或暂不关注：{item.get('名称')}，原因。"
    return f"可回复：无价值：{item.get('名称')}，原因；或暂不关注：{item.get('名称')}，原因。"


def build_markdown(report: dict[str, Any]) -> str:
    pool = report["候选池"]
    lines = [
        "# L5深度研究候选日报",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "声明：本报告只用于研究辅助，不构成投资建议，不自动交易。",
        "",
        "## 一、候选池概览",
        "",
        f"- L5深度研究：{len(pool['L5深度研究'])}只",
        f"- L6轻度关注：{len(pool['L6轻度关注'])}只",
        f"- L7系统过滤：{len(pool['L7系统过滤'])}只",
        "",
        "## 二、数据健康度",
        "",
        f"- 健康等级：{report.get('数据健康度', {}).get('健康等级')}",
        f"- 指标成功：{report.get('数据健康度', {}).get('指标成功数量')}/{report.get('数据健康度', {}).get('股票数量')}，成功率{report.get('数据健康度', {}).get('成功率')}%",
        f"- 降级说明：{report.get('数据健康度', {}).get('历史行情降级说明') or '无'}",
        f"- 使用建议：{report.get('数据健康度', {}).get('建议')}",
        "",
        "## 三、L5深度研究候选",
        "",
    ]
    for item in pool["L5深度研究"]:
        lines.append(f"### {item['名称']}（{item['代码']}）")
        lines.append(f"- 评分：{item['系统评分']}")
        lines.append(f"- 摘要：{item['研究摘要']}")
        lines.append(f"- 确认入口：{item['人工确认建议']}")
        lines.append("")
    if not pool["L5深度研究"]:
        lines.append("暂无L5候选。")
        lines.append("")
    lines.append("## 四、L6轻度关注")
    lines.append("")
    for item in pool["L6轻度关注"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：评分{item['系统评分']}。{item['人工确认建议']}")
    if not pool["L6轻度关注"]:
        lines.append("- 暂无。")
    lines.extend(["", "## 五、L7过滤与数据不足", ""])
    for item in pool["L7系统过滤"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：{';'.join(item.get('风险', []))}")
    if not pool["L7系统过滤"]:
        lines.append("- 暂无。")
    lines.extend(["", "## 六、后续复盘计划", "", "系统会把本次候选写入系统判断账，并等待人工反馈和后续T+1/T+3/T+5/T+20验证。", ""])
    lines.extend([
        "## 七、人工反馈入口",
        "",
        "无论当前是否出现L5候选，都可以用以下格式反馈，系统会写入人工决策账：",
        "",
        "- 继续观察：股票名称，原因",
        "- 暂不关注：股票名称，原因",
        "- 无价值：股票名称，原因",
        "- 确认L4：股票名称，原因（必须由你人工确认）",
        ""
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "L5深度研究报告规则.json")
    pool_data = load_json(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json")
    quotes = quote_map(root)
    raw_pool = pool_data.get("候选池", {})
    pool = {
        "L5深度研究": enrich_items(raw_pool.get("L5深度研究", []), quotes),
        "L6轻度关注": enrich_items(raw_pool.get("L6轻度关注", []), quotes),
        "L7系统过滤": enrich_items(raw_pool.get("L7系统过滤", []), quotes),
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "L5深度研究报告规则.json"),
        "候选池文件": str(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json"),
        "报告结构": rules.get("报告结构", []),
        "数据健康度": load_data_health(root),
        "候选池": pool,
        "人工确认提示": rules.get("人工确认提示", []),
        "安全边界": {
            "是否调用大模型": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "15深度研究"
    report_dir = root / "03数据" / "03研究报告"
    output = output_dir / f"L5深度研究报告_{timestamp}.json"
    latest = output_dir / "L5深度研究报告_最新.json"
    markdown = report_dir / f"L5深度研究候选日报_{timestamp}.md"
    markdown_latest = report_dir / "L5深度研究候选日报_最新.md"
    write_json(output, report)
    write_json(latest, report)
    text = build_markdown(report)
    write_text(markdown, text)
    write_text(markdown_latest, text)
    print(json.dumps({"L5数量": len(pool["L5深度研究"]), "输出": str(output), "报告": str(markdown)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
