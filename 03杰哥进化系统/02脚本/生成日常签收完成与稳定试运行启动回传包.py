# -*- coding: utf-8 -*-
"""生成日常可用版签收完成与稳定版试运行启动回传包。

只形成本地回传、启动观察点和剩余缺口说明；不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常签收完成与稳定试运行启动回传包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "最终交付清单与启动索引": EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
    "签收回执与首轮试运行任务单": EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包" / "日常稳定交付签收回执与首轮试运行任务单包_最新.json",
    "最终签收启动包": EVOLUTION_ROOT / "03数据" / "94日常稳定交付最终签收启动包" / "日常稳定交付最终签收启动包_最新.json",
    "使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常签收完成与稳定试运行启动回传包_最新.json"
PACKAGE_MD = DATA_DIR / "日常签收完成与稳定试运行启动回传包_最新.md"
SIGNOFF_DONE_MD = DATA_DIR / "日常可用版签收完成说明_最新.md"
STABLE_START_MD = DATA_DIR / "稳定版试运行启动说明_最新.md"
REMAINING_GAPS_MD = DATA_DIR / "剩余缺口与红线说明_最新.md"
GEN_LOG = LOG_DIR / "生成日常签收完成与稳定试运行启动回传包_最新.json"

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


def signoff_done() -> list[dict[str, str]]:
    return [
        {"项目": "日常可用交付版", "结论": "完成签收条件", "说明": "公共入口、职责分流、税收待复核、股票展示口径、视频阻断、一键只读总回归均有验收证据"},
        {"项目": "使用方式", "结论": "可进入日常使用", "说明": "使用者按入口导航和操作卡使用，异常先进本地问题入账"},
        {"项目": "安全边界", "结论": "保持关闭", "说明": "真实发送、n8n、券商、税局、财税软件、视频真实渲染发布均未放行"},
    ]


def stable_start() -> list[dict[str, str]]:
    return [
        {"观察点": "首轮试运行任务单", "启动口径": "按 7 项任务逐项执行", "异常处理": "登记问题并回收到候选或台账"},
        {"观察点": "每日一键只读回归", "启动口径": "每天开工先跑", "异常处理": "失败时停在问题回收路径"},
        {"观察点": "反馈本地入账", "启动口径": "所有试运行反馈先进本地候选", "异常处理": "不得直接改正式规则"},
        {"观察点": "运行日报与次日待办", "启动口径": "每日汇总低风险续建和需确认事项", "异常处理": "需确认事项不自动执行"},
        {"观察点": "回滚与接管索引", "启动口径": "异常时按索引定位处理", "异常处理": "不得自行重载 19310/19302"},
    ]


def remaining_gaps() -> list[dict[str, str]]:
    return [
        {"缺口": "完全交付使用版", "原因": "外部真实动作和正式规则仍保持关闭", "下一步": "继续做低风险模板、离线预演和人工确认材料"},
        {"缺口": "真正自主运行版", "原因": "长期运行样本、自动化治理和红线解锁仍不足", "下一步": "继续累积试运行数据和人工确认经验"},
        {"缺口": "n8n启用", "原因": "真实触发关闭", "下一步": "只做离线蓝图、干跑、凭据隔离和启用申请"},
        {"缺口": "视频真实渲染/发布", "原因": "环境和放行链仍阻断", "下一步": "只做识别、预检、白名单和回滚预案"},
        {"缺口": "正式规则", "原因": "候选不能自动转正式", "下一步": "只做申请草案、冲突扫描和签收台账"},
    ]


def main() -> int:
    source_summary: dict[str, Any] = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("总体状态") or data.get("状态") or data.get("通过") or data.get("passed"),
            "指标": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }

    snapshot = read_json(SOURCES["日常可用版自主巡检快照"])
    regression = read_json(SOURCES["日常可用版一键只读总回归"])
    ready = (
        all(item["存在"] for item in source_summary.values())
        and snapshot.get("总体状态") == "pass"
        and snapshot.get("汇总", {}).get("失败", 0) == 0
        and regression.get("通过") is True
        and regression.get("指标", {}).get("错误数", 0) == 0
    )

    package = {
        "名称": "日常签收完成与稳定试运行启动回传包",
        "生成时间": now_text(),
        "状态": "daily_signoff_done_stable_trial_start_ready" if ready else "daily_signoff_done_stable_trial_start_blocked",
        "用途": "作为日常可用版签收完成和稳定交付版进入试运行的本地回传证据。",
        "来源摘要": source_summary,
        "日常可用版签收完成说明": signoff_done(),
        "稳定版试运行启动说明": stable_start(),
        "剩余缺口与红线说明": remaining_gaps(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "日常可用版签收完成说明": str(SIGNOFF_DONE_MD),
            "稳定版试运行启动说明": str(STABLE_START_MD),
            "剩余缺口与红线说明": str(REMAINING_GAPS_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    signoff_rows = [f"| {item['项目']} | {item['结论']} | {item['说明']} |" for item in package["日常可用版签收完成说明"]]
    stable_rows = [f"| {item['观察点']} | {item['启动口径']} | {item['异常处理']} |" for item in package["稳定版试运行启动说明"]]
    gap_rows = [f"| {item['缺口']} | {item['原因']} | {item['下一步']} |" for item in package["剩余缺口与红线说明"]]
    package_md = "\n".join([
        "# 日常签收完成与稳定试运行启动回传包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 用途：{package['用途']}",
        "",
        "## 来源摘要",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
        "",
        "## 日常可用版签收完成说明",
        "| 项目 | 结论 | 说明 |",
        "| --- | --- | --- |",
        *signoff_rows,
        "",
        "## 稳定版试运行启动说明",
        "| 观察点 | 启动口径 | 异常处理 |",
        "| --- | --- | --- |",
        *stable_rows,
        "",
        "## 剩余缺口与红线说明",
        "| 缺口 | 原因 | 下一步 |",
        "| --- | --- | --- |",
        *gap_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(SIGNOFF_DONE_MD, "\n".join(["# 日常可用版签收完成说明", "", "| 项目 | 结论 | 说明 |", "| --- | --- | --- |", *signoff_rows]))
    write_text(STABLE_START_MD, "\n".join(["# 稳定版试运行启动说明", "", "| 观察点 | 启动口径 | 异常处理 |", "| --- | --- | --- |", *stable_rows]))
    write_text(REMAINING_GAPS_MD, "\n".join(["# 剩余缺口与红线说明", "", "| 缺口 | 原因 | 下一步 |", "| --- | --- | --- |", *gap_rows]))
    write_json(GEN_LOG, {"名称": "生成日常签收完成与稳定试运行启动回传包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "日常签收项": len(package["日常可用版签收完成说明"]), "稳定观察点": len(package["稳定版试运行启动说明"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
