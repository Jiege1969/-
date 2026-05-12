# -*- coding: utf-8 -*-
"""生成稳定交付异常恢复与日志索引包。

安全边界：只扫描本地日志与既有验收产物，写入 03杰哥进化系统 的候选资料。
不请求业务接口，不重载 19310/19302，不触发企业微信/n8n/券商/税局/视频发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "49稳定交付异常恢复与日志索引包"
LATEST_JSON = OUTPUT_DIR / "稳定交付异常恢复与日志索引包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付异常恢复与日志索引包_最新.md"
LOG_INDEX_MD = OUTPUT_DIR / "关键日志索引_最新.md"
FAILURE_CARD_MD = OUTPUT_DIR / "失败定位卡_最新.md"
RECOVERY_GUIDE_MD = OUTPUT_DIR / "异常恢复手册_最新.md"
RELOAD_TEMPLATE_MD = OUTPUT_DIR / "19310_19302重载需总管确认申请单_最新.md"


COMPONENTS = [
    {
        "组件": "企业微信公共接入层",
        "职责": "19310、/health、工作秘书/系统管家/视频助理职责分流、本地 dry-run。",
        "目录": [
            ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "04日志",
            ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包",
        ],
    },
    {
        "组件": "税收业务新入口",
        "职责": "工作秘书税收原始文本传入新入口，输出待复核草案摘要。",
        "目录": [
            ROOT / "02杰哥扩展系统" / "05税收业务系统" / "03数据",
            ROOT / "02杰哥扩展系统" / "05税收业务系统" / "04日志",
            ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包",
        ],
    },
    {
        "组件": "股票研究前台展示",
        "职责": "前台口径一致性、交易化表达扫雷、低风险影子验收。",
        "目录": [
            ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "246展示口径修复",
            ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "245L3评分基础资产",
        ],
    },
    {
        "组件": "视频制作与发布预检",
        "职责": "脚本/分镜/人工回执、真实渲染禁用态、发布预检阻断。",
        "目录": [
            ROOT / "02杰哥扩展系统" / "02视频制作系统" / "04日志",
            ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核",
            ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "08本地整理门禁",
        ],
    },
    {
        "组件": "智能进化候选层",
        "职责": "只读验收、候选经验、封版候选、总回归和状态包。",
        "目录": [
            EVOLUTION_ROOT / "04日志",
            EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照",
            EVOLUTION_ROOT / "03数据" / "44日常可用交付版一键只读总回归",
            EVOLUTION_ROOT / "03数据" / "48最终日常可用交付候选回传",
        ],
    },
]


FAILURE_CARDS = [
    {
        "编号": "SRL-001",
        "现象": "19310 不在线或 /health 异常",
        "先看日志": ["wecom-unified-local-service.pid", "wecom-unified-local-service.stdout.log", "wecom-unified-local-service.stderr.log", "企业微信公共接入层日常只读巡检_最新.json"],
        "判断口径": "只做端口和健康检查定位；重载必须登记为需总管确认。",
        "禁止动作": ["不得自行重载 19310", "不得真实发送企业微信"],
    },
    {
        "编号": "SRL-002",
        "现象": "工作秘书税收回复回到旧标题或旧事项",
        "先看日志": ["企业微信公共接入层日常只读巡检_最新.json", "wecom-unified-command-local-service-最新.json", "税收企业微信正式入口消息预演输出"],
        "判断口径": "优先确认公共层是否把原始文本传给税收新入口；不改税收判断逻辑。",
        "禁止动作": ["不得生成正式税务结论", "不得登录电子税务局", "不得接财税软件"],
    },
    {
        "编号": "SRL-003",
        "现象": "税收新入口 stdout/JSON 编码异常",
        "先看日志": ["wecom-unified-local-service.stderr.log", "税收新入口生成的 Markdown 结果路径", "企业微信统一指令本地调用预演规则.json"],
        "判断口径": "优先读取新入口固定产物，并登记下次重载 UTF-8 环境适配；当前服务不二次重载。",
        "禁止动作": ["不得绕过公共层直接改税收业务结论"],
    },
    {
        "编号": "SRL-004",
        "现象": "系统管家/工作秘书直接回答股票问题",
        "先看日志": ["企业微信公共接入层日常只读巡检_最新.json", "wecom-multi-assistant-route-shadow-plan-verify-最新.json"],
        "判断口径": "这是职责分流问题，归公共接入层路由；不请求 19302 股票业务接口。",
        "禁止动作": ["不得接券商", "不得交易", "不得请求 19302 业务接口做排障"],
    },
    {
        "编号": "SRL-005",
        "现象": "股票前台再次出现推荐词和回避/风险复核并存",
        "先看日志": ["股票展示口径一致性验收_最新.json", "股票前台展示口径全量一致性扫雷_最新.json"],
        "判断口径": "只修前台展示产物或展示生成层，不改评分引擎和推荐名单生成逻辑。",
        "禁止动作": ["不得生成买卖指令", "不得修改核心评分引擎"],
    },
    {
        "编号": "SRL-006",
        "现象": "股票报告残留加仓/减仓/仓位等交易化表达",
        "先看日志": ["股票前台展示口径全量一致性扫雷_最新.json", "03数据\\246展示口径修复"],
        "判断口径": "归展示层措辞扫雷；当前系统只给研究价值和风险复核。",
        "禁止动作": ["不得接券商", "不得交易"],
    },
    {
        "编号": "SRL-007",
        "现象": "视频真实渲染预检从 blocked 变成 pass",
        "先看日志": ["视频真实渲染禁用态检查_最新.json", "adapter-moneyprinter-run-最新.json", "视频真实渲染环境识别与放行前检查回传_20260508.md"],
        "判断口径": "MoneyPrinterTurbo/ImageMagick 未识别前必须保持阻断；不得伪造接入。",
        "禁止动作": ["不得调用 MoneyPrinterTurbo", "不得真实渲染视频"],
    },
    {
        "编号": "SRL-008",
        "现象": "视频发布预检未放行却可发布",
        "先看日志": ["publisher-run-最新.json", "视频任务ID与放行链一致性复核卡_最新.json"],
        "判断口径": "未视频文件、未发布清单、未人工放行时必须 blocked。",
        "禁止动作": ["不得上传", "不得自动发布视频", "不得接 n8n 发布链"],
    },
    {
        "编号": "SRL-009",
        "现象": "进化候选验收通过后被误当成正式规则",
        "先看日志": ["阶段性多业务联调通过封版候选回传_最新.md", "multi-business-integration-passed-freeze-candidate-verify-最新.json"],
        "判断口径": "进化系统只能形成候选；正式规则变更必须总管确认。",
        "禁止动作": ["不得自动转正式规则", "不得修改运行配置"],
    },
    {
        "编号": "SRL-010",
        "现象": "一键只读总回归失败",
        "先看日志": ["日常可用交付版一键只读总回归_最新.json", "daily-usable-readonly-regression-verify-最新.json"],
        "判断口径": "先定位失败任务所属业务线，再只做对应低风险修复；不要扩大到服务重载。",
        "禁止动作": ["不得重载 19310/19302", "不得真实调用外部系统"],
    },
    {
        "编号": "SRL-011",
        "现象": "19302 状态异常或被误请求",
        "先看日志": ["企业微信公共接入层日常只读巡检_最新.json", "股票桥接入口 PID 记录"],
        "判断口径": "日常巡检只允许读取端口状态，不请求股票业务接口。",
        "禁止动作": ["不得触碰券商接口", "不得交易", "不得自行重载 19302"],
    },
]


RECOVERY_STEPS = [
    {"步骤": "确认异常归属", "动作": "按现象匹配失败定位卡，先分到公共接入、税收、股票、视频或进化候选层。"},
    {"步骤": "读取最近验收", "动作": "优先看 *_最新.json 和 *_最新.md，确认是当前失败还是历史旧产物。"},
    {"步骤": "复跑只读脚本", "动作": "只允许复跑已登记的一键只读总回归、日常巡检、展示口径验收、视频禁用态检查等脚本。"},
    {"步骤": "锁定最小边界", "动作": "公共层只改路由/传参；股票只改展示；税收不出正式结论；视频不进真实渲染/发布；进化只写候选。"},
    {"步骤": "登记红线", "动作": "一旦涉及重载、正式规则、真实发送、真实发布或外部账号，立即停止并登记需总管确认。"},
    {"步骤": "形成回传", "动作": "修复或定位后写明修改范围、验收命令、通过/未通过、下一步阻断项。"},
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


def collect_files(paths: list[Path], limit: int = 14) -> list[dict[str, Any]]:
    found: list[Path] = []
    for base in paths:
        if base.is_file():
            found.append(base)
        elif base.exists():
            for pattern in ("*.json", "*.md", "*.log", "*.pid"):
                found.extend(base.rglob(pattern))
    unique = sorted(set(found), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    files = []
    for item in unique[:limit]:
        stat = item.stat()
        files.append(
            {
                "路径": str(item),
                "文件名": item.name,
                "大小": stat.st_size,
                "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return files


def build_log_index() -> list[dict[str, Any]]:
    index = []
    for component in COMPONENTS:
        files = collect_files(component["目录"])
        index.append(
            {
                "组件": component["组件"],
                "职责": component["职责"],
                "目录": [str(path) for path in component["目录"]],
                "证据文件数": len(files),
                "最近证据": files,
            }
        )
    return index


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_log_index_md(report: dict[str, Any]) -> str:
    lines = ["# 关键日志索引", "", f"- 生成时间：{report['生成时间']}", ""]
    for item in report["关键日志索引"]:
        lines.extend([f"## {item['组件']}", "", f"- 职责：{item['职责']}", f"- 证据文件数：{item['证据文件数']}", ""])
        lines.extend(["| 文件 | 修改时间 | 路径 |", "| --- | --- | --- |"])
        for evidence in item["最近证据"]:
            lines.append(f"| {evidence['文件名']} | {evidence['修改时间']} | {evidence['路径']} |")
        lines.append("")
    return "\n".join(lines)


def build_failure_card_md(report: dict[str, Any]) -> str:
    lines = ["# 失败定位卡", "", "只用于定位和分派修复边界，不授权真实外部动作。", ""]
    for card in report["失败定位卡"]:
        lines.extend(
            [
                f"## {card['编号']} {card['现象']}",
                "",
                f"- 先看日志：{'; '.join(card['先看日志'])}",
                f"- 判断口径：{card['判断口径']}",
                f"- 禁止动作：{'; '.join(card['禁止动作'])}",
                "",
            ]
        )
    return "\n".join(lines)


def build_recovery_guide_md(report: dict[str, Any]) -> str:
    lines = ["# 异常恢复手册", "", "原则：先只读定位，再最小修复；凡触碰红线，停止并登记需总管确认。", ""]
    lines.extend(["| 顺序 | 步骤 | 动作 |", "| --- | --- | --- |"])
    for idx, step in enumerate(report["异常恢复步骤"], start=1):
        lines.append(f"| {idx} | {step['步骤']} | {step['动作']} |")
    lines.extend(["", "## 红线", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines)


def build_reload_template_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 19310/19302 重载需总管确认申请单",
            "",
            "只有出现服务代码已改但运行中服务未加载、端口异常且只读定位无法恢复时，才填写本申请。",
            "",
            "- 申请时间：",
            "- 申请端口：19310 / 19302（二选一）",
            "- 当前 PID：",
            "- 入口脚本：",
            "- 触发原因：",
            "- 已查看日志：",
            "- 已执行只读验收：",
            "- 预计影响：",
            "- 明确不做：不真实发送企业微信、不触发 n8n、不接券商、不交易、不登录税局、不接财税软件、不真实渲染/发布视频。",
            "- 总管确认结果：未确认 / 已确认",
            "",
            f"本模板生成于：{report['生成时间']}",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['组件']} | {item['证据文件数']} | {item['职责']} |"
        for item in report["关键日志索引"]
    ]
    return "\n".join(
        [
            "# 稳定交付异常恢复与日志索引包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 组件数：{len(report['关键日志索引'])}",
            f"- 失败定位卡：{len(report['失败定位卡'])}",
            f"- 异常恢复步骤：{len(report['异常恢复步骤'])}",
            "",
            "| 组件 | 证据文件数 | 职责 |",
            "| --- | --- | --- |",
            *rows,
            "",
            "## 输出文件",
            "",
            f"- 关键日志索引：{LOG_INDEX_MD}",
            f"- 失败定位卡：{FAILURE_CARD_MD}",
            f"- 异常恢复手册：{RECOVERY_GUIDE_MD}",
            f"- 重载确认申请单：{RELOAD_TEMPLATE_MD}",
            "",
            "## 安全边界",
            "",
            "- 本包不请求业务接口，不重载服务，不触发外部系统，只形成稳定交付支撑资料。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付异常恢复与日志索引包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_support_candidate_ready",
        "关键日志索引": build_log_index(),
        "失败定位卡": FAILURE_CARDS,
        "异常恢复步骤": RECOVERY_STEPS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "关键日志索引": str(LOG_INDEX_MD),
            "失败定位卡": str(FAILURE_CARD_MD),
            "异常恢复手册": str(RECOVERY_GUIDE_MD),
            "重载需总管确认申请单": str(RELOAD_TEMPLATE_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(LOG_INDEX_MD, build_log_index_md(report))
    write_text(FAILURE_CARD_MD, build_failure_card_md(report))
    write_text(RECOVERY_GUIDE_MD, build_recovery_guide_md(report))
    write_text(RELOAD_TEMPLATE_MD, build_reload_template_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "组件数": len(report["关键日志索引"]), "失败定位卡": len(report["失败定位卡"]), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
