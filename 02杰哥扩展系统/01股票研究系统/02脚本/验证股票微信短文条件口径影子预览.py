# -*- coding: utf-8 -*-
"""
名称：验证股票微信短文条件口径影子预览.py
作用：验收微信短文影子预览是否短小、清晰、有具体价格和成交额、保留详情入口、明确非交易边界。
安全边界：只读影子预览；只写验收报告；不改正式入口，不重启服务，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "221微信短文条件口径影子预览"
PREVIEW_JSON = OUT_DIR / "股票微信短文条件口径影子预览_最新.json"
PREVIEW_MD = OUT_DIR / "股票微信短文条件口径影子预览_最新.md"


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
        "# 股票微信短文条件口径影子预览验收",
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
    preview = load_json(PREVIEW_JSON)
    md = read_text(PREVIEW_MD)
    short = preview.get("微信短文", "")
    safety = preview.get("安全边界", {})
    checks_map = preview.get("禁用表达检查", {})
    fields = [item.get("字段", "") for item in preview.get("字段来源", [])]
    formal_amount = "东方财富历史K线正式成交额口径" in short
    text = json.dumps(preview, ensure_ascii=False) + "\n" + md

    checks = [
        check(PREVIEW_JSON.exists() and PREVIEW_MD.exists(), "预览 JSON 和 Markdown 存在", str(OUT_DIR)),
        check("【新易盛】可观察，暂不提高优先级。" in short, "一句话结论明确且不夸大", ""),
        check(260 <= len(short) <= 650, "短文长度适合微信端", f"长度={len(short)}"),
        check("当前价525.79元" in short and "536.01元-541.37元" in short, "逻辑段包含当前价和承接区", ""),
        check("未来3个有效交易日内，至少2天收盘不低于536.01元" in short, "观察条件有天数和价格", ""),
        check(
            ("301.02亿元" in short and "250.85亿元" in short) or ("275.80亿元" in short and "229.83亿元" in short),
            "观察和转强条件包含成交额金额",
            "",
        ),
        check("连续2天收盘高于567.85元" in short, "转强条件有连续天数和价格", ""),
        check("收盘低于448.60元" in short and "2个有效交易日内未收回" in short, "失败条件有风险线和修复窗口", ""),
        check(
            formal_amount or "估算口径，待正式成交额源回补" in short,
            "成交额口径已披露",
            "",
        ),
        check("详情：" in short and "单股标准报告v2_最新.md" in short, "保留详情入口", ""),
        check("研究分析短文，不自动交易" in short, "非交易声明存在", ""),
        check(all(checks_map.values()), "禁用表达检查全部通过", json.dumps(checks_map, ensure_ascii=False)),
        check({"一句话结论", "逻辑", "观察条件", "转强条件", "失败条件", "风险", "详情"}.issubset(set(fields)), "字段来源覆盖 6+1", ",".join(fields)),
        check(all(value is False for key, value in safety.items() if key != "本步骤仅生成微信短文影子预览"), "高风险安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("本步骤仅生成微信短文影子预览") is True, "明确本步骤仅生成影子预览", json.dumps(safety, ensure_ascii=False)),
        check("不替换正式企业微信入口" in text or "正式入口替换仍需停下报告" in text, "明确不替换正式入口", ""),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票微信短文条件口径影子预览验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "股票微信短文条件口径影子预览验收_最新.json"
    latest_md = OUT_DIR / "股票微信短文条件口径影子预览验收_最新.md"
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
