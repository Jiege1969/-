# -*- coding: utf-8 -*-
"""
名称：生成300只盘后深度分析预处理包.py
作用：将300只试运行池盘后轻扫描候选整理为深度分析预处理包。
触发方式：python 生成300只盘后深度分析预处理包.py
依赖：Python标准库；300只盘后深度分析预处理规则.json；300只试运行池盘后轻扫描_最新.json；300只试运行池_行情补齐_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读轻扫描结果和行情补齐池，只写新系统预处理包；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只盘后深度分析预处理包脚本。
标识：stock-trial-pool-300-deep-preprocess
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_quote_map(pool: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")): item for item in pool.get("股票池", [])}


def build_need_list(health: str) -> list[str]:
    needs = ["历史K线", "技术指标", "公告", "财务", "行业事件"]
    if health != "健康":
        needs.insert(0, "实时行情二次校验")
    return needs


def build_item(candidate: dict[str, Any], quote: dict[str, Any], health: str) -> dict[str, Any]:
    return {
        "代码": candidate.get("代码"),
        "名称": candidate.get("名称"),
        "市场": candidate.get("市场") or quote.get("市场"),
        "行业": candidate.get("行业") or quote.get("行业") or "未分类",
        "轻扫描评分": candidate.get("轻扫描评分"),
        "现价": quote.get("现价", candidate.get("现价")),
        "涨跌幅": quote.get("涨跌幅", candidate.get("涨跌幅")),
        "成交额": quote.get("成交额", candidate.get("成交额")),
        "流通市值": quote.get("流通市值", candidate.get("流通市值")),
        "总市值": quote.get("总市值", candidate.get("总市值")),
        "行情时间": quote.get("行情时间"),
        "候选理由": candidate.get("候选理由", []),
        "风险和降级说明": candidate.get("风险和降级说明", []),
        "需要补齐": build_need_list(health),
        "预处理结论": "进入深度分析预处理，不直接推送，不形成买卖指令。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只盘后深度分析预处理报告",
        "",
        f"生成时间：{report['生成时间']}",
        f"数据健康度：{report['数据健康度']}",
        "",
        "说明：本报告只确定深度分析入口，不构成投资建议，不自动交易，不触发企业微信真实发送。",
        "",
        "## 预处理候选",
        "",
    ]
    for index, item in enumerate(report["预处理候选"], start=1):
        needs = "、".join(item["需要补齐"])
        lines.append(f"{index}. {item['名称']}（{item['代码']}）：轻扫描评分 {item['轻扫描评分']}，现价 {item.get('现价')}，涨跌幅 {item.get('涨跌幅')}%。")
        lines.append(f"   - 下一步补齐：{needs}")
        lines.append(f"   - 结论：{item['预处理结论']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式业务库。",
            "- 未调用券商接口，未自动交易。",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只盘后深度分析预处理规则.json"
    rule = load_json(rule_path)
    scan_path = root / rule["输入"]["轻扫描结果"]
    quote_path = root / rule["输入"]["行情补齐池"]
    scan = load_json(scan_path)
    quote_map = build_quote_map(load_json(quote_path))
    health = scan.get("数据健康度", {}).get("状态", "未知")
    candidates = [
        build_item(item, quote_map.get(str(item.get("代码", "")), {}), health)
        for item in scan.get("候选清单", [])
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "轻扫描文件": str(scan_path),
        "行情补齐文件": str(quote_path),
        "数据健康度": health,
        "候选数量": len(candidates),
        "预处理候选": candidates,
        "安全边界": rule.get("安全边界", {}),
        "实际动作": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只盘后深度分析预处理包_{stamp}.json"
    latest = output_dir / rule["输出"]["最新文件"]
    markdown = output_dir / f"300只盘后深度分析预处理报告_{stamp}.md"
    markdown_latest = output_dir / rule["输出"]["报告文件"]
    write_json(output, report)
    write_json(latest, report)
    text = build_markdown(report)
    write_text(markdown, text)
    write_text(markdown_latest, text)
    print(json.dumps({"候选数量": len(candidates), "数据健康度": health, "输出": str(output)}, ensure_ascii=False))
    return 0 if 5 <= len(candidates) <= 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
