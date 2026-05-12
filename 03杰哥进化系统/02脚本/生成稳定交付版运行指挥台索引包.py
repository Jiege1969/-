# -*- coding: utf-8 -*-
"""生成稳定交付版运行指挥台索引包。

把稳定版每日运行入口、日报、三日判定、问题台账和红线状态集中成只读索引。
不修改总管面板或一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版运行指挥台索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版运行指挥台索引包_最新.md"
DASHBOARD_JSON = OUTPUT_DIR / "稳定版运行指挥台_最新.json"
DASHBOARD_MD = OUTPUT_DIR / "稳定版运行指挥台_最新.md"


SOURCES = {
    "每日一键只读刷新结果": EVOLUTION_ROOT / "03数据" / "86稳定交付版每日一键只读刷新与日报汇总包" / "稳定版每日一键只读刷新结果_最新.json",
    "每日运行日报": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定版每日运行日报_最新.json",
    "次日待办清单": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定版次日待办清单_最新.json",
    "三日达标判定": EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json",
    "次日复验闸口": EVOLUTION_ROOT / "03数据" / "83稳定交付版次日复验待执行闸口包" / "稳定交付版次日复验待执行闸口包_最新.json",
    "问题闭环总台账索引": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
    "试运行反馈本地入账结果": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账结果_最新.json",
    "试运行反馈候选台账": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈候选台账_最新.json",
    "自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归验收": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
}


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


def source_status() -> list[dict[str, Any]]:
    rows = []
    for name, path in SOURCES.items():
        data = read_json(path)
        status = (
            data.get("总体状态")
            or data.get("状态")
            or data.get("通过")
            or data.get("稳定版运行状态")
            or data.get("三日达标")
        )
        rows.append({"名称": name, "路径": str(path), "存在": path.exists(), "状态": status})
    return rows


def build_dashboard(now: datetime) -> dict[str, Any]:
    refresh = read_json(SOURCES["每日一键只读刷新结果"])
    daily = read_json(SOURCES["每日运行日报"])
    three_day = read_json(SOURCES["三日达标判定"])
    day2 = read_json(SOURCES["次日复验闸口"])
    snapshot = read_json(SOURCES["自主巡检快照"])
    regression = read_json(SOURCES["一键只读总回归验收"])
    feedback = read_json(SOURCES["试运行反馈本地入账结果"])
    feedback_ledger = read_json(SOURCES["试运行反馈候选台账"])
    return {
        "名称": "稳定版运行指挥台",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "运行灯号": daily.get("稳定版运行状态", "unknown"),
        "今日结论": daily.get("今日结论", ""),
        "每日刷新": {
            "状态": refresh.get("总体状态"),
            "通过": refresh.get("汇总", {}).get("通过"),
            "总数": refresh.get("汇总", {}).get("总数"),
            "失败": refresh.get("汇总", {}).get("失败"),
        },
        "总巡检": {
            "状态": snapshot.get("总体状态"),
            "通过": snapshot.get("汇总", {}).get("通过"),
            "总数": snapshot.get("汇总", {}).get("总数"),
            "失败": snapshot.get("汇总", {}).get("失败"),
        },
        "总回归": {
            "通过": regression.get("通过"),
            "总数": regression.get("指标", {}).get("总数"),
            "失败": regression.get("指标", {}).get("失败"),
            "错误数": regression.get("指标", {}).get("错误数"),
        },
        "三日稳定": {
            "达标": three_day.get("三日达标"),
            "通过样本数": three_day.get("不同自然日通过样本数"),
            "仍缺样本数": three_day.get("仍缺自然日样本数"),
            "下一自然日最早采集日期": three_day.get("下一自然日最早采集日期"),
        },
        "次日闸口": {
            "当前是否可执行次日复验": day2.get("当前是否可执行次日复验"),
            "次日最早执行日期": day2.get("次日最早执行日期"),
            "是否生成次日样本": day2.get("是否生成次日样本"),
        },
        "试运行反馈": {
            "扫描文件数": feedback.get("指标", {}).get("扫描文件数"),
            "接收数": feedback.get("指标", {}).get("接收数"),
            "拒收数": feedback.get("指标", {}).get("拒收数"),
            "需总管确认数": feedback.get("指标", {}).get("需总管确认数"),
            "候选问题数": feedback_ledger.get("候选问题数"),
        },
        "推荐入口": {
            "每日一键刷新命令": f'python "{EVOLUTION_ROOT / "02脚本" / "执行稳定交付版每日一键只读刷新与日报汇总.py"}"',
            "每日一键刷新验收命令": f'python "{EVOLUTION_ROOT / "02脚本" / "验证稳定交付版每日一键只读刷新与日报汇总包.py"}"',
            "日报路径": str(SOURCES["每日运行日报"]),
            "次日待办路径": str(SOURCES["次日待办清单"]),
            "试运行反馈待入账目录": str(EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "待入账回传"),
            "试运行反馈候选台账": str(SOURCES["试运行反馈候选台账"]),
        },
        "安全边界": SAFETY_BOUNDARY,
    }


def build_dashboard_md(dashboard: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版运行指挥台",
            "",
            f"- 生成时间：{dashboard['生成时间']}",
            f"- 运行灯号：{dashboard['运行灯号']}",
            f"- 今日结论：{dashboard['今日结论']}",
            f"- 每日刷新：{dashboard['每日刷新']['通过']} / {dashboard['每日刷新']['总数']}，失败 {dashboard['每日刷新']['失败']}",
            f"- 总巡检：{dashboard['总巡检']['通过']} / {dashboard['总巡检']['总数']}，失败 {dashboard['总巡检']['失败']}",
            f"- 总回归：失败 {dashboard['总回归']['失败']}，错误 {dashboard['总回归']['错误数']}",
            f"- 三日稳定：达标={dashboard['三日稳定']['达标']}，通过样本={dashboard['三日稳定']['通过样本数']}，仍缺={dashboard['三日稳定']['仍缺样本数']}",
            f"- 次日最早采集日期：{dashboard['三日稳定']['下一自然日最早采集日期']}",
            f"- 试运行反馈：扫描={dashboard['试运行反馈']['扫描文件数']}，接收={dashboard['试运行反馈']['接收数']}，拒收={dashboard['试运行反馈']['拒收数']}，需确认={dashboard['试运行反馈']['需总管确认数']}",
            "",
            "## 推荐入口",
            "",
            f"- 每日一键刷新：`{dashboard['推荐入口']['每日一键刷新命令']}`",
            f"- 每日刷新验收：`{dashboard['推荐入口']['每日一键刷新验收命令']}`",
            f"- 日报路径：{dashboard['推荐入口']['日报路径']}",
            f"- 次日待办路径：{dashboard['推荐入口']['次日待办路径']}",
            f"- 试运行反馈待入账目录：{dashboard['推荐入口']['试运行反馈待入账目录']}",
            f"- 试运行反馈候选台账：{dashboard['推荐入口']['试运行反馈候选台账']}",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {item['存在']} | {item['状态']} | {item['路径']} |"
        for item in report["来源索引"]
    ]
    return "\n".join(
        [
            "# 稳定交付版运行指挥台索引包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 运行灯号：{report['运行灯号']}",
            f"- 来源数：{report['指标']['来源数']}",
            "",
            "| 来源 | 存在 | 状态 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    now = datetime.now()
    dashboard = build_dashboard(now)
    sources = source_status()
    report = {
        "名称": "稳定交付版运行指挥台索引包",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_runtime_dashboard_index_ready",
        "运行灯号": dashboard.get("运行灯号"),
        "来源索引": sources,
        "指挥台": str(DASHBOARD_JSON),
        "指标": {
            "来源数": len(sources),
            "来源存在数": sum(1 for item in sources if item["存在"]),
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "指挥台JSON": str(DASHBOARD_JSON),
            "指挥台Markdown": str(DASHBOARD_MD),
        },
    }
    write_json(DASHBOARD_JSON, dashboard)
    write_text(DASHBOARD_MD, build_dashboard_md(dashboard))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "运行灯号": report["运行灯号"], "来源存在数": report["指标"]["来源存在数"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
