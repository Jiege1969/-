# -*- coding: utf-8 -*-
"""生成稳定交付版次日复验待执行闸口包。

只登记第 2 个自然日复验的待执行条件和入口，不伪造次日样本。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "83稳定交付版次日复验待执行闸口包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版次日复验待执行闸口包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版次日复验待执行闸口包_最新.md"
GATE_JSON = OUTPUT_DIR / "稳定版次日复验待执行闸口_最新.json"
GATE_MD = OUTPUT_DIR / "稳定版次日复验待执行闸口_最新.md"

DAY1_RESULT = EVOLUTION_ROOT / "03数据" / "82稳定交付版首日复验执行与问题回收包" / "稳定版首日只读复验执行结果_最新.json"
DAY1_VERIFY = EVOLUTION_ROOT / "04日志" / "稳定交付版首日复验执行与问题回收包验收" / "stable-delivery-day1-recheck-issue-intake-verify-最新.json"
DAY2_SCRIPT = EVOLUTION_ROOT / "02脚本" / "执行稳定交付版首日只读复验与问题回收.py"
DAY2_VERIFY_SCRIPT = EVOLUTION_ROOT / "02脚本" / "验证稳定交付版首日复验执行与问题回收包.py"


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


def parse_date(text: str) -> datetime:
    return datetime.strptime(text[:10], "%Y-%m-%d")


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付版次日复验待执行闸口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 首日样本日期：{report['首日样本日期']}",
            f"- 次日最早执行日期：{report['次日最早执行日期']}",
            f"- 当前是否可执行次日复验：{report['当前是否可执行次日复验']}",
            f"- 是否生成次日样本：{report['是否生成次日样本']}",
            "",
            "## 执行入口",
            "",
            f"- 复验执行脚本：{report['次日复验执行入口']['执行脚本']}",
            f"- 复验验收脚本：{report['次日复验执行入口']['验收脚本']}",
            "",
            "## 闸口规则",
            "",
            "- 当前日期早于次日最早执行日期时，只能登记待执行，不能生成次日样本。",
            "- 次日复验仍只允许本地只读复验和问题回收。",
            "- 失败只入台账；红线、服务重载、正式规则变更必须登记需总管确认。",
            "",
        ]
    )


def main() -> int:
    now = datetime.now()
    day1 = read_json(DAY1_RESULT)
    day1_verify = read_json(DAY1_VERIFY)
    day1_time = day1.get("生成时间") or day1_verify.get("生成时间") or now.strftime("%Y-%m-%d %H:%M:%S")
    day1_date = parse_date(day1_time)
    earliest = day1_date + timedelta(days=1)
    can_run = now.date() >= earliest.date()

    gate = {
        "名称": "稳定版次日复验待执行闸口",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "首日样本日期": day1_date.strftime("%Y-%m-%d"),
        "次日最早执行日期": earliest.strftime("%Y-%m-%d"),
        "当前日期": now.strftime("%Y-%m-%d"),
        "当前是否可执行次日复验": can_run,
        "是否生成次日样本": False,
        "待执行原因": "" if can_run else "当前仍处首日自然日，不得伪造次日样本。",
        "次日复验执行入口": {
            "执行脚本": str(DAY2_SCRIPT),
            "验收脚本": str(DAY2_VERIFY_SCRIPT),
        },
        "安全边界": SAFETY_BOUNDARY,
    }
    report = {
        "名称": "稳定交付版次日复验待执行闸口包",
        "生成时间": gate["生成时间"],
        "状态": "stable_delivery_day2_recheck_pending_gate_ready",
        "首日样本日期": gate["首日样本日期"],
        "次日最早执行日期": gate["次日最早执行日期"],
        "当前日期": gate["当前日期"],
        "当前是否可执行次日复验": gate["当前是否可执行次日复验"],
        "是否生成次日样本": False,
        "次日复验执行入口": gate["次日复验执行入口"],
        "指标": {
            "首日复验通过": day1.get("总体状态") == "pass",
            "首日验收通过": day1_verify.get("通过") is True,
            "问题项": len(day1.get("问题项", [])),
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "闸口JSON": str(GATE_JSON),
            "闸口Markdown": str(GATE_MD),
        },
    }
    write_json(GATE_JSON, gate)
    write_text(GATE_MD, build_md(report))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "当前是否可执行次日复验": can_run, "是否生成次日样本": False, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
