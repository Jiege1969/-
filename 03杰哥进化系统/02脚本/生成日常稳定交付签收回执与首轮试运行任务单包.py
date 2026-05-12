# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版签收回执与首轮试运行任务单包。

只生成本地签收回执模板、首轮试运行任务单和问题回收路径；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定交付签收回执与首轮试运行任务单包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "日常稳定交付最终签收启动包": EVOLUTION_ROOT / "03数据" / "94日常稳定交付最终签收启动包" / "日常稳定交付最终签收启动包_最新.json",
    "日常稳定交付使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
    "稳定版试运行反馈本地入账": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账执行器包_最新.json",
    "运行期问题闭环总台账索引": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
    "运行期故障恢复与回滚总索引": EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包" / "运行期故障恢复与回滚总索引包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常稳定交付签收回执与首轮试运行任务单包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定交付签收回执与首轮试运行任务单包_最新.md"
RECEIPT_MD = DATA_DIR / "签收回执模板_最新.md"
TASK_MD = DATA_DIR / "首轮试运行任务单_最新.md"
ISSUE_MD = DATA_DIR / "问题回收路径_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定交付签收回执与首轮试运行任务单包_最新.json"

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


def receipt_items() -> list[dict[str, Any]]:
    return [
        {"项目": "日常可用交付版", "建议选择": "签收使用", "签收口径": "作为日常问答、预演、只读巡检和低风险候选沉淀入口使用"},
        {"项目": "稳定交付版", "建议选择": "签收试运行", "签收口径": "按操作卡和运行指挥台试运行，问题先入账，不直接变正式规则"},
        {"项目": "完全交付使用版", "建议选择": "暂缓签收", "签收口径": "等待外部真实动作红线逐项人工解锁"},
        {"项目": "真正自主运行版", "建议选择": "暂缓签收", "签收口径": "等待长期运行样本、正式规则治理和外部自动化能力沉淀"},
    ]


def trial_tasks() -> list[dict[str, Any]]:
    return [
        {"编号": "TRIAL-001", "任务": "开局只读总回归", "通过标准": "一键只读总回归 11/11 通过", "失败处理": "登记问题，不继续扩大动作"},
        {"编号": "TRIAL-002", "任务": "税收三条样例复测", "通过标准": "均返回待复核草案摘要且事项正确", "失败处理": "回收到公共入口或税收候选"},
        {"编号": "TRIAL-003", "任务": "股票展示口径抽测", "通过标准": "无推荐/回避冲突，无交易化表达", "失败处理": "回收到展示层候选，不改分析引擎"},
        {"编号": "TRIAL-004", "任务": "视频阻断链路抽测", "通过标准": "真实渲染和发布继续 blocked", "失败处理": "停止视频真实动作并登记"},
        {"编号": "TRIAL-005", "任务": "问题回传入账", "通过标准": "问题形成候选台账或拒收清单", "失败处理": "手工登记到问题闭环台账"},
        {"编号": "TRIAL-006", "任务": "每日运行日报", "通过标准": "生成日报与次日待办", "失败处理": "回到运行指挥台索引定位"},
        {"编号": "TRIAL-007", "任务": "红线事项复核", "通过标准": "所有红线仍需总管确认", "失败处理": "立即停止并标记需总管确认"},
    ]


def issue_routes() -> list[dict[str, Any]]:
    return [
        {"问题类型": "入口/分流异常", "回收路径": "企业微信公共接入层候选或只读巡检包", "默认动作": "本地复测"},
        {"问题类型": "税收事项识别异常", "回收路径": "税收业务候选，不生成正式税务结论", "默认动作": "待复核草案对照"},
        {"问题类型": "股票展示口径异常", "回收路径": "股票前台展示层候选", "默认动作": "只修展示，不接交易"},
        {"问题类型": "视频渲染/发布误放行", "回收路径": "视频阻断与放行前检查", "默认动作": "立即 blocked"},
        {"问题类型": "n8n/外部触发诉求", "回收路径": "n8n离线蓝图和禁用态检查", "默认动作": "不真实触发"},
        {"问题类型": "正式规则诉求", "回收路径": "正式规则申请草案和冲突扫描", "默认动作": "需总管确认"},
        {"问题类型": "服务重载诉求", "回收路径": "重载确认登记", "默认动作": "需总管确认"},
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
        "名称": "日常稳定交付签收回执与首轮试运行任务单包",
        "生成时间": now_text(),
        "状态": "daily_stable_signoff_receipt_trial_task_ready" if ready else "daily_stable_signoff_receipt_trial_task_blocked",
        "用途": "为日常可用版签收使用和稳定交付版首轮试运行提供回执模板、任务单和问题回收路径。",
        "来源摘要": source_summary,
        "签收回执模板": receipt_items(),
        "首轮试运行任务单": trial_tasks(),
        "问题回收路径": issue_routes(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "签收回执模板": str(RECEIPT_MD),
            "首轮试运行任务单": str(TASK_MD),
            "问题回收路径": str(ISSUE_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    receipt_rows = [f"| {item['项目']} | {item['建议选择']} | {item['签收口径']} |" for item in package["签收回执模板"]]
    task_rows = [f"| {item['编号']} | {item['任务']} | {item['通过标准']} | {item['失败处理']} |" for item in package["首轮试运行任务单"]]
    issue_rows = [f"| {item['问题类型']} | {item['回收路径']} | {item['默认动作']} |" for item in package["问题回收路径"]]
    package_md = "\n".join([
        "# 日常稳定交付签收回执与首轮试运行任务单包",
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
        "## 签收回执模板",
        "| 项目 | 建议选择 | 签收口径 |",
        "| --- | --- | --- |",
        *receipt_rows,
        "",
        "## 首轮试运行任务单",
        "| 编号 | 任务 | 通过标准 | 失败处理 |",
        "| --- | --- | --- | --- |",
        *task_rows,
        "",
        "## 问题回收路径",
        "| 问题类型 | 回收路径 | 默认动作 |",
        "| --- | --- | --- |",
        *issue_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(RECEIPT_MD, "\n".join(["# 签收回执模板", "", "| 项目 | 建议选择 | 签收口径 |", "| --- | --- | --- |", *receipt_rows]))
    write_text(TASK_MD, "\n".join(["# 首轮试运行任务单", "", "| 编号 | 任务 | 通过标准 | 失败处理 |", "| --- | --- | --- | --- |", *task_rows]))
    write_text(ISSUE_MD, "\n".join(["# 问题回收路径", "", "| 问题类型 | 回收路径 | 默认动作 |", "| --- | --- | --- |", *issue_rows]))
    write_json(GEN_LOG, {"名称": "生成日常稳定交付签收回执与首轮试运行任务单包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "任务数": len(package["首轮试运行任务单"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
