# -*- coding: utf-8 -*-
"""
名称：验证股票价位成交额正式口径影子重算.py
作用：验收228正式成交额口径影子重算是否完整、安全、未覆盖220原文件。
安全边界：只读228重算报告；只写验收报告；不覆盖220、不改221/222、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "228价位成交额正式口径影子重算"
REPORT_JSON = OUT_DIR / "股票价位成交额正式口径影子重算_最新.json"
REPORT_MD = OUT_DIR / "股票价位成交额正式口径影子重算_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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
        "# 股票价位成交额正式口径影子重算验收",
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
    data = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    text = json.dumps(data, ensure_ascii=False) + "\n" + md
    threshold = data.get("阈值对照", {})
    rows = data.get("近5日正式成交额明细", []) or []
    safety = data.get("安全边界", {})
    formal_rows = [item for item in rows if item.get("口径") == "东方财富历史K线正式成交额"]
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "228重算 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "股票价位成交额正式口径影子重算", "报告名称正确", str(data.get("名称"))),
        check(data.get("样本股票", {}).get("名称") == "新易盛", "样本股票为新易盛", json.dumps(data.get("样本股票", {}), ensure_ascii=False)),
        check(threshold.get("正式近5日均额") == "250.85亿元", "正式近5日均额正确", json.dumps(threshold, ensure_ascii=False)),
        check(threshold.get("正式近5日均额1.2倍") == "301.02亿元", "正式1.2倍阈值正确", json.dumps(threshold, ensure_ascii=False)),
        check(threshold.get("是否可解除估算降级") is True, "估算降级可进入影子解除", json.dumps(threshold, ensure_ascii=False)),
        check(len(rows) == 5 and len(formal_rows) == 5, "近5日正式成交额明细完整", f"{len(formal_rows)}/{len(rows)}"),
        check("东方财富历史K线正式成交额" in text, "正式成交额口径写入影子版", ""),
        check("按成交量×收盘价×100估算 -> 东方财富历史K线正式成交额" in text, "口径变化清晰", ""),
        check("估算口径，待正式成交额源回补" not in json.dumps(data.get("条件口径正式影子版", []), ensure_ascii=False), "条件口径影子版已移除估算降级短语", ""),
        check("若历史成交额来自估算" not in json.dumps(data.get("条件口径正式影子版", []), ensure_ascii=False), "条件口径影子版已移除估算前提", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("覆盖220原文件") is False and safety.get("覆盖历史K线最新快照") is False, "未覆盖220和历史K线最新快照", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票价位成交额正式口径影子重算验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "联网请求": False,
            "覆盖220原文件": False,
            "覆盖历史K线最新快照": False,
            "修改221短文": False,
            "修改222影子分支": False,
            "修改正式短回复生成器": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "股票价位成交额正式口径影子重算验收_最新.json"
    latest_md = OUT_DIR / "股票价位成交额正式口径影子重算验收_最新.md"
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
