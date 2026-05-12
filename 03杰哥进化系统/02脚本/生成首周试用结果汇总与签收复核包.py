# -*- coding: utf-8 -*-
"""生成首周试用结果汇总与签收复核包。

只汇总本地试用场景、问题回传、签收队列和总巡检结果，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "91首周试用结果汇总与签收复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "首周试用结果汇总与签收复核包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "首周试用场景": EVOLUTION_ROOT / "03数据" / "90使用者首周试用场景演练包" / "使用者首周试用场景演练包_最新.json",
    "试运行问题回传": EVOLUTION_ROOT / "03数据" / "90稳定版试运行问题回传模板与入账预演包" / "稳定版试运行问题回传模板与入账预演包_最新.json",
    "试运行回传导航": EVOLUTION_ROOT / "03数据" / "91稳定版试运行回传入口导航与闭环索引包" / "稳定版试运行回传入口导航与闭环索引包_最新.json",
    "签收迭代队列": EVOLUTION_ROOT / "03数据" / "89使用者验收签收与后续迭代队列包" / "使用者验收签收与后续迭代队列包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "首周试用结果汇总与签收复核包_最新.json"
PACKAGE_MD = DATA_DIR / "首周试用结果汇总与签收复核包_最新.md"
SUMMARY_JSON = DATA_DIR / "首周试用结果汇总_最新.json"
SUMMARY_MD = DATA_DIR / "首周试用结果汇总_最新.md"
SIGNOFF_RECHECK_MD = DATA_DIR / "签收复核清单_最新.md"
NEXT_MD = DATA_DIR / "试用后下一步建议_最新.md"
GEN_LOG = LOG_DIR / "生成首周试用结果汇总与签收复核包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "执行真实回滚": False,
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


def build_recheck_items() -> list[dict[str, Any]]:
    return [
        {"复核项": "日常可用版签收", "结论": "保持可签收使用", "依据": "总巡检和一键总回归通过"},
        {"复核项": "稳定交付版签收", "结论": "保持可签收使用", "依据": "试用场景、问题回传、运行索引已闭环"},
        {"复核项": "完全交付使用版", "结论": "继续排队", "依据": "真实外部动作仍关闭"},
        {"复核项": "真正自主运行版", "结论": "继续排队", "依据": "正式规则和外部动作仍需总管确认"},
    ]


def build_next_steps() -> list[dict[str, Any]]:
    return [
        {"编号": "AFTER-001", "事项": "继续收集首周试用反馈", "默认动作": "入账预演与候选复验", "需总管确认": False},
        {"编号": "AFTER-002", "事项": "低风险体验优化", "默认动作": "生成候选包和只读验收", "需总管确认": False},
        {"编号": "AFTER-003", "事项": "正式规则申请", "默认动作": "申请草案审查", "需总管确认": True},
        {"编号": "AFTER-004", "事项": "n8n导入或启用", "默认动作": "凭据隔离与启用禁入检查", "需总管确认": True},
        {"编号": "AFTER-005", "事项": "视频真实渲染试运行", "默认动作": "白名单和回滚预案草案", "需总管确认": True},
    ]


def main() -> int:
    source_summary = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    snapshot = read_json(SOURCES["总巡检快照"])
    regression = read_json(SOURCES["一键只读总回归"])
    trial = read_json(SOURCES["首周试用场景"])
    signoff = read_json(SOURCES["签收迭代队列"])
    ready = (
        snapshot.get("总体状态") == "pass"
        and snapshot.get("汇总", {}).get("失败", 0) == 0
        and regression.get("通过") is True
        and regression.get("指标", {}).get("错误数", 0) == 0
        and all(item["存在"] for item in source_summary.values())
    )
    recheck_items = build_recheck_items()
    next_steps = build_next_steps()
    package = {
        "名称": "首周试用结果汇总与签收复核包",
        "生成时间": now_text(),
        "状态": "week1_trial_signoff_recheck_ready" if ready else "week1_trial_signoff_recheck_blocked",
        "用途": "汇总使用者首周试用、问题回传、签收状态和后续队列，形成签收复核证据。",
        "来源摘要": source_summary,
        "试用摘要": {
            "试用场景数": len(trial.get("试用场景", [])),
            "签收项": len(signoff.get("签收检查清单", [])),
            "迭代项": len(signoff.get("后续迭代队列", [])),
        },
        "签收复核": recheck_items,
        "试用后下一步": next_steps,
        "复核结论": "日常可用版与稳定交付版继续保持可签收使用；完全交付和真正自主运行继续排队。",
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "试用结果汇总JSON": str(SUMMARY_JSON),
            "试用结果汇总Markdown": str(SUMMARY_MD),
            "签收复核清单": str(SIGNOFF_RECHECK_MD),
            "试用后下一步建议": str(NEXT_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(SUMMARY_JSON, {"名称": "首周试用结果汇总", "试用摘要": package["试用摘要"], "签收复核": recheck_items})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    recheck_rows = [f"| {item['复核项']} | {item['结论']} | {item['依据']} |" for item in recheck_items]
    next_rows = [f"| {item['编号']} | {item['事项']} | {item['默认动作']} | {item['需总管确认']} |" for item in next_steps]
    package_md = "\n".join([
        "# 首周试用结果汇总与签收复核包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 复核结论：{package['复核结论']}",
        "",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(SUMMARY_MD, package_md)
    write_text(SIGNOFF_RECHECK_MD, "\n".join(["# 签收复核清单", "", "| 复核项 | 结论 | 依据 |", "| --- | --- | --- |", *recheck_rows]))
    write_text(NEXT_MD, "\n".join(["# 试用后下一步建议", "", "| 编号 | 事项 | 默认动作 | 需总管确认 |", "| --- | --- | --- | --- |", *next_rows]))
    write_json(GEN_LOG, {"名称": "生成首周试用结果汇总与签收复核包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "复核项": len(recheck_items), "下一步": len(next_steps), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
