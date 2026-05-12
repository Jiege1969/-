# -*- coding: utf-8 -*-
"""生成稳定交付日常运行台账与交接验收包。

只生成稳定交付支撑资料和候选台账模板，不修改运行服务或正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包"
LATEST_JSON = OUTPUT_DIR / "稳定交付日常运行台账与交接验收包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付日常运行台账与交接验收包_最新.md"
LEDGER_MD = OUTPUT_DIR / "日常运行台账模板_最新.md"
HANDOFF_MD = OUTPUT_DIR / "交接验收清单_最新.md"
DAILY_RUNBOOK_MD = OUTPUT_DIR / "日常运行检查手册_最新.md"
ISSUE_LEDGER_MD = OUTPUT_DIR / "异常记录台账模板_最新.md"


DAILY_CHECKS: list[dict[str, Any]] = [
    {
        "编号": "SDC-001",
        "检查项": "企业微信公共入口日常巡检",
        "频率": "每日/改动后",
        "验收产物": str(ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json"),
        "通过口径": "总体状态=pass，real_send=false，触发n8n=false。",
        "失败处理": "按 SRL-001/SRL-002/SRL-004 定位；需重载 19310 时登记总管确认。",
    },
    {
        "编号": "SDC-002",
        "检查项": "股票展示口径一致性",
        "频率": "每日/股票前台产物刷新后",
        "验收产物": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "246展示口径修复" / "股票展示口径一致性验收_最新.json"),
        "通过口径": "通过=true，错误=0，无推荐/回避冲突和交易化表达残留。",
        "失败处理": "只修展示层，不改评分引擎和推荐名单生成逻辑。",
    },
    {
        "编号": "SDC-003",
        "检查项": "股票低风险基础资产影子验收",
        "频率": "候选资产刷新后",
        "验收产物": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "245L3评分基础资产" / "股票线第九批统一影子验收总表验收结果_最新.json"),
        "通过口径": "passed=true，failed_count=0，real_system_triggered=false。",
        "失败处理": "只回到候选卡和影子验收，不接券商、不交易。",
    },
    {
        "编号": "SDC-004",
        "检查项": "视频状态摘要与真实渲染禁用态",
        "频率": "每日/视频任务更新后",
        "验收产物": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "04日志" / "video-production-system-status-summary-verify-最新.json"),
        "通过口径": "状态摘要验收失败=0；真实渲染和发布仍保持 blocked。",
        "失败处理": "只做预检和复核卡；不得真实渲染/发布。",
    },
    {
        "编号": "SDC-005",
        "检查项": "日常可用交付版一键只读总回归",
        "频率": "每日收尾/阶段包完成后",
        "验收产物": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "通过口径": "通过=true，错误数=0，总数=11，失败=0。",
        "失败处理": "按失败自动分级进入 L1/L2 自动复跑，L3-L5 停止并汇报。",
    },
    {
        "编号": "SDC-006",
        "检查项": "自主巡检快照",
        "频率": "阶段包完成后",
        "验收产物": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "通过口径": "总体状态=pass，失败=0。",
        "失败处理": "先看缺失项，再复跑对应只读验收。",
    },
]


HANDOFF_CHECKS: list[dict[str, Any]] = [
    {"编号": "SHC-001", "交接项": "当前能力边界", "必须说明": "哪些可用、哪些 blocked、哪些需总管确认。"},
    {"编号": "SHC-002", "交接项": "最近一次总回归", "必须说明": "总数、通过、失败、验收日志路径。"},
    {"编号": "SHC-003", "交接项": "19310/19302 状态", "必须说明": "是否只是读取状态，是否存在重载申请。"},
    {"编号": "SHC-004", "交接项": "股票展示口径", "必须说明": "是否仍无交易化表达和推荐/回避冲突。"},
    {"编号": "SHC-005", "交接项": "税收输出口径", "必须说明": "是否仍为待复核草案摘要，不出正式税务结论。"},
    {"编号": "SHC-006", "交接项": "视频渲染/发布", "必须说明": "真实渲染和真实发布是否仍被阻断。"},
    {"编号": "SHC-007", "交接项": "进化候选", "必须说明": "候选未转正式规则，正式变更需确认。"},
    {"编号": "SHC-008", "交接项": "下一步施工", "必须说明": "只允许低风险候选包、只读验收或展示层修复继续自主施工。"},
]


ISSUE_FIELDS = [
    "记录时间",
    "发现入口",
    "影响业务线",
    "失败级别 L0-L5",
    "现象",
    "已查看日志",
    "是否触红线",
    "是否需总管确认",
    "已执行只读复跑",
    "处理结果",
    "下一步",
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


def build_ledger_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['检查项']} | {item['频率']} | 待填写 | 待填写 |" for item in report["日常检查项"]]
    return "\n".join(["# 日常运行台账模板", "", "| 编号 | 检查项 | 频率 | 今日结果 | 备注 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_handoff_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['交接项']} | {item['必须说明']} | 待填写 |" for item in report["交接验收项"]]
    return "\n".join(["# 交接验收清单", "", "| 编号 | 交接项 | 必须说明 | 交接结论 |", "| --- | --- | --- | --- |", *rows, ""])


def build_runbook_md(report: dict[str, Any]) -> str:
    lines = ["# 日常运行检查手册", "", "按顺序执行，只读优先；任何红线立即停止。", ""]
    for item in report["日常检查项"]:
        lines.extend(
            [
                f"## {item['编号']} {item['检查项']}",
                "",
                f"- 频率：{item['频率']}",
                f"- 验收产物：{item['验收产物']}",
                f"- 通过口径：{item['通过口径']}",
                f"- 失败处理：{item['失败处理']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_issue_ledger_md(report: dict[str, Any]) -> str:
    header = "| " + " | ".join(report["异常记录字段"]) + " |"
    sep = "| " + " | ".join(["---"] * len(report["异常记录字段"])) + " |"
    blank = "| " + " | ".join(["待填写"] * len(report["异常记录字段"])) + " |"
    return "\n".join(["# 异常记录台账模板", "", header, sep, blank, ""])


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付日常运行台账与交接验收包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 日常检查项：{len(report['日常检查项'])}",
            f"- 交接验收项：{len(report['交接验收项'])}",
            f"- 异常记录字段：{len(report['异常记录字段'])}",
            "",
            "## 输出文件",
            "",
            f"- 日常运行台账模板：{LEDGER_MD}",
            f"- 交接验收清单：{HANDOFF_MD}",
            f"- 日常运行检查手册：{DAILY_RUNBOOK_MD}",
            f"- 异常记录台账模板：{ISSUE_LEDGER_MD}",
            "",
            "## 核心口径",
            "",
            "- 日常运行只看只读验收和 blocked 状态，不触发真实外部动作。",
            "- 交接时必须说明可用能力、阻断能力、红线和下一步边界。",
            "- 异常记录必须标明失败级别和是否需总管确认。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定交付日常运行台账与交接验收包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_daily_ledger_handoff_candidate_ready",
        "日常检查项": DAILY_CHECKS,
        "交接验收项": HANDOFF_CHECKS,
        "异常记录字段": ISSUE_FIELDS,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "日常运行台账模板": str(LEDGER_MD),
            "交接验收清单": str(HANDOFF_MD),
            "日常运行检查手册": str(DAILY_RUNBOOK_MD),
            "异常记录台账模板": str(ISSUE_LEDGER_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(LEDGER_MD, build_ledger_md(report))
    write_text(HANDOFF_MD, build_handoff_md(report))
    write_text(DAILY_RUNBOOK_MD, build_runbook_md(report))
    write_text(ISSUE_LEDGER_MD, build_issue_ledger_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "日常检查项": len(DAILY_CHECKS), "交接验收项": len(HANDOFF_CHECKS), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
