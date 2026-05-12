# -*- coding: utf-8 -*-
"""
名称：验证环境自适应三级漏斗推荐引擎.py
作用：验收影子三级漏斗推荐引擎是否满足市场->行业->个股->风险上限的结构要求。
安全边界：只读本地文件；只写本地03数据验收产物；不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"

RULE_PATH = CONFIG / "环境自适应三级漏斗推荐引擎_v1.0.json"
REPORT_PATH = DATA / "283环境自适应三级漏斗推荐引擎" / "环境自适应三级漏斗推荐引擎_最新.json"
OUT_DIR = DATA / "284环境自适应三级漏斗推荐引擎验收"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    errors: list[str] = []
    warnings: list[str] = []

    rule = read_json(RULE_PATH, {})
    report = read_json(REPORT_PATH, {})

    if not rule:
        errors.append(f"缺少规则文件: {RULE_PATH}")
    if not report:
        errors.append(f"缺少引擎产物: {REPORT_PATH}")

    required_sections = [
        "市场环境",
        "判断线权重",
        "优先行业",
        "重点关注个股",
        "观察验证个股",
        "暂缓行业",
        "前台影子摘要",
        "安全边界",
    ]
    for section in required_sections:
        if section not in report:
            errors.append(f"引擎产物缺少章节: {section}")

    weights = report.get("判断线权重", {})
    for key in ["市场环境", "行业强弱", "行业内个股", "趋势阶段", "量价承接", "风险刹车"]:
        if key not in weights:
            errors.append(f"判断线权重缺少: {key}")
    weight_sum = sum(float(v or 0) for v in weights.values()) if isinstance(weights, dict) else 0
    if weights and not (0.98 <= weight_sum <= 1.02):
        errors.append(f"判断线权重合计异常: {weight_sum}")

    priority_industries = report.get("优先行业", [])
    focus_stocks = report.get("重点关注个股", [])
    watch_stocks = report.get("观察验证个股", [])
    wait_focus = report.get("重点待验证个股", [])
    if not priority_industries:
        errors.append("优先行业为空，三级漏斗没有行业方向。")
    if not focus_stocks and not wait_focus and not watch_stocks:
        errors.append("重点/待验证/观察个股均为空，三级漏斗没有个股输出。")

    priority_set = {item.get("行业") for item in priority_industries}
    focus_outside = [
        item for item in focus_stocks
        if item.get("行业") not in priority_set and item.get("个股类型") != "行业弱但个股独立强"
    ]
    if focus_outside:
        warnings.append(f"存在重点个股不在优先行业中: {len(focus_outside)}只，需复核是否为独立强势。")

    illegal_focus = [
        item for item in focus_stocks
        if item.get("结论上限") not in ("重点关注", "重点待验证") or item.get("刹车项数量", 0) > 0
    ]
    if illegal_focus:
        errors.append(f"存在重点个股违反结论上限或刹车规则: {len(illegal_focus)}只")

    front = report.get("前台影子摘要", {})
    if not front.get("优先行业") or not front.get("风险边界"):
        errors.append("前台影子摘要缺少优先行业或风险边界。")

    safety = report.get("安全边界", {})
    for key in ["真实发送企业微信", "触发n8n", "调用券商接口", "自动交易", "输出交易指令", "替换正式前台"]:
        if safety.get(key) is not False:
            errors.append(f"安全边界异常: {key} 必须为 false")

    report_out = {
        "名称": "环境自适应三级漏斗推荐引擎验收",
        "生成时间": now,
        "结论": "通过" if not errors else "不通过",
        "错误": errors,
        "警告": warnings,
        "检查摘要": {
            "市场状态": report.get("市场环境", {}).get("市场状态"),
            "主状态": report.get("市场环境", {}).get("主状态"),
            "判断线权重合计": round(weight_sum, 4),
            "优先行业数量": len(priority_industries),
            "重点关注个股数量": len(focus_stocks),
            "重点待验证个股数量": len(wait_focus),
            "观察验证个股数量": len(watch_stocks),
            "暂缓行业数量": len(report.get("暂缓行业", [])),
        },
        "安全边界": safety,
        "输入": {
            "规则": str(RULE_PATH),
            "引擎产物": str(REPORT_PATH),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = OUT_DIR / "环境自适应三级漏斗推荐引擎验收_最新.json"
    latest_md = OUT_DIR / "环境自适应三级漏斗推荐引擎验收_最新.md"
    write_json(OUT_DIR / f"环境自适应三级漏斗推荐引擎验收_{timestamp}.json", report_out)
    write_json(latest_json, report_out)

    lines = [
        "# 环境自适应三级漏斗推荐引擎验收",
        "",
        f"生成时间：{now}",
        f"结论：{report_out['结论']}",
        "",
        "## 摘要",
        "",
    ]
    for key, value in report_out["检查摘要"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## 错误", ""])
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in warnings] or ["- 无"])
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({"结论": report_out["结论"], "错误数": len(errors), "警告数": len(warnings), "输出": str(latest_json)}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
