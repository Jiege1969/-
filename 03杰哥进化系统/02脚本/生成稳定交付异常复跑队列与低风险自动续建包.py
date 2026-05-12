# -*- coding: utf-8 -*-
"""生成稳定交付异常复跑队列与低风险自动续建包。

本包只定义低风险复跑/续建边界和命令清单，不触发服务重载，不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包"
LATEST_JSON = OUTPUT_DIR / "稳定交付异常复跑队列与低风险自动续建包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付异常复跑队列与低风险自动续建包_最新.md"
QUEUE_JSON = OUTPUT_DIR / "异常复跑队列_最新.json"
QUEUE_MD = OUTPUT_DIR / "异常复跑队列_最新.md"
REBUILD_MD = OUTPUT_DIR / "低风险自动续建清单_最新.md"
BOUNDARY_MD = OUTPUT_DIR / "自动续建边界说明_最新.md"


def script_path(*parts: str) -> str:
    return str(ROOT.joinpath(*parts))


RERUN_QUEUE: list[dict[str, Any]] = [
    {
        "编号": "SRQ-001",
        "名称": "企业微信公共入口日常只读巡检",
        "触发条件": "19310 在线但总入口烟测、职责分流或税收三条任一异常。",
        "执行模式": "readonly_rerun",
        "脚本": script_path("02杰哥扩展系统", "00公共组件", "企业微信接入设置", "02脚本", "执行企业微信公共接入层日常只读巡检.py"),
        "工作目录": script_path("02杰哥扩展系统", "00公共组件", "企业微信接入设置"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "00公共组件", "企业微信接入设置", "03数据", "15日常可用版只读巡检包", "企业微信公共接入层日常只读巡检_最新.json"),
        "红线": ["不得真实发送企业微信", "不得触发 n8n", "不得自行重载 19310"],
    },
    {
        "编号": "SRQ-002",
        "名称": "股票展示口径一致性验收",
        "触发条件": "股票前台出现推荐词与回避/风险复核冲突，或旧交易化词残留。",
        "执行模式": "readonly_verify",
        "脚本": script_path("02杰哥扩展系统", "01股票研究系统", "02脚本", "验证股票展示口径一致性.py"),
        "工作目录": script_path("02杰哥扩展系统", "01股票研究系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "01股票研究系统", "03数据", "246展示口径修复", "股票展示口径一致性验收_最新.json"),
        "红线": ["不得接券商", "不得交易", "不得改核心评分引擎"],
    },
    {
        "编号": "SRQ-003",
        "名称": "股票第九批统一影子验收",
        "触发条件": "股票低风险基础资产候选卡、队列或统一验收总表被更新后。",
        "执行模式": "readonly_verify",
        "脚本": script_path("02杰哥扩展系统", "01股票研究系统", "02脚本", "验证股票线第九批统一影子验收总表.py"),
        "工作目录": script_path("02杰哥扩展系统", "01股票研究系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "01股票研究系统", "03数据", "245L3评分基础资产", "股票线第九批统一影子验收总表验收结果_最新.json"),
        "红线": ["不得接券商", "不得交易"],
    },
    {
        "编号": "SRQ-004",
        "名称": "视频制作系统状态摘要验收",
        "触发条件": "视频脚本、分镜、人工复核、放行预检状态发生变更。",
        "执行模式": "readonly_verify",
        "脚本": script_path("02杰哥扩展系统", "02视频制作系统", "02脚本", "验证视频制作系统状态摘要.py"),
        "工作目录": script_path("02杰哥扩展系统", "02视频制作系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "02视频制作系统", "04日志", "video-production-system-status-summary-verify-最新.json"),
        "红线": ["不得真实渲染", "不得自动发布"],
    },
    {
        "编号": "SRQ-005",
        "名称": "视频真实渲染禁用态检查",
        "触发条件": "MoneyPrinterTurbo 或 ImageMagick 环境口径发生变化。",
        "执行模式": "blocked_state_verify",
        "脚本": script_path("02杰哥扩展系统", "02视频制作系统", "02脚本", "执行视频真实渲染禁用态检查.py"),
        "工作目录": script_path("02杰哥扩展系统", "02视频制作系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "02视频制作系统", "03数据", "08本地整理门禁", "视频真实渲染禁用态检查_最新.json"),
        "红线": ["不得调用 MoneyPrinterTurbo", "不得调用 ImageMagick 真实渲染"],
    },
    {
        "编号": "SRQ-006",
        "名称": "视频 P0 人工回执影子样例验收",
        "触发条件": "视频 P0 人工确认样例、回执口径或影子样例变化。",
        "执行模式": "readonly_verify",
        "脚本": script_path("02杰哥扩展系统", "02视频制作系统", "02脚本", "验证视频P0人工回执影子样例.py"),
        "工作目录": script_path("02杰哥扩展系统", "02视频制作系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("02杰哥扩展系统", "02视频制作系统", "04日志", "video-p0-human-receipt-shadow-samples-verify-最新.json"),
        "红线": ["不得真实渲染", "不得上传发布"],
    },
    {
        "编号": "SRQ-007",
        "名称": "阶段性封版候选回归建议拆单验收",
        "触发条件": "进化候选、封版候选或回归建议拆单被补充。",
        "执行模式": "candidate_verify",
        "脚本": script_path("03杰哥进化系统", "02脚本", "验证阶段性封版候选回归建议拆单.py"),
        "工作目录": script_path("03杰哥进化系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("03杰哥进化系统", "04日志", "阶段性封版候选回归建议拆单验收", "freeze-candidate-regression-cards-verify-最新.json"),
        "红线": ["不得自动转正式规则", "不得修改运行配置"],
    },
    {
        "编号": "SRQ-008",
        "名称": "日常可用交付版状态包验收",
        "触发条件": "可用能力、阻断能力、后续回归卡或进度估计被刷新。",
        "执行模式": "candidate_verify",
        "脚本": script_path("03杰哥进化系统", "02脚本", "验证日常可用交付版状态包.py"),
        "工作目录": script_path("03杰哥进化系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("03杰哥进化系统", "04日志", "日常可用交付版状态包验收", "daily-usable-delivery-status-package-verify-最新.json"),
        "红线": ["不得写正式规则", "不得修改总管面板"],
    },
    {
        "编号": "SRQ-009",
        "名称": "日常可用交付版一键只读总回归",
        "触发条件": "任一业务线低风险产物更新后，需要总体验收兜底。",
        "执行模式": "readonly_regression",
        "脚本": script_path("03杰哥进化系统", "02脚本", "执行日常可用交付版一键只读总回归.py"),
        "工作目录": script_path("03杰哥进化系统"),
        "允许自动复跑": True,
        "允许低风险续建": False,
        "输出验收": script_path("03杰哥进化系统", "03数据", "44日常可用交付版一键只读总回归", "日常可用交付版一键只读总回归_最新.json"),
        "红线": ["不得重载 19310/19302", "不得请求 19302 业务接口"],
    },
]


LOW_RISK_REBUILD: list[dict[str, Any]] = [
    {
        "编号": "SLB-001",
        "名称": "进化候选类文档续建",
        "允许范围": "03杰哥进化系统/03数据 下的候选、状态、回归建议、只读验收建议。",
        "可自动": True,
        "前置条件": "只生成候选资料，不改正式规则和运行配置。",
    },
    {
        "编号": "SLB-002",
        "名称": "只读验收日志刷新",
        "允许范围": "04日志 下的验收 JSON/Markdown。",
        "可自动": True,
        "前置条件": "脚本不触发真实发送、真实发布、外部账号、服务重载。",
    },
    {
        "编号": "SLB-003",
        "名称": "股票前台展示口径扫雷",
        "允许范围": "股票研究系统前台展示产物和展示生成层。",
        "可自动": "需先命中展示残留问题",
        "前置条件": "不得改分析引擎、评分逻辑、推荐名单生成逻辑。",
    },
    {
        "编号": "SLB-004",
        "名称": "视频放行前检查卡刷新",
        "允许范围": "视频测试与审核资料、任务 ID 与放行链复核卡。",
        "可自动": True,
        "前置条件": "只做预检/复核卡，不进入真实渲染和真实发布。",
    },
    {
        "编号": "SLB-005",
        "名称": "企业微信公共入口只读巡检刷新",
        "允许范围": "公共接入层巡检报告与本地 dry-run 验收。",
        "可自动": True,
        "前置条件": "real_send=false，触发n8n=false；如需重载只登记需总管确认。",
    },
]


STOP_RULES = [
    "需要重载 19310 或 19302 时停止，登记需总管确认。",
    "需要真实发送企业微信、触发 n8n、登录外部账号或调用真实发布链时停止。",
    "需要接券商、交易、登录电子税务局、接财税软件时停止。",
    "需要把候选经验转成正式规则，或修改运行配置/总管面板/一键接续包时停止。",
    "任何脚本输出提示真实渲染或真实发布可进入时停止复核。",
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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_queue_md(queue: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['执行模式']} | {item['允许自动复跑']} | {item['触发条件']} |"
        for item in queue
    ]
    return "\n".join(["# 异常复跑队列", "", "| 编号 | 名称 | 执行模式 | 自动复跑 | 触发条件 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_rebuild_md(items: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['可自动']} | {item['允许范围']} | {item['前置条件']} |"
        for item in items
    ]
    return "\n".join(["# 低风险自动续建清单", "", "| 编号 | 名称 | 可自动 | 允许范围 | 前置条件 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_boundary_md(report: dict[str, Any]) -> str:
    lines = ["# 自动续建边界说明", "", "自动续建只覆盖低风险资料、候选、只读验收和前台展示层安全修复。", "", "## 停止规则", ""]
    lines.extend([f"- {rule}" for rule in report["停止规则"]])
    lines.extend(["", "## 安全边界", ""])
    lines.extend([f"- {key}：{value}" for key, value in report["安全边界"].items()])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付异常复跑队列与低风险自动续建包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 异常复跑队列：{len(report['异常复跑队列'])} 项",
            f"- 低风险自动续建清单：{len(report['低风险自动续建清单'])} 项",
            f"- 停止规则：{len(report['停止规则'])} 项",
            "",
            "## 输出文件",
            "",
            f"- 异常复跑队列：{QUEUE_MD}",
            f"- 低风险自动续建清单：{REBUILD_MD}",
            f"- 自动续建边界说明：{BOUNDARY_MD}",
            "",
            "## 核心口径",
            "",
            "- 可自动复跑的是只读巡检、只读验收、候选验收和 blocked 状态检查。",
            "- 可低风险续建的是候选资料、验收日志、前台展示层安全口径和视频放行前检查卡。",
            "- 任何服务重载、真实外部动作、正式规则变更都停止并汇报。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付异常复跑队列与低风险自动续建包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_rerun_rebuild_candidate_ready",
        "异常复跑队列": RERUN_QUEUE,
        "低风险自动续建清单": LOW_RISK_REBUILD,
        "停止规则": STOP_RULES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "异常复跑队列JSON": str(QUEUE_JSON),
            "异常复跑队列Markdown": str(QUEUE_MD),
            "低风险自动续建清单": str(REBUILD_MD),
            "自动续建边界说明": str(BOUNDARY_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_json(QUEUE_JSON, RERUN_QUEUE)
    write_text(QUEUE_MD, build_queue_md(RERUN_QUEUE))
    write_text(REBUILD_MD, build_rebuild_md(LOW_RISK_REBUILD))
    write_text(BOUNDARY_MD, build_boundary_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "复跑队列": len(RERUN_QUEUE), "续建清单": len(LOW_RISK_REBUILD), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
