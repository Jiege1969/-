# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版双版本交付封存与后续路线包。

只汇总已通过的本地验收、签收完成说明、持续运行守护和后续路线；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "100日常稳定双版本交付封存与后续路线包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定双版本交付封存与后续路线包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "稳定交付版本地试运行达标复核与签收完成": EVOLUTION_ROOT / "03数据" / "99稳定交付版本地试运行达标复核与签收完成包" / "稳定交付版本地试运行达标复核与签收完成包_最新.json",
    "稳定试运行首轮观察执行闭环": EVOLUTION_ROOT / "03数据" / "98稳定试运行首轮观察执行闭环包" / "稳定试运行首轮观察执行闭环包_最新.json",
    "日常签收完成与稳定试运行启动回传": EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包" / "日常签收完成与稳定试运行启动回传包_最新.json",
    "最终交付清单与启动索引": EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
    "签收回执与首轮试运行任务单": EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包" / "日常稳定交付签收回执与首轮试运行任务单包_最新.json",
    "使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常稳定双版本交付封存与后续路线包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定双版本交付封存与后续路线包_最新.md"
FREEZE_MD = DATA_DIR / "双版本交付封存说明_最新.md"
ROUTE_MD = DATA_DIR / "后续路线分层清单_最新.md"
KEEP_MD = DATA_DIR / "封存后守护与复验清单_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定双版本交付封存与后续路线包_最新.json"

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


def freeze_items() -> list[dict[str, str]]:
    return [
        {"版本": "日常可用交付版", "封存状态": "已封存为可签收使用", "证据": "一键只读总回归、自主巡检快照、签收完成回传均通过"},
        {"版本": "稳定交付版", "封存状态": "已封存为本地试运行签收完成", "证据": "试运行观察闭环、达标复核、签收完成说明均通过"},
        {"版本": "完全交付使用版", "封存状态": "未封存", "证据": "仍受外部真实动作和正式规则红线限制"},
        {"版本": "真正自主运行版", "封存状态": "未封存", "证据": "仍需长期样本、正式规则治理和外部自动化人工解锁"},
    ]


def route_items() -> list[dict[str, str]]:
    return [
        {"路线": "日常可用版后续", "默认动作": "每日只读回归、问题入账、低风险候选续建", "是否需确认": "否"},
        {"路线": "稳定交付版后续", "默认动作": "持续运行观察、日报、次轮样本扩展、回滚索引守护", "是否需确认": "否"},
        {"路线": "正式规则路线", "默认动作": "申请草案、冲突扫描、签收台账", "是否需确认": "是"},
        {"路线": "n8n路线", "默认动作": "离线蓝图、干跑、凭据隔离、启用禁入检查", "是否需确认": "是"},
        {"路线": "视频真实渲染/发布路线", "默认动作": "环境识别、白名单、预检、回滚预案", "是否需确认": "是"},
        {"路线": "真实业务连接路线", "默认动作": "税局、财税软件、券商均继续禁用", "是否需确认": "是"},
    ]


def keep_items() -> list[dict[str, str]]:
    return [
        {"守护项": "只读总回归", "复验频率": "每日或每次改动后", "通过标准": "11/11 通过"},
        {"守护项": "自主巡检快照", "复验频率": "每批吸收后", "通过标准": "失败数为 0"},
        {"守护项": "稳定试运行观察", "复验频率": "每轮试运行后", "通过标准": "观察项全部达标或入账"},
        {"守护项": "问题闭环", "复验频率": "每次问题回传后", "通过标准": "候选、拒收、需确认三类清楚"},
        {"守护项": "红线闸口", "复验频率": "持续", "通过标准": "真实动作和正式规则未自动放行"},
        {"守护项": "服务重载", "复验频率": "涉及 19310/19302 时", "通过标准": "先登记需总管确认"},
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
        "名称": "日常稳定双版本交付封存与后续路线包",
        "生成时间": now_text(),
        "状态": "daily_stable_dual_delivery_freeze_ready" if ready else "daily_stable_dual_delivery_freeze_blocked",
        "用途": "将日常可用版和稳定交付版的签收完成状态封存，并把后续完全交付、自主运行路线分层列清。",
        "来源摘要": source_summary,
        "双版本交付封存说明": freeze_items(),
        "后续路线分层清单": route_items(),
        "封存后守护与复验清单": keep_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "双版本交付封存说明": str(FREEZE_MD),
            "后续路线分层清单": str(ROUTE_MD),
            "封存后守护与复验清单": str(KEEP_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    freeze_rows = [f"| {item['版本']} | {item['封存状态']} | {item['证据']} |" for item in package["双版本交付封存说明"]]
    route_rows = [f"| {item['路线']} | {item['默认动作']} | {item['是否需确认']} |" for item in package["后续路线分层清单"]]
    keep_rows = [f"| {item['守护项']} | {item['复验频率']} | {item['通过标准']} |" for item in package["封存后守护与复验清单"]]
    package_md = "\n".join([
        "# 日常稳定双版本交付封存与后续路线包",
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
        "## 双版本交付封存说明",
        "| 版本 | 封存状态 | 证据 |",
        "| --- | --- | --- |",
        *freeze_rows,
        "",
        "## 后续路线分层清单",
        "| 路线 | 默认动作 | 是否需确认 |",
        "| --- | --- | --- |",
        *route_rows,
        "",
        "## 封存后守护与复验清单",
        "| 守护项 | 复验频率 | 通过标准 |",
        "| --- | --- | --- |",
        *keep_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(FREEZE_MD, "\n".join(["# 双版本交付封存说明", "", "| 版本 | 封存状态 | 证据 |", "| --- | --- | --- |", *freeze_rows]))
    write_text(ROUTE_MD, "\n".join(["# 后续路线分层清单", "", "| 路线 | 默认动作 | 是否需确认 |", "| --- | --- | --- |", *route_rows]))
    write_text(KEEP_MD, "\n".join(["# 封存后守护与复验清单", "", "| 守护项 | 复验频率 | 通过标准 |", "| --- | --- | --- |", *keep_rows]))
    write_json(GEN_LOG, {"名称": "生成日常稳定双版本交付封存与后续路线包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "封存项": len(package["双版本交付封存说明"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
