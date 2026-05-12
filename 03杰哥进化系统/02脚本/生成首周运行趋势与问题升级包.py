# -*- coding: utf-8 -*-
"""生成首周运行趋势与问题升级包。

只生成本地趋势模板、升级矩阵和周复盘清单；不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "首周运行趋势与问题升级包验收"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"
DAY1_JSON = EVOLUTION_ROOT / "03数据" / "81交付后首日运行观察与问题登记包" / "交付后首日运行观察与问题登记包_最新.json"
DAILY_JSON = EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包" / "每日开工收工清单与低风险续跑包_最新.json"

PACKAGE_JSON = DATA_DIR / "首周运行趋势与问题升级包_最新.json"
PACKAGE_MD = DATA_DIR / "首周运行趋势与问题升级包_最新.md"
TREND_JSON = DATA_DIR / "首周运行趋势记录模板_最新.json"
TREND_MD = DATA_DIR / "首周运行趋势记录模板_最新.md"
ESCALATION_MD = DATA_DIR / "问题升级矩阵_最新.md"
WEEK_REVIEW_MD = DATA_DIR / "首周复盘清单_最新.md"
GEN_LOG = LOG_DIR / "生成首周运行趋势与问题升级包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_trend_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for day in range(1, 8):
        rows.append(
            {
                "自然日序号": day,
                "总巡检状态": "待记录",
                "总巡检通过数": None,
                "总巡检失败数": None,
                "一键总回归状态": "待记录",
                "新增问题数": 0,
                "红线触发数": 0,
                "需总管确认数": 0,
                "低风险候选新增数": 0,
                "备注": "",
            }
        )
    return rows


def build_escalation_matrix() -> list[dict[str, Any]]:
    return [
        {"级别": "观察", "触发条件": "单日非红线问题，且不影响总巡检/总回归", "处理": "登记首日或当日问题台账，生成候选即可", "是否需总管确认": False},
        {"级别": "复验", "触发条件": "同类问题连续2天出现", "处理": "生成复验任务和只读回归卡", "是否需总管确认": False},
        {"级别": "升级", "触发条件": "同类问题连续3天出现，或影响日常使用体验", "处理": "登记稳定版缺口，等待总管确认是否进入修复", "是否需总管确认": True},
        {"级别": "停机确认", "触发条件": "涉及真实发送、触发n8n、交易、登录、渲染、发布、正式规则、服务重载", "处理": "立即暂停，只登记不执行", "是否需总管确认": True},
        {"级别": "正式规则候选", "触发条件": "一周内多次复验通过且不触碰红线", "处理": "仅生成正式规则候选草案，不自动生效", "是否需总管确认": True},
    ]


def main() -> int:
    snapshot = read_json(SNAPSHOT_JSON)
    regression = read_json(REGRESSION_JSON)
    day1 = read_json(DAY1_JSON)
    daily = read_json(DAILY_JSON)
    trend_rows = build_trend_rows()
    escalation = build_escalation_matrix()
    package = {
        "名称": "首周运行趋势与问题升级包",
        "生成时间": now_text(),
        "状态": "week1_trend_escalation_ready",
        "用途": "把稳定交付后的首周运行趋势、问题升级和周复盘固定为低风险本地流程。",
        "当前总巡检": {"路径": str(SNAPSHOT_JSON), "总体状态": snapshot.get("总体状态"), "汇总": snapshot.get("汇总", {})},
        "当前总回归": {"路径": str(REGRESSION_JSON), "通过": regression.get("通过"), "指标": regression.get("指标", {})},
        "依赖包": {
            "首日观察包": {"路径": str(DAY1_JSON), "状态": day1.get("状态")},
            "每日开工收工包": {"路径": str(DAILY_JSON), "状态": daily.get("状态")},
        },
        "趋势记录模板": trend_rows,
        "问题升级矩阵": escalation,
        "周复盘清单": [
            "核对7天总巡检失败数是否全部为0。",
            "核对一键总回归错误数是否持续为0。",
            "统计红线触发和需总管确认次数。",
            "统计低风险候选新增数和关闭数。",
            "把连续问题升级为稳定版缺口候选，不自动改正式规则。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "趋势记录模板JSON": str(TREND_JSON),
            "趋势记录模板Markdown": str(TREND_MD),
            "问题升级矩阵": str(ESCALATION_MD),
            "首周复盘清单": str(WEEK_REVIEW_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(TREND_JSON, {"名称": "首周运行趋势记录模板", "趋势记录模板": trend_rows, "安全边界": SAFETY_BOUNDARY})

    trend_rows_md = [
        f"| 第{row['自然日序号']}天 | {row['总巡检状态']} | {row['一键总回归状态']} | {row['新增问题数']} | {row['红线触发数']} | {row['需总管确认数']} |"
        for row in trend_rows
    ]
    escalation_rows = [
        f"| {row['级别']} | {row['触发条件']} | {row['处理']} | {row['是否需总管确认']} |"
        for row in escalation
    ]
    package_md = "\n".join(
        [
            "# 首周运行趋势与问题升级包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            "- 结论：只记录趋势和升级条件，不执行任何外部动作。",
            "",
            "| 天数 | 总巡检 | 总回归 | 新增问题 | 红线 | 需总管确认 |",
            "| --- | --- | --- | --- | --- | --- |",
            *trend_rows_md,
        ]
    )
    write_text(PACKAGE_MD, package_md)
    write_text(TREND_MD, package_md)
    write_text(
        ESCALATION_MD,
        "\n".join(["# 问题升级矩阵", "", "| 级别 | 触发条件 | 处理 | 需总管确认 |", "| --- | --- | --- | --- |", *escalation_rows]),
    )
    write_text(WEEK_REVIEW_MD, "# 首周复盘清单\n\n" + "\n".join(f"- {item}" for item in package["周复盘清单"]))
    write_json(GEN_LOG, {"名称": "生成首周运行趋势与问题升级包", "生成时间": now_text(), "通过": True, "错误数": 0, "输出": package["输出文件"]})
    print(json.dumps({"状态": "ready", "趋势天数": len(trend_rows), "升级级别": len(escalation), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
