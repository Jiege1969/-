# -*- coding: utf-8 -*-
"""生成稳定交付失败自动分级与总管确认闸口包。

本包只定义失败分级和确认闸口，不修改正式规则、不触发服务重载。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包"
LATEST_JSON = OUTPUT_DIR / "稳定交付失败自动分级与总管确认闸口包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付失败自动分级与总管确认闸口包_最新.md"
LEVELS_MD = OUTPUT_DIR / "失败分级规则_最新.md"
CONFIRM_MD = OUTPUT_DIR / "需总管确认闸口清单_最新.md"
DISPATCH_MD = OUTPUT_DIR / "失败后自动处置矩阵_最新.md"


FAILURE_LEVELS: list[dict[str, Any]] = [
    {
        "级别": "L0",
        "名称": "全部通过",
        "判定": "只读巡检、总回归、候选验收均通过。",
        "动作": "继续自主施工下一批低风险候选包。",
        "是否需总管确认": False,
        "是否允许自动复跑": False,
    },
    {
        "级别": "L1",
        "名称": "只读产物缺失或过期",
        "判定": "最新 JSON/Markdown 不存在、验收日志缺失、快照引用断裂。",
        "动作": "允许自动重建候选资料或复跑只读验收。",
        "是否需总管确认": False,
        "是否允许自动复跑": True,
    },
    {
        "级别": "L2",
        "名称": "低风险口径不一致",
        "判定": "展示层措辞、候选说明、预检卡、只读清单不一致，但不涉及服务运行和外部动作。",
        "动作": "允许在原业务边界内最小修复，并复跑对应只读验收。",
        "是否需总管确认": False,
        "是否允许自动复跑": True,
    },
    {
        "级别": "L3",
        "名称": "运行服务加载异常",
        "判定": "代码或配置产物已更新，但 19310/19302 运行态未加载，或端口服务异常。",
        "动作": "停止自动施工，登记重载申请，等待总管确认。",
        "是否需总管确认": True,
        "是否允许自动复跑": False,
    },
    {
        "级别": "L4",
        "名称": "真实外部动作风险",
        "判定": "出现真实发送企业微信、触发 n8n、接券商、交易、登录税局、接财税软件、真实渲染或发布视频的迹象。",
        "动作": "立即停止，保留日志，标记红线风险，等待总管确认。",
        "是否需总管确认": True,
        "是否允许自动复跑": False,
    },
    {
        "级别": "L5",
        "名称": "正式规则或总管资产风险",
        "判定": "需要自动转正式规则、修改运行配置、修改总管面板或一键接续包。",
        "动作": "立即停止，只形成候选说明，不落正式变更。",
        "是否需总管确认": True,
        "是否允许自动复跑": False,
    },
]


CONFIRMATION_GATES: list[dict[str, Any]] = [
    {"编号": "SCG-001", "闸口": "19310 重载", "触发": "公共接入层服务需重新加载代码或端口异常", "确认前允许动作": "只读巡检、日志定位、重载申请单", "确认前禁止动作": "停止/启动 19310"},
    {"编号": "SCG-002", "闸口": "19302 重载", "触发": "股票桥接入口需重载或端口异常", "确认前允许动作": "端口状态读取、日志定位", "确认前禁止动作": "请求 19302 业务接口、停止/启动 19302"},
    {"编号": "SCG-003", "闸口": "企业微信真实发送", "触发": "real_send 可能变为 true 或需要发给联系人/群", "确认前允许动作": "本地 dry-run", "确认前禁止动作": "真实发送"},
    {"编号": "SCG-004", "闸口": "n8n 真实触发", "触发": "需要接入或触发 n8n 工作流", "确认前允许动作": "检查项可读、配置说明候选", "确认前禁止动作": "真实 webhook/工作流触发"},
    {"编号": "SCG-005", "闸口": "股票交易链路", "触发": "券商、交易、下单、仓位动作", "确认前允许动作": "研究分析和风险复核", "确认前禁止动作": "连接券商、下单、调仓"},
    {"编号": "SCG-006", "闸口": "税务真实账号链路", "触发": "电子税务局、财税软件、正式税务结论", "确认前允许动作": "待复核草案摘要、资料清单", "确认前禁止动作": "登录税局、接财税软件、正式结论"},
    {"编号": "SCG-007", "闸口": "视频真实渲染/发布", "触发": "MoneyPrinterTurbo/ImageMagick 可调用、视频文件生成、平台发布", "确认前允许动作": "预检和 blocked 状态检查", "确认前禁止动作": "真实渲染、上传、发布"},
    {"编号": "SCG-008", "闸口": "正式规则变更", "触发": "进化候选要转入正式规则或运行配置", "确认前允许动作": "候选包、只读验收建议", "确认前禁止动作": "写正式规则、改运行配置"},
    {"编号": "SCG-009", "闸口": "总管面板/一键接续包", "触发": "需要修改总管面板或一键接续包", "确认前允许动作": "候选说明、差异清单", "确认前禁止动作": "直接修改"},
]


AUTO_ACTION_MATRIX: list[dict[str, Any]] = [
    {"输入状态": "全部通过", "失败级别": "L0", "自动动作": "继续下一批低风险施工", "需汇报": "阶段包完成时汇报"},
    {"输入状态": "缺少候选产物", "失败级别": "L1", "自动动作": "重建候选产物并复跑验收", "需汇报": "不需要，除非复跑失败"},
    {"输入状态": "只读验收失败但不触红线", "失败级别": "L2", "自动动作": "最小修复或重新生成只读产物，复跑总回归", "需汇报": "阶段包完成时汇报"},
    {"输入状态": "服务运行态异常", "失败级别": "L3", "自动动作": "停止，生成重载申请", "需汇报": "立即汇报需总管确认"},
    {"输入状态": "真实外部动作风险", "失败级别": "L4", "自动动作": "停止，保留日志", "需汇报": "立即汇报红线"},
    {"输入状态": "正式规则/总管资产变更", "失败级别": "L5", "自动动作": "停止，只写候选说明", "需汇报": "立即汇报需总管确认"},
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "请求19302业务接口": False,
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_levels_md() -> str:
    rows = [
        f"| {item['级别']} | {item['名称']} | {item['是否需总管确认']} | {item['是否允许自动复跑']} | {item['动作']} |"
        for item in FAILURE_LEVELS
    ]
    return "\n".join(["# 失败分级规则", "", "| 级别 | 名称 | 需总管确认 | 允许自动复跑 | 动作 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_confirm_md() -> str:
    rows = [
        f"| {item['编号']} | {item['闸口']} | {item['触发']} | {item['确认前允许动作']} | {item['确认前禁止动作']} |"
        for item in CONFIRMATION_GATES
    ]
    return "\n".join(["# 需总管确认闸口清单", "", "| 编号 | 闸口 | 触发 | 确认前允许动作 | 确认前禁止动作 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_dispatch_md() -> str:
    rows = [
        f"| {item['输入状态']} | {item['失败级别']} | {item['自动动作']} | {item['需汇报']} |"
        for item in AUTO_ACTION_MATRIX
    ]
    return "\n".join(["# 失败后自动处置矩阵", "", "| 输入状态 | 失败级别 | 自动动作 | 需汇报 |", "| --- | --- | --- | --- |", *rows, ""])


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付失败自动分级与总管确认闸口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 失败分级：{len(report['失败分级规则'])} 级",
            f"- 需总管确认闸口：{len(report['需总管确认闸口'])} 项",
            f"- 自动处置矩阵：{len(report['失败后自动处置矩阵'])} 项",
            "",
            "## 输出文件",
            "",
            f"- 失败分级规则：{LEVELS_MD}",
            f"- 需总管确认闸口清单：{CONFIRM_MD}",
            f"- 失败后自动处置矩阵：{DISPATCH_MD}",
            "",
            "## 核心口径",
            "",
            "- L1/L2 可自动复跑或低风险续建。",
            "- L3/L4/L5 必须停止并汇报，不得继续施工。",
            "- 本包是稳定交付候选支撑资料，不是正式规则变更。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付失败自动分级与总管确认闸口包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_failure_gate_candidate_ready",
        "失败分级规则": FAILURE_LEVELS,
        "需总管确认闸口": CONFIRMATION_GATES,
        "失败后自动处置矩阵": AUTO_ACTION_MATRIX,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "失败分级规则": str(LEVELS_MD),
            "需总管确认闸口清单": str(CONFIRM_MD),
            "失败后自动处置矩阵": str(DISPATCH_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(LEVELS_MD, build_levels_md())
    write_text(CONFIRM_MD, build_confirm_md())
    write_text(DISPATCH_MD, build_dispatch_md())
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "失败分级": len(FAILURE_LEVELS), "确认闸口": len(CONFIRMATION_GATES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
