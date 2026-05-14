# -*- coding: utf-8 -*-
"""
名称：验证收盘短线观察前台条件.py
作用：守住短线观察报告的前台体验，确保股票名称可点击且每只股票都有算好的观察条件。
安全边界：只读最新短线报告并写本地验收结果；不发送企业微信；不触发n8n；不接券商；不交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def stock_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    root = stock_root()
    data_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    json_path = data_dir / "收盘短线观察_基于300只轻扫描_最新.json"
    md_path = data_dir / "收盘短线观察_基于300只轻扫描_最新.md"
    out_dir = root / "03数据" / "296收盘短线观察前台条件验收"
    now = datetime.now()
    report = read_json(json_path)
    text = read_text(md_path)
    stocks = report.get("股票", []) if isinstance(report.get("股票"), list) else []
    link_count = len(re.findall(r"\[[^\]]+（(?:sz|sh)\d{6}）\]\(http://43\.167\.210\.211/wecom-bot/message\?ask=", text))
    forbidden = ["不设具体触发价", "不生成具体止损价", "等待观察线刷新后再给价位型条件"]
    backend_terms = ["MACD", "RSI", "MA20", "MA60", "DIF", "DEA"]
    stock_checks = []
    for item in stocks:
        trade = item.get("成交观察", {}) if isinstance(item.get("成交观察"), dict) else {}
        levels = item.get("价位", {}) if isinstance(item.get("价位"), dict) else {}
        stock_checks.append(
            check(
                f"{item.get('名称')}具备前台条件",
                bool(item.get("前台状态"))
                and "站稳" in str(item.get("明天短线观察条件", ""))
                and "成交量达到" in str(item.get("明天短线观察条件", ""))
                and "风险线" in str(item.get("短线止损参考价", ""))
                and float(trade.get("放量达标量") or 0) > 0
                and float(levels.get("转强确认位") or 0) > 0
                and float(levels.get("短线放弃线") or 0) > 0,
                {
                    "代码": item.get("代码"),
                    "放量达标量": trade.get("放量达标量"),
                    "转强确认位": levels.get("转强确认位"),
                    "短线放弃线": levels.get("短线放弃线"),
                },
            )
        )
    checks = [
        check("最新JSON存在", json_path.exists(), str(json_path)),
        check("最新Markdown存在", md_path.exists(), str(md_path)),
        check("至少10只短线观察股", len(stocks) >= 10, len(stocks)),
        check("股票名称可点击", link_count >= len(stocks) and link_count > 0, {"链接数": link_count, "股票数": len(stocks)}),
        check("前台不再输出半成品观察线话术", not any(term in text for term in forbidden), forbidden),
        check("前台不堆后台技术指标", not any(term in text for term in backend_terms), backend_terms),
        *stock_checks,
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "收盘短线观察前台条件验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "检查项": checks,
        "失败项": failed,
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = now.strftime("%Y%m%d_%H%M%S")
    write_json(out_dir / f"收盘短线观察前台条件验收_{stamp}.json", result)
    write_json(out_dir / "收盘短线观察前台条件验收_最新.json", result)
    md = [
        "# 收盘短线观察前台条件验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 结论：{result['结论']}",
        f"- 失败项：{len(failed)}",
        "",
        "## 检查项",
        "",
    ]
    for item in checks:
        md.append(f"- {'通过' if item['通过'] else '失败'}：{item['名称']}")
    write_text(out_dir / f"收盘短线观察前台条件验收_{stamp}.md", "\n".join(md) + "\n")
    write_text(out_dir / "收盘短线观察前台条件验收_最新.md", "\n".join(md) + "\n")
    print(json.dumps({"结论": result["结论"], "失败项": len(failed), "输出": str(out_dir / "收盘短线观察前台条件验收_最新.json")}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
