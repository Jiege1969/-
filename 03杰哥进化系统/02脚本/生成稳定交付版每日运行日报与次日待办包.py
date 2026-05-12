# -*- coding: utf-8 -*-
"""生成稳定交付版每日运行日报与次日待办包。

只读取稳定版运行观察、总巡检、总回归、三日判定和问题台账；
不触发外部系统，不生成未来样本，不修改正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版每日运行日报与次日待办包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版每日运行日报与次日待办包_最新.md"
DAILY_REPORT_JSON = OUTPUT_DIR / "稳定版每日运行日报_最新.json"
DAILY_REPORT_MD = OUTPUT_DIR / "稳定版每日运行日报_最新.md"
NEXT_TODO_JSON = OUTPUT_DIR / "稳定版次日待办清单_最新.json"
NEXT_TODO_MD = OUTPUT_DIR / "稳定版次日待办清单_最新.md"

SNAPSHOT = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_VERIFY = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"
DAY1_RECHECK = EVOLUTION_ROOT / "03数据" / "82稳定交付版首日复验执行与问题回收包" / "稳定版首日只读复验执行结果_最新.json"
DAY2_GATE = EVOLUTION_ROOT / "03数据" / "83稳定交付版次日复验待执行闸口包" / "稳定交付版次日复验待执行闸口包_最新.json"
THREE_DAY_DECISION = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"
ISSUE_LEDGER = EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json"


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


def build_daily_report(now: datetime) -> dict[str, Any]:
    snapshot = read_json(SNAPSHOT)
    regression = read_json(REGRESSION_VERIFY)
    day1 = read_json(DAY1_RECHECK)
    day2 = read_json(DAY2_GATE)
    three_day = read_json(THREE_DAY_DECISION)
    issue_ledger = read_json(ISSUE_LEDGER)
    snapshot_ok = snapshot.get("总体状态") == "pass"
    regression_ok = regression.get("通过") is True
    day1_ok = day1.get("总体状态") == "pass"
    issue_sources = issue_ledger.get("来源索引", issue_ledger.get("来源", []))
    issue_blocked = 0
    if isinstance(issue_sources, list):
        issue_blocked = sum(1 for item in issue_sources if item.get("状态") in {"blocked", "fail", False})

    stable_today = snapshot_ok and regression_ok and day1_ok and issue_blocked == 0
    return {
        "名称": "稳定版每日运行日报",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "日报日期": now.strftime("%Y-%m-%d"),
        "今日结论": "今日稳定版只读复验通过，可继续运行观察" if stable_today else "今日存在需登记复核项",
        "总巡检": {
            "状态": snapshot.get("总体状态"),
            "通过": snapshot.get("汇总", {}).get("通过"),
            "总数": snapshot.get("汇总", {}).get("总数"),
            "失败": snapshot.get("汇总", {}).get("失败"),
        },
        "一键只读总回归": {
            "通过": regression.get("通过"),
            "总数": regression.get("指标", {}).get("总数"),
            "失败": regression.get("指标", {}).get("失败"),
            "错误数": regression.get("指标", {}).get("错误数"),
        },
        "首日复验": {
            "状态": day1.get("总体状态"),
            "通过": day1.get("汇总", {}).get("通过"),
            "失败": day1.get("汇总", {}).get("失败"),
            "问题数": len(day1.get("问题项", [])),
        },
        "三日稳定样本": {
            "三日达标": three_day.get("三日达标"),
            "通过样本数": three_day.get("不同自然日通过样本数"),
            "仍缺样本数": three_day.get("仍缺自然日样本数"),
            "下一自然日最早采集日期": three_day.get("下一自然日最早采集日期"),
        },
        "次日闸口": {
            "当前是否可执行次日复验": day2.get("当前是否可执行次日复验"),
            "次日最早执行日期": day2.get("次日最早执行日期"),
            "是否生成次日样本": day2.get("是否生成次日样本"),
        },
        "问题总台账": {
            "索引状态": issue_ledger.get("状态"),
            "异常来源数": issue_blocked,
        },
        "稳定版运行状态": "green" if stable_today else "yellow",
        "安全边界": SAFETY_BOUNDARY,
    }


def build_next_todo(report: dict[str, Any]) -> dict[str, Any]:
    todos = [
        {
            "编号": "NEXT-001",
            "事项": "到达真实次日后执行稳定版首日只读复验脚本作为第2自然日复验入口",
            "最早日期": report["三日稳定样本"].get("下一自然日最早采集日期"),
            "当前状态": "waiting-natural-day",
            "红线": False,
        },
        {
            "编号": "NEXT-002",
            "事项": "复跑日常可用交付版一键只读总回归",
            "最早日期": report["日报日期"],
            "当前状态": "ready",
            "红线": False,
        },
        {
            "编号": "NEXT-003",
            "事项": "复跑日常可用版自主巡检快照",
            "最早日期": report["日报日期"],
            "当前状态": "ready",
            "红线": False,
        },
        {
            "编号": "NEXT-004",
            "事项": "若出现失败项，登记运行期问题闭环总台账，不自动写正式规则",
            "最早日期": report["日报日期"],
            "当前状态": "ready-on-failure",
            "红线": False,
        },
    ]
    return {
        "名称": "稳定版次日待办清单",
        "生成时间": report["生成时间"],
        "待办": todos,
        "安全边界": SAFETY_BOUNDARY,
    }


def build_daily_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版每日运行日报",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 日报日期：{report['日报日期']}",
            f"- 今日结论：{report['今日结论']}",
            f"- 运行状态：{report['稳定版运行状态']}",
            f"- 总巡检：{report['总巡检']['通过']} / {report['总巡检']['总数']}，失败 {report['总巡检']['失败']}",
            f"- 一键只读总回归：失败 {report['一键只读总回归']['失败']}，错误 {report['一键只读总回归']['错误数']}",
            f"- 首日复验：失败 {report['首日复验']['失败']}，问题 {report['首日复验']['问题数']}",
            f"- 三日稳定样本：{report['三日稳定样本']['通过样本数']} 个，仍缺 {report['三日稳定样本']['仍缺样本数']} 个，达标={report['三日稳定样本']['三日达标']}",
            "",
        ]
    )


def build_todo_md(todo: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['事项']} | {item['最早日期']} | {item['当前状态']} |"
        for item in todo["待办"]
    ]
    return "\n".join(
        [
            "# 稳定版次日待办清单",
            "",
            f"- 生成时间：{todo['生成时间']}",
            "",
            "| 编号 | 事项 | 最早日期 | 当前状态 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_summary_md(report: dict[str, Any], todo: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付版每日运行日报与次日待办包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 今日结论：{report['今日结论']}",
            f"- 稳定版运行状态：{report['稳定版运行状态']}",
            f"- 三日达标：{report['三日稳定样本']['三日达标']}",
            f"- 仍缺自然日样本：{report['三日稳定样本']['仍缺样本数']}",
            f"- 次日待办数：{len(todo['待办'])}",
            "",
            "## 边界",
            "",
            "- 只读汇总，不触发外部系统。",
            "- 不生成未来自然日样本。",
            "- 不写正式规则，不重载 19310/19302。",
            "",
        ]
    )


def main() -> int:
    now = datetime.now()
    report = build_daily_report(now)
    todo = build_next_todo(report)
    package = {
        "名称": "稳定交付版每日运行日报与次日待办包",
        "生成时间": report["生成时间"],
        "状态": "stable_delivery_daily_report_next_todo_ready",
        "每日运行日报": str(DAILY_REPORT_JSON),
        "次日待办清单": str(NEXT_TODO_JSON),
        "指标": {
            "运行状态": report["稳定版运行状态"],
            "总巡检失败": report["总巡检"]["失败"],
            "总回归失败": report["一键只读总回归"]["失败"],
            "首日问题数": report["首日复验"]["问题数"],
            "三日达标": report["三日稳定样本"]["三日达标"],
            "仍缺自然日样本": report["三日稳定样本"]["仍缺样本数"],
            "次日待办数": len(todo["待办"]),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "每日运行日报JSON": str(DAILY_REPORT_JSON),
            "每日运行日报Markdown": str(DAILY_REPORT_MD),
            "次日待办清单JSON": str(NEXT_TODO_JSON),
            "次日待办清单Markdown": str(NEXT_TODO_MD),
        },
    }
    write_json(DAILY_REPORT_JSON, report)
    write_text(DAILY_REPORT_MD, build_daily_md(report))
    write_json(NEXT_TODO_JSON, todo)
    write_text(NEXT_TODO_MD, build_todo_md(todo))
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_summary_md(report, todo))
    print(json.dumps({"状态": package["状态"], "运行状态": report["稳定版运行状态"], "次日待办数": len(todo["待办"]), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
