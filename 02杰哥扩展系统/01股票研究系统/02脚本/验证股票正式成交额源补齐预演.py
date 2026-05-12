# -*- coding: utf-8 -*-
"""
名称：验证股票正式成交额源补齐预演.py
作用：验收223正式成交额源补齐预演是否准确标明当前正式源、历史缺口、回补路径和安全边界。
安全边界：只读223预演报告；只写验收报告；不联网、不修改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "223正式成交额源补齐预演"
REPORT_JSON = OUT_DIR / "股票正式成交额源补齐预演_最新.json"
REPORT_MD = OUT_DIR / "股票正式成交额源补齐预演_最新.md"


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
        "# 股票正式成交额源补齐预演验收",
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
    source_status = data.get("正式成交额源状态", {})
    current = data.get("当前行情成交额", {})
    history = data.get("样本历史K线摘要", {})
    recent = data.get("近5日成交额对照", []) or []
    safety = data.get("安全边界", {})
    global_stats = data.get("全局历史K线源统计", {})
    can_replace = [item for item in recent if item.get("当前可替换估算") is True]
    claimed_formal_history = source_status.get("历史成交额") == "历史成交额正式可用"
    harmful_words = ["买入", "卖出", "下单", "调仓", "收益承诺"]
    harmful_hits = {word: word in text for word in harmful_words}

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "223预演 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "股票正式成交额源补齐预演", "报告名称正确", str(data.get("名称"))),
        check(data.get("样本股票", {}).get("名称") == "新易盛", "样本股票承接220/221新易盛", json.dumps(data.get("样本股票", {}), ensure_ascii=False)),
        check(source_status.get("当前成交额") == "当前成交额正式可用", "当前成交额已标明正式可用", json.dumps(source_status, ensure_ascii=False)),
        check(current.get("数据源") == "东方财富公开行情接口" and current.get("是否正式可用") is True, "当前成交额来自东方财富公开行情快照", json.dumps(current, ensure_ascii=False)),
        check(current.get("成交额显示") == "159.97亿元", "当前成交额数值与220一致", str(current.get("成交额显示"))),
        check(source_status.get("历史成交额") in ("历史成交额正式可用", "历史成交额仍需回补"), "历史成交额状态枚举明确", str(source_status.get("历史成交额"))),
        check(not claimed_formal_history or len(can_replace) >= 5, "未在近5日正式成交额不足时宣称可用", f"可替换={len(can_replace)}/5"),
        check(claimed_formal_history or "仍需回补" in text, "历史成交额缺失时保留回补提示", ""),
        check("生成重点关注池历史K线快照.py" in text and "parts[6]" in text, "回补路径指向东方财富历史K线成交额字段", ""),
        check("估算降级" in text and "不能解除" in text or source_status.get("是否解除估算降级") is True, "估算降级处理明确", ""),
        check(len(recent) == 5, "近5日成交额对照完整", f"数量={len(recent)}"),
        check(global_stats.get("股票数", 0) >= 1, "全局历史K线源统计存在", json.dumps(global_stats, ensure_ascii=False)),
        check("腾讯" in str(history.get("数据源", "")) or "东方财富" in str(history.get("数据源", "")), "样本历史K线来源明确", str(history.get("数据源", ""))),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("联网刷新行情") is False, "未联网刷新行情", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
        check(not any(harmful_hits.values()), "未输出交易动作或收益承诺词", json.dumps(harmful_hits, ensure_ascii=False)),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票正式成交额源补齐预演验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "联网刷新行情": False,
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
    latest_json = OUT_DIR / "股票正式成交额源补齐预演验收_最新.json"
    latest_md = OUT_DIR / "股票正式成交额源补齐预演验收_最新.md"
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
