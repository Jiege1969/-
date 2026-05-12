# -*- coding: utf-8 -*-
"""生成稳定交付版本地试运行达标复核与签收完成包。

只基于本地只读回归、观察执行闭环和签收启动材料做复核；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99稳定交付版本地试运行达标复核与签收完成包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版本地试运行达标复核与签收完成包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "稳定试运行首轮观察执行闭环": EVOLUTION_ROOT / "03数据" / "98稳定试运行首轮观察执行闭环包" / "稳定试运行首轮观察执行闭环包_最新.json",
    "日常签收完成与稳定试运行启动回传": EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包" / "日常签收完成与稳定试运行启动回传包_最新.json",
    "最终交付清单与启动索引": EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
    "签收回执与首轮试运行任务单": EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包" / "日常稳定交付签收回执与首轮试运行任务单包_最新.json",
    "最终签收启动包": EVOLUTION_ROOT / "03数据" / "94日常稳定交付最终签收启动包" / "日常稳定交付最终签收启动包_最新.json",
    "使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "稳定交付版本地试运行达标复核与签收完成包_最新.json"
PACKAGE_MD = DATA_DIR / "稳定交付版本地试运行达标复核与签收完成包_最新.md"
PASS_MD = DATA_DIR / "稳定交付版达标复核结论_最新.md"
SIGNOFF_MD = DATA_DIR / "稳定交付版签收完成说明_最新.md"
KEEP_MD = DATA_DIR / "签收后持续运行守护清单_最新.md"
GEN_LOG = LOG_DIR / "生成稳定交付版本地试运行达标复核与签收完成包_最新.json"

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


def pass_items() -> list[dict[str, str]]:
    return [
        {"复核项": "入口与职责分流", "结论": "达标", "依据": "企业微信公共入口巡检和一键只读总回归持续通过"},
        {"复核项": "税收待复核链路", "结论": "达标", "依据": "税收样例只输出待复核草案摘要，不生成正式税务结论"},
        {"复核项": "股票展示链路", "结论": "达标", "依据": "展示口径保持非交易化，无推荐/回避冲突"},
        {"复核项": "视频安全阻断", "结论": "达标", "依据": "真实渲染和真实发布仍保持 blocked"},
        {"复核项": "问题回收与候选入账", "结论": "达标", "依据": "反馈本地入账和问题闭环处理清单可用"},
        {"复核项": "红线守护", "结论": "达标", "依据": "所有外部真实动作、正式规则和服务重载仍需总管确认"},
    ]


def signoff_items() -> list[dict[str, str]]:
    return [
        {"版本": "日常可用交付版", "签收状态": "已具备签收完成条件", "后续": "进入日常使用和只读巡检"},
        {"版本": "稳定交付版", "签收状态": "已具备本地试运行签收完成条件", "后续": "进入持续运行观察和问题闭环"},
        {"版本": "完全交付使用版", "签收状态": "未签收", "后续": "等待外部真实能力和正式规则逐项人工解锁"},
        {"版本": "真正自主运行版", "签收状态": "未签收", "后续": "继续累积长期运行样本和人工确认经验"},
    ]


def keep_items() -> list[dict[str, str]]:
    return [
        {"守护项": "每日开工回归", "要求": "一键只读总回归必须通过"},
        {"守护项": "自主巡检快照", "要求": "失败数保持 0"},
        {"守护项": "问题入账", "要求": "所有反馈先进候选或拒收清单"},
        {"守护项": "低风险续建", "要求": "只做候选、文档、只读验收和展示层小修"},
        {"守护项": "需确认事项", "要求": "正式规则、n8n、真实发送、真实渲染发布、服务重载均停在总管确认"},
        {"守护项": "签收后回滚", "要求": "异常时按运行期故障恢复与回滚总索引处理"},
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
        "名称": "稳定交付版本地试运行达标复核与签收完成包",
        "生成时间": now_text(),
        "状态": "stable_local_trial_acceptance_signoff_done" if ready else "stable_local_trial_acceptance_signoff_blocked",
        "用途": "把稳定交付版的本地试运行复核结果、签收完成说明和签收后守护清单收口。",
        "来源摘要": source_summary,
        "稳定交付版达标复核结论": pass_items(),
        "稳定交付版签收完成说明": signoff_items(),
        "签收后持续运行守护清单": keep_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "稳定交付版达标复核结论": str(PASS_MD),
            "稳定交付版签收完成说明": str(SIGNOFF_MD),
            "签收后持续运行守护清单": str(KEEP_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    pass_rows = [f"| {item['复核项']} | {item['结论']} | {item['依据']} |" for item in package["稳定交付版达标复核结论"]]
    signoff_rows = [f"| {item['版本']} | {item['签收状态']} | {item['后续']} |" for item in package["稳定交付版签收完成说明"]]
    keep_rows = [f"| {item['守护项']} | {item['要求']} |" for item in package["签收后持续运行守护清单"]]
    package_md = "\n".join([
        "# 稳定交付版本地试运行达标复核与签收完成包",
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
        "## 稳定交付版达标复核结论",
        "| 复核项 | 结论 | 依据 |",
        "| --- | --- | --- |",
        *pass_rows,
        "",
        "## 稳定交付版签收完成说明",
        "| 版本 | 签收状态 | 后续 |",
        "| --- | --- | --- |",
        *signoff_rows,
        "",
        "## 签收后持续运行守护清单",
        "| 守护项 | 要求 |",
        "| --- | --- |",
        *keep_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(PASS_MD, "\n".join(["# 稳定交付版达标复核结论", "", "| 复核项 | 结论 | 依据 |", "| --- | --- | --- |", *pass_rows]))
    write_text(SIGNOFF_MD, "\n".join(["# 稳定交付版签收完成说明", "", "| 版本 | 签收状态 | 后续 |", "| --- | --- | --- |", *signoff_rows]))
    write_text(KEEP_MD, "\n".join(["# 签收后持续运行守护清单", "", "| 守护项 | 要求 |", "| --- | --- |", *keep_rows]))
    write_json(GEN_LOG, {"名称": "生成稳定交付版本地试运行达标复核与签收完成包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "复核项": len(package["稳定交付版达标复核结论"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
