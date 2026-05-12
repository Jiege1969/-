# -*- coding: utf-8 -*-
"""
名称：验证历史K线东方财富增强影子快照.py
作用：验收227东方财富增强影子快照是否全量含正式成交额，且未覆盖正式历史K线快照。
安全边界：只读227影子快照；只写验收报告；不覆盖历史K线最新快照、不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "227历史K线东方财富增强影子快照"
REPORT_JSON = OUT_DIR / "历史K线东方财富增强影子快照_最新.json"
REPORT_MD = OUT_DIR / "历史K线东方财富增强影子快照_最新.md"
FORMAL_HISTORY = ROOT / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json"


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
        "# 历史K线东方财富增强影子快照验收",
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
    summary = data.get("汇总", {})
    rows = data.get("历史K线", []) or []
    safety = data.get("安全边界", {})
    formal = load_json(FORMAL_HISTORY)
    current_sources = {item.get("数据源", "") for item in formal.get("历史K线", []) or []}
    sample = next((item for item in rows if item.get("名称") == "新易盛"), {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "227影子快照 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "历史K线东方财富增强影子快照", "报告名称正确", str(data.get("名称"))),
        check(summary.get("股票数量", 0) >= 1 and len(rows) == summary.get("股票数量"), "股票数量与明细一致", json.dumps(summary, ensure_ascii=False)),
        check(summary.get("成功数量") == summary.get("股票数量"), "东方财富增强影子快照全量成功", json.dumps(summary, ensure_ascii=False)),
        check(summary.get("含正式成交额数量") == summary.get("股票数量"), "全量股票含正式成交额", json.dumps(summary, ensure_ascii=False)),
        check(all((item.get("记录数") or 0) >= 100 for item in rows), "每只股票记录数满足历史窗口", "min=" + str(min([item.get("记录数") or 0 for item in rows] or [0]))),
        check(sample.get("状态") == "成功" and sample.get("含正式成交额") is True, "新易盛样本成功含正式成交额", json.dumps(sample, ensure_ascii=False)[:500]),
        check(summary.get("是否可进入220正式口径影子重算") is True, "可进入220正式口径影子重算", json.dumps(summary, ensure_ascii=False)),
        check("腾讯历史K线" in current_sources, "正式历史K线最新快照仍未被覆盖", json.dumps(sorted(current_sources), ensure_ascii=False)),
        check(safety.get("联网只读公开接口") is True, "本轮仅联网只读公开接口", json.dumps(safety, ensure_ascii=False)),
        check(all(value is False for key, value in safety.items() if key != "联网只读公开接口"), "除联网只读外安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("覆盖历史K线最新快照") is False and safety.get("修改历史K线生成脚本") is False, "未覆盖快照且未改脚本", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "历史K线东方财富增强影子快照验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "联网只读公开接口": True,
            "覆盖历史K线最新快照": False,
            "修改历史K线生成脚本": False,
            "修改220口径": False,
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
    latest_json = OUT_DIR / "历史K线东方财富增强影子快照验收_最新.json"
    latest_md = OUT_DIR / "历史K线东方财富增强影子快照验收_最新.md"
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
