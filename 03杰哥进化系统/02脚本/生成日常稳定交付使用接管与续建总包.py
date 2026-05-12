# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版的使用接管与续建总包。

只汇总既有只读验收、入口、操作卡、反馈入账和签收复核材料；
不触发外部系统，不写正式规则，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定交付使用接管与续建总包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "使用者入口导航与常用指令": EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包" / "使用者入口导航与常用指令包_最新.json",
    "稳定版一页操作卡": EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版使用者一页操作卡与灯号说明包_最新.json",
    "首周试用结果签收复核": EVOLUTION_ROOT / "03数据" / "91首周试用结果汇总与签收复核包" / "首周试用结果汇总与签收复核包_最新.json",
    "稳定版试运行反馈本地入账": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账执行器包_最新.json",
    "稳定版运行指挥台索引": EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定交付版运行指挥台索引包_最新.json",
    "稳定版每日运行日报与次日待办": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定交付版每日运行日报与次日待办包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常稳定交付使用接管与续建总包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定交付使用接管与续建总包_最新.md"
HANDOFF_MD = DATA_DIR / "使用接管清单_最新.md"
CONTINUE_MD = DATA_DIR / "后续低风险续建清单_最新.md"
GATE_MD = DATA_DIR / "必须总管确认事项清单_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定交付使用接管与续建总包_最新.json"

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


def build_handoff_items() -> list[dict[str, Any]]:
    return [
        {"编号": "HANDOFF-001", "事项": "先看使用者入口导航与常用指令", "用途": "确定从哪个入口发起税收、股票、视频、系统状态问题"},
        {"编号": "HANDOFF-002", "事项": "按稳定版一页操作卡执行", "用途": "用灯号和操作卡判断能用、阻断、需确认"},
        {"编号": "HANDOFF-003", "事项": "每日先跑日常可用版一键只读总回归", "用途": "确认公共入口、职责分流、税收、视频阻断和红线仍正常"},
        {"编号": "HANDOFF-004", "事项": "查看日常可用版自主巡检快照", "用途": "确认所有已吸收验收包仍为 pass"},
        {"编号": "HANDOFF-005", "事项": "试运行问题先进本地入账执行器", "用途": "先形成候选台账，不直接改正式规则"},
        {"编号": "HANDOFF-006", "事项": "运行指挥台索引用于找证据", "用途": "定位日报、周报、回滚、反馈、签收和续建材料"},
        {"编号": "HANDOFF-007", "事项": "首周试用结果签收复核", "用途": "复核日常可用版和稳定交付版仍可签收使用"},
        {"编号": "HANDOFF-008", "事项": "遇到红线事项登记为需总管确认", "用途": "不自动放行外部真实动作和正式规则"},
    ]


def build_continue_items() -> list[dict[str, Any]]:
    return [
        {"编号": "NEXT-001", "事项": "继续补充使用者问题样本", "默认动作": "本地入账、去重、形成候选", "需总管确认": False},
        {"编号": "NEXT-002", "事项": "继续刷新日报、周报、趋势包", "默认动作": "只读汇总和证据索引", "需总管确认": False},
        {"编号": "NEXT-003", "事项": "继续补齐低风险操作文档", "默认动作": "生成候选文档和只读验收", "需总管确认": False},
        {"编号": "NEXT-004", "事项": "正式规则申请", "默认动作": "只生成申请草案和冲突扫描", "需总管确认": True},
        {"编号": "NEXT-005", "事项": "n8n导入或启用", "默认动作": "只做离线蓝图、干跑和凭据隔离检查", "需总管确认": True},
        {"编号": "NEXT-006", "事项": "企业微信真实发送", "默认动作": "只保留本地预演和 real_send=false", "需总管确认": True},
        {"编号": "NEXT-007", "事项": "视频真实渲染或发布", "默认动作": "只做环境识别、白名单、回滚预案", "需总管确认": True},
    ]


def build_gates() -> list[dict[str, Any]]:
    return [
        {"事项": "19310/19302重载", "当前口径": "只登记需总管确认，不自行重载"},
        {"事项": "正式规则变更", "当前口径": "只生成候选或申请草案，不自动生效"},
        {"事项": "n8n真实触发", "当前口径": "只做离线蓝图、干跑和禁用态检查"},
        {"事项": "企业微信真实发送", "当前口径": "只做本地预演，不发给联系人或群"},
        {"事项": "券商/交易", "当前口径": "只做研究展示和风险复核，不接账户不下单"},
        {"事项": "税局/财税软件", "当前口径": "只做待复核草案，不登录不读取真实账务"},
        {"事项": "视频真实渲染/发布", "当前口径": "未放行前只阻断和预检"},
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
        "名称": "日常稳定交付使用接管与续建总包",
        "生成时间": now_text(),
        "状态": "daily_stable_handoff_continue_ready" if ready else "daily_stable_handoff_continue_blocked",
        "用途": "把日常可用版和稳定交付版的入口、巡检、签收、反馈入账、运行指挥台和后续续建动作汇总成可接管材料。",
        "来源摘要": source_summary,
        "使用接管清单": build_handoff_items(),
        "后续低风险续建清单": build_continue_items(),
        "必须总管确认事项": build_gates(),
        "交付判断": {
            "日常可用交付版": "可签收使用",
            "稳定交付版": "可签收试运行",
            "完全交付使用版": "继续排队",
            "真正自主运行版": "继续排队",
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "使用接管清单": str(HANDOFF_MD),
            "后续低风险续建清单": str(CONTINUE_MD),
            "必须总管确认事项清单": str(GATE_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    handoff_rows = [f"| {item['编号']} | {item['事项']} | {item['用途']} |" for item in package["使用接管清单"]]
    continue_rows = [f"| {item['编号']} | {item['事项']} | {item['默认动作']} | {item['需总管确认']} |" for item in package["后续低风险续建清单"]]
    gate_rows = [f"| {item['事项']} | {item['当前口径']} |" for item in package["必须总管确认事项"]]
    package_md = "\n".join([
        "# 日常稳定交付使用接管与续建总包",
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
        "## 使用接管清单",
        "| 编号 | 事项 | 用途 |",
        "| --- | --- | --- |",
        *handoff_rows,
        "",
        "## 后续低风险续建清单",
        "| 编号 | 事项 | 默认动作 | 需总管确认 |",
        "| --- | --- | --- | --- |",
        *continue_rows,
        "",
        "## 必须总管确认事项",
        "| 事项 | 当前口径 |",
        "| --- | --- |",
        *gate_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(HANDOFF_MD, "\n".join(["# 使用接管清单", "", "| 编号 | 事项 | 用途 |", "| --- | --- | --- |", *handoff_rows]))
    write_text(CONTINUE_MD, "\n".join(["# 后续低风险续建清单", "", "| 编号 | 事项 | 默认动作 | 需总管确认 |", "| --- | --- | --- | --- |", *continue_rows]))
    write_text(GATE_MD, "\n".join(["# 必须总管确认事项清单", "", "| 事项 | 当前口径 |", "| --- | --- |", *gate_rows]))
    write_json(GEN_LOG, {"名称": "生成日常稳定交付使用接管与续建总包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "接管事项": len(package["使用接管清单"]), "续建事项": len(package["后续低风险续建清单"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
