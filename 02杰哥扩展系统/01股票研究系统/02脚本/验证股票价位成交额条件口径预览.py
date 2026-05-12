# -*- coding: utf-8 -*-
"""
名称：验证股票价位成交额条件口径预览.py
作用：验收股票价位、成交额阈值、N日M日条件、降级规则和非交易边界是否完整。
安全边界：只读口径预览；只写验收报告；不改正式入口，不重启服务，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "220价位成交额条件口径"
PREVIEW_JSON = OUT_DIR / "股票价位成交额条件口径预览_最新.json"
PREVIEW_MD = OUT_DIR / "股票价位成交额条件口径预览_最新.md"


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
        "# 股票价位成交额条件口径预览验收",
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
    text = json.dumps(preview, ensure_ascii=False) + "\n" + md
    stock = preview.get("样本股票", {})
    base = preview.get("基准数据", {})
    conditions = preview.get("条件口径", [])
    wechat_lines = preview.get("微信短文可用表达", [])
    safety = preview.get("安全边界", {})
    forbidden = preview.get("禁用表达", [])
    has_formal_amount = "东方财富历史K线正式成交额" in str(base.get("近5日成交额口径", "")) or "东方财富历史K线正式成交额" in text

    condition_names = [item.get("条件名称", "") for item in conditions]
    condition_text = "\n".join(item.get("可执行表述", "") for item in conditions)

    checks = [
        check(PREVIEW_JSON.exists() and PREVIEW_MD.exists(), "预览 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(stock.get("代码") == "300502" and "新易盛" in stock.get("名称", ""), "样本股票识别正确", json.dumps(stock, ensure_ascii=False)),
        check("536.01元-541.37元" in str(base.get("承接区", "")), "承接区展开为具体价格", str(base.get("承接区", ""))),
        check(str(base.get("转强线", "")).startswith("567.85"), "转强线展开为具体价格", str(base.get("转强线", ""))),
        check(str(base.get("风险线", "")).startswith("448.60"), "风险线展开为具体价格", str(base.get("风险线", ""))),
        check("亿元" in str(base.get("截至昨日近5日均额", "")) and "亿元" in str(base.get("截至昨日近5日均额1.2倍", "")), "近5日均额和1.2倍阈值有明确金额", json.dumps(base, ensure_ascii=False)),
        check(("估算" in str(base.get("阈值可信度", ""))) or has_formal_amount, "成交额阈值可信度按估算或正式口径明确", str(base.get("阈值可信度", ""))),
        check({"观察条件", "转强条件", "失败条件", "成交额可信度条件"}.issubset(set(condition_names)), "四类条件齐全", ",".join(condition_names)),
        check("未来3个有效交易日内，至少2个交易日" in condition_text, "观察条件采用N日M日格式", ""),
        check("连续2个有效交易日" in condition_text and "至少1日成交额" in condition_text, "转强条件包含连续天数和成交额阈值", ""),
        check(not has_formal_amount or "待正式成交额源回补" not in condition_text, "正式成交额口径下不再要求待回补", ""),
        check("后续2个有效交易日内仍未重新收回" in condition_text and "5个有效交易日内" in condition_text, "失败条件包含修复窗口和降级窗口", ""),
        check(len(wechat_lines) >= 4 and all("元" in line or "亿元" in line for line in wechat_lines), "微信短文表达包含具体价格或金额", "\n".join(wechat_lines)),
        check(all(word in forbidden for word in ["稳住", "有承接", "放量", "转强", "继续观察"]), "禁用模糊表达清单完整", ",".join(forbidden)),
        check(all(value is False for key, value in safety.items() if key != "本步骤仅生成口径预览"), "高风险安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("本步骤仅生成口径预览") is True, "明确本步骤仅生成口径预览", json.dumps(safety, ensure_ascii=False)),
        check("不改正式入口" in text or "正式接入前" in text, "明确正式入口仍不替换", ""),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票价位成交额条件口径预览验收",
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

    latest_json = OUT_DIR / "股票价位成交额条件口径预览验收_最新.json"
    latest_md = OUT_DIR / "股票价位成交额条件口径预览验收_最新.md"
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
