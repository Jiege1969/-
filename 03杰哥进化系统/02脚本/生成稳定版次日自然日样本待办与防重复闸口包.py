# -*- coding: utf-8 -*-
"""生成稳定版次日自然日样本待办与防重复闸口包。

只读取三日样本台账和达标判定结果，生成次日待办卡与防重复闸口；不预生成未来样本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "99稳定版次日自然日样本待办与防重复闸口包"

LATEST_JSON = OUTPUT_DIR / "稳定版次日自然日样本待办与防重复闸口包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版次日自然日样本待办与防重复闸口包_最新.md"
TODO_MD = OUTPUT_DIR / "次日自然日样本待办卡_最新.md"
GATE_JSON = OUTPUT_DIR / "自然日样本防重复闸口_最新.json"

DECISION_JSON = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"
LEDGER_JSON = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
SINGLE_ENTRY_CARD = EVOLUTION_ROOT / "03数据" / "98稳定版每日唯一入口操作卡同步包" / "稳定版每日唯一入口操作卡_最新.md"
SINGLE_ENTRY_SCRIPT = EVOLUTION_ROOT / "02脚本" / "执行稳定版自然日样本采集与达标刷新.py"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "预生成未来自然日样本": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sample_date(sample: dict[str, Any]) -> str:
    return str(sample.get("样本日期") or sample.get("鏍锋湰鏃ユ湡") or "")[:10]


def sample_status(sample: dict[str, Any]) -> str:
    return str(sample.get("当日状态") or sample.get("褰撴棩鐘舵€?") or "")


def decision_value(decision: dict[str, Any], chinese_key: str, mojibake_key: str, default: Any = None) -> Any:
    return decision.get(chinese_key, decision.get(mojibake_key, default))


def build_todo_card(report: dict[str, Any]) -> str:
    gate = report["防重复闸口"]
    return "\n".join(
        [
            "# 次日自然日样本待办卡",
            "",
            f"- 当前日期：{gate['当前日期']}",
            f"- 下一最早采集日期：{gate['下一最早采集日期']}",
            f"- 今天是否允许新增自然日样本：{gate['今天是否允许新增自然日样本']}",
            f"- 三日达标：{report['三日达标']}",
            f"- 仍缺自然日样本数：{report['仍缺自然日样本数']}",
            "",
            "## 到点后只跑这个",
            "",
            "```powershell",
            f'python "{SINGLE_ENTRY_SCRIPT}"',
            "```",
            "",
            "## 防重复说明",
            "",
            "- 同一自然日重复运行只覆盖当天样本。",
            "- 不允许为了凑三日达标生成未来日期样本。",
            "- 三日达标必须来自三个不同真实自然日的通过样本。",
            "",
        ]
    )


def build_md(report: dict[str, Any]) -> str:
    gate = report["防重复闸口"]
    return "\n".join(
        [
            "# 稳定版次日自然日样本待办与防重复闸口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 已有通过自然日样本数：{report['已有通过自然日样本数']}",
            f"- 仍缺自然日样本数：{report['仍缺自然日样本数']}",
            f"- 三日达标：{report['三日达标']}",
            f"- 今天是否允许新增自然日样本：{gate['今天是否允许新增自然日样本']}",
            f"- 下一最早采集日期：{gate['下一最早采集日期']}",
            "",
            "## 输出文件",
            "",
            *[f"- {key}：{value}" for key, value in report["输出文件"].items()],
            "",
        ]
    )


def main() -> int:
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    decision = read_json(DECISION_JSON)
    ledger = read_json(LEDGER_JSON)
    samples = ledger.get("自然日样本") or ledger.get("鑷劧鏃ユ牱鏈?") or []
    all_dates = [sample_date(item) for item in samples if sample_date(item)]
    pass_dates = sorted({sample_date(item) for item in samples if sample_date(item) and sample_status(item) == "pass"})
    duplicate_dates = sorted({date for date in all_dates if all_dates.count(date) > 1})
    next_date = decision_value(decision, "下一自然日最早采集日期", "涓嬩竴鑷劧鏃ユ渶鏃╅噰闆嗘棩鏈?", "")
    if not next_date and pass_dates:
        next_date = pass_dates[-1]
    three_day_passed = bool(decision_value(decision, "三日达标", "涓夋棩杈炬爣", False))
    missing = int(decision_value(decision, "仍缺自然日样本数", "浠嶇己鑷劧鏃ユ牱鏈暟", max(0, 3 - len(pass_dates))) or 0)
    today_already_recorded = today in all_dates
    allow_today = bool(next_date and today >= next_date and not today_already_recorded and not three_day_passed)
    gate = {
        "当前日期": today,
        "下一最早采集日期": next_date,
        "今天是否已有样本": today_already_recorded,
        "今天是否允许新增自然日样本": allow_today,
        "重复样本日期": duplicate_dates,
        "通过样本日期": pass_dates,
        "是否生成未来样本": False,
        "推荐每日入口": str(SINGLE_ENTRY_SCRIPT),
    }
    report = {
        "名称": "稳定版次日自然日样本待办与防重复闸口包",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_nextday_natural_sample_todo_duplicate_gate_ready",
        "已有通过自然日样本数": len(pass_dates),
        "仍缺自然日样本数": missing,
        "三日达标": three_day_passed,
        "防重复闸口": gate,
        "来源文件": {
            "三日达标判定结果": str(DECISION_JSON),
            "三日样本台账": str(LEDGER_JSON),
            "每日唯一入口操作卡": str(SINGLE_ENTRY_CARD),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "次日自然日样本待办卡": str(TODO_MD),
            "自然日样本防重复闸口": str(GATE_JSON),
        },
    }
    write_json(GATE_JSON, gate)
    write_json(LATEST_JSON, report)
    write_text(TODO_MD, build_todo_card(report))
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "今天是否允许新增自然日样本": allow_today, "仍缺自然日样本数": missing, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
