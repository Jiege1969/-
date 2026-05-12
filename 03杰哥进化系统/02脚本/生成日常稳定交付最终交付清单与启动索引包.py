# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版最终交付清单与启动索引包。

只汇总交付入口、启动命令、验收证据和红线闸口；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定交付最终交付清单与启动索引包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "日常稳定交付最终签收启动包": EVOLUTION_ROOT / "03数据" / "94日常稳定交付最终签收启动包" / "日常稳定交付最终签收启动包_最新.json",
    "日常稳定交付签收回执与首轮试运行任务单": EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包" / "日常稳定交付签收回执与首轮试运行任务单包_最新.json",
    "日常稳定交付使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
    "使用者入口导航与常用指令": EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包" / "使用者入口导航与常用指令包_最新.json",
    "稳定版试运行反馈本地入账执行器": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账执行器包_最新.json",
    "运行期故障恢复与回滚总索引": EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包" / "运行期故障恢复与回滚总索引包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常稳定交付最终交付清单与启动索引包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定交付最终交付清单与启动索引包_最新.md"
DELIVERY_MD = DATA_DIR / "最终交付清单_最新.md"
START_INDEX_MD = DATA_DIR / "启动索引_最新.md"
ACCEPTANCE_MD = DATA_DIR / "签收验收口径_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定交付最终交付清单与启动索引包_最新.json"

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


def delivery_items() -> list[dict[str, Any]]:
    return [
        {"编号": "DEL-001", "名称": "最终签收启动包", "用途": "判断日常版和稳定版是否可签收及如何启动"},
        {"编号": "DEL-002", "名称": "签收回执与首轮试运行任务单", "用途": "落地签收回执、试运行任务和问题回收路径"},
        {"编号": "DEL-003", "名称": "使用接管与续建总包", "用途": "说明怎么接管、怎么低风险续建、哪些需确认"},
        {"编号": "DEL-004", "名称": "使用者入口导航与常用指令", "用途": "使用者从哪个入口问什么问题"},
        {"编号": "DEL-005", "名称": "一键只读总回归", "用途": "每天开工前确认 11 项基础链路通过"},
        {"编号": "DEL-006", "名称": "自主巡检快照", "用途": "查看全部已吸收验收包是否仍为 pass"},
        {"编号": "DEL-007", "名称": "反馈本地入账执行器", "用途": "问题先入账形成候选，不直接改正式规则"},
        {"编号": "DEL-008", "名称": "故障恢复与回滚总索引", "用途": "异常时按索引定位回滚和接管路径"},
    ]


def start_index() -> list[dict[str, Any]]:
    return [
        {"顺序": 1, "动作": "查看最终签收建议", "文件": str(SOURCES["日常稳定交付最终签收启动包"])},
        {"顺序": 2, "动作": "跑一键只读总回归", "命令": r'python "D:\杰哥智能化系统\03杰哥进化系统\02脚本\执行日常可用交付版一键只读总回归.py"'},
        {"顺序": 3, "动作": "验证一键只读总回归", "命令": r'python "D:\杰哥智能化系统\03杰哥进化系统\02脚本\验证日常可用交付版一键只读总回归.py"'},
        {"顺序": 4, "动作": "刷新自主巡检快照", "命令": r'python "D:\杰哥智能化系统\03杰哥进化系统\02脚本\生成日常可用版自主巡检快照.py"'},
        {"顺序": 5, "动作": "按首轮试运行任务单执行", "文件": str(DATA_DIR.parent / "95日常稳定交付签收回执与首轮试运行任务单包" / "首轮试运行任务单_最新.md")},
        {"顺序": 6, "动作": "问题进入本地入账执行器", "文件": str(SOURCES["稳定版试运行反馈本地入账执行器"])},
        {"顺序": 7, "动作": "异常时查看回滚总索引", "文件": str(SOURCES["运行期故障恢复与回滚总索引"])},
    ]


def acceptance_items() -> list[dict[str, Any]]:
    return [
        {"验收项": "日常可用版", "口径": "可签收使用", "硬条件": "一键只读总回归通过，巡检快照无失败"},
        {"验收项": "稳定交付版", "口径": "可签收试运行", "硬条件": "签收启动包、接管包、任务单包均通过"},
        {"验收项": "问题处理", "口径": "先入账后候选", "硬条件": "不直接写正式规则"},
        {"验收项": "服务重载", "口径": "需总管确认", "硬条件": "19310/19302 不自行重载"},
        {"验收项": "外部自动化", "口径": "需总管确认", "硬条件": "企业微信真实发送和 n8n 真实触发保持关闭"},
        {"验收项": "真实业务连接", "口径": "需总管确认", "硬条件": "券商、税局、财税软件、视频发布均保持关闭"},
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
        "名称": "日常稳定交付最终交付清单与启动索引包",
        "生成时间": now_text(),
        "状态": "daily_stable_final_delivery_start_index_ready" if ready else "daily_stable_final_delivery_start_index_blocked",
        "用途": "把日常可用版和稳定交付版最后交付时需要看的材料、启动动作和验收口径收成一个索引。",
        "来源摘要": source_summary,
        "最终交付清单": delivery_items(),
        "启动索引": start_index(),
        "签收验收口径": acceptance_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "最终交付清单": str(DELIVERY_MD),
            "启动索引": str(START_INDEX_MD),
            "签收验收口径": str(ACCEPTANCE_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    delivery_rows = [f"| {item['编号']} | {item['名称']} | {item['用途']} |" for item in package["最终交付清单"]]
    start_rows = [f"| {item['顺序']} | {item['动作']} | {item.get('文件') or item.get('命令')} |" for item in package["启动索引"]]
    acceptance_rows = [f"| {item['验收项']} | {item['口径']} | {item['硬条件']} |" for item in package["签收验收口径"]]
    package_md = "\n".join([
        "# 日常稳定交付最终交付清单与启动索引包",
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
        "## 最终交付清单",
        "| 编号 | 名称 | 用途 |",
        "| --- | --- | --- |",
        *delivery_rows,
        "",
        "## 启动索引",
        "| 顺序 | 动作 | 文件或命令 |",
        "| --- | --- | --- |",
        *start_rows,
        "",
        "## 签收验收口径",
        "| 验收项 | 口径 | 硬条件 |",
        "| --- | --- | --- |",
        *acceptance_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(DELIVERY_MD, "\n".join(["# 最终交付清单", "", "| 编号 | 名称 | 用途 |", "| --- | --- | --- |", *delivery_rows]))
    write_text(START_INDEX_MD, "\n".join(["# 启动索引", "", "| 顺序 | 动作 | 文件或命令 |", "| --- | --- | --- |", *start_rows]))
    write_text(ACCEPTANCE_MD, "\n".join(["# 签收验收口径", "", "| 验收项 | 口径 | 硬条件 |", "| --- | --- | --- |", *acceptance_rows]))
    write_json(GEN_LOG, {"名称": "生成日常稳定交付最终交付清单与启动索引包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "交付项": len(package["最终交付清单"]), "启动项": len(package["启动索引"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
