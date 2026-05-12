# -*- coding: utf-8 -*-
"""
名称：验证重点关注池历史K线东方财富增强受控刷新.py
作用：验收233受控刷新是否备份旧快照、刷新后最新快照是否全量东方财富且含正式成交额。
安全边界：只读233执行报告和历史K线最新快照；只写验收报告；不再次刷新、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "233历史K线东方财富增强受控刷新"
EXEC_REPORT = OUT_DIR / "重点关注池历史K线东方财富增强受控刷新执行报告_最新.json"
LATEST_HISTORY = ROOT / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 重点关注池历史K线东方财富增强受控刷新验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    exec_report = load_json(EXEC_REPORT)
    latest = load_json(LATEST_HISTORY)
    rows = latest.get("历史K线", []) or []
    eastmoney = [item for item in rows if "东方财富" in str(item.get("数据源", ""))]
    with_amount = [
        item for item in rows
        if any((row.get("成交额") or 0) for row in item.get("K线", []) or [])
    ]
    backup = Path(exec_report.get("备份文件", ""))
    safety = exec_report.get("安全边界", {})
    expected_count = int((exec_report.get("刷新后统计", {}) or {}).get("股票数量", 0))
    min_records = min([int(item.get("记录数") or 0) for item in rows] or [0])
    short_records = [
        {"代码": item.get("代码"), "名称": item.get("名称"), "记录数": item.get("记录数")}
        for item in rows if int(item.get("记录数") or 0) < 160
    ]
    checks = [
        check(EXEC_REPORT.exists(), "233执行报告存在", str(EXEC_REPORT)),
        check(exec_report.get("结论") == "完成", "执行报告结论完成", str(exec_report.get("结论"))),
        check(backup.exists(), "刷新前备份文件存在", str(backup)),
        check(exec_report.get("刷新前sha256") and exec_report.get("刷新后sha256") and exec_report.get("刷新前sha256") != exec_report.get("刷新后sha256"), "刷新前后sha256发生变化", ""),
        check(expected_count > 0 and len(rows) == expected_count, "最新历史K线股票数量与执行报告一致", f"latest={len(rows)}, report={expected_count}"),
        check(len(eastmoney) == len(rows), "最新历史K线全量来自东方财富", f"{len(eastmoney)}/{len(rows)}"),
        check(len(with_amount) == len(rows), "最新历史K线全量含正式成交额", f"{len(with_amount)}/{len(rows)}"),
        check(min_records > 0, "每只股票至少有历史记录", f"min={min_records}; short={json.dumps(short_records, ensure_ascii=False)}"),
        check(safety.get("已备份刷新前最新快照") is True, "执行前已备份", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "重点关注池历史K线东方财富增强受控刷新验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "再次刷新历史K线": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "重点关注池历史K线东方财富增强受控刷新验收_最新.json"
    latest_md = OUT_DIR / "重点关注池历史K线东方财富增强受控刷新验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
