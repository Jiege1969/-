# -*- coding: utf-8 -*-
"""生成稳定版候选正式封版申请草案与最终交付封面收紧包。

本脚本只生成“正式封版申请草案”和交付封面收紧材料，不执行正式封版，
不修改运行配置，不触发任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "71稳定版候选正式封版申请草案与最终交付封面收紧包"

LATEST_JSON = OUTPUT_DIR / "稳定版候选正式封版申请草案与最终交付封面收紧包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版候选正式封版申请草案与最终交付封面收紧包_最新.md"
CONDITIONS_MD = OUTPUT_DIR / "正式封版申请条件_最新.md"
EVIDENCE_MD = OUTPUT_DIR / "当前证据清单_最新.md"
CONFIRM_MD = OUTPUT_DIR / "仍需总管确认项_最新.md"
PROHIBITED_MD = OUTPUT_DIR / "禁止自动执行项_最新.md"
COVER_MD = OUTPUT_DIR / "使用者交付封面简版_最新.md"


SOURCE_FILES = [
    {
        "编号": "SRC-001",
        "名称": "稳定版最后收口封面",
        "类别": "最后收口封面",
        "路径": str(EVOLUTION_ROOT / "03数据" / "67稳定版最后收口总回传与候选交付封面包" / "稳定版最后收口总回传与候选交付封面包_最新.json"),
        "期望状态字段": "状态",
        "期望状态值": "stable_final_closeout_cover_ready",
    },
    {
        "编号": "SRC-002",
        "名称": "稳定候选最终复核",
        "类别": "最终复核",
        "路径": str(EVOLUTION_ROOT / "03数据" / "62稳定候选最终复核与日常版收口声明包" / "稳定候选最终复核与日常版收口声明包_最新.json"),
        "期望状态字段": "状态",
        "期望状态值": "stable_candidate_final_review_daily_closeout_ready",
    },
    {
        "编号": "SRC-003",
        "名称": "第二轮并行合并验收",
        "类别": "并行合并验收",
        "路径": str(EVOLUTION_ROOT / "04日志" / "第二轮并行施工调度索引与合并验收准备包验收" / "parallel-round2-dispatch-merge-prepare-verify-最新.json"),
        "期望状态字段": "通过",
        "期望状态值": True,
    },
    {
        "编号": "SRC-004",
        "名称": "自主巡检快照",
        "类别": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "期望状态字段": "总体状态",
        "期望状态值": "pass",
    },
]


APPLICATION_CONDITIONS = [
    "只读证据齐全：最后收口封面、最终复核、第二轮并行合并验收、自主巡检快照均可读取且达成候选口径。",
    "错误数为 0：验证日志与只读核对汇总不得出现错误项。",
    "红线动作全部关闭：企业微信真实发送、n8n 触发、券商/交易、税局/财税软件、真实视频渲染/发布、服务重载均保持 false。",
    "仍由总管确认：本包只能提交正式封版申请草案，不自动转正式封版、不自动转正式规则。",
    "交付封面收紧：面向使用者只保留可读、可交接、可复核的简明封面，不夸大成长周期稳定或真实外部执行能力。",
]


CONFIRMATION_ITEMS = [
    "是否允许把当前稳定版候选提交进入正式封版评审流程。",
    "是否接受当前长周期样本仍不足、三日巡检仍需继续补样的风险说明。",
    "是否继续保持 19310/19302 不重载，所有服务配置不改动。",
    "是否继续禁止真实外部动作，直到单项红线评审另行通过。",
    "是否允许后续 worker 只围绕只读验收、证据补样、交付说明继续收紧。",
]


PROHIBITED_ACTIONS = {
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
    "正式封版": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "请求19302业务接口": False,
}


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_summary(source: dict[str, Any]) -> dict[str, Any]:
    path = Path(source["路径"])
    data = read_json_if_exists(path)
    status_field = source["期望状态字段"]
    actual = data.get(status_field)
    summary: dict[str, Any] = {
        "编号": source["编号"],
        "名称": source["名称"],
        "类别": source["类别"],
        "路径": source["路径"],
        "存在": path.exists(),
        "期望状态字段": status_field,
        "期望状态值": source["期望状态值"],
        "实际状态值": actual,
        "通过": path.exists() and actual == source["期望状态值"],
    }
    if source["名称"] == "自主巡检快照":
        summary["摘要"] = data.get("汇总", {})
    elif source["名称"] == "第二轮并行合并验收":
        summary["摘要"] = data.get("指标", {})
    else:
        summary["摘要"] = {
            "生成时间": data.get("生成时间"),
            "当前结论": data.get("当前结论"),
            "安全边界": data.get("安全边界", {}),
        }
    return summary


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_conditions_md(report: dict[str, Any]) -> str:
    lines = ["# 正式封版申请条件", ""]
    lines.extend(f"- {item}" for item in report["申请条件"])
    lines.extend(["", "## 草案性质", "", "- 本包是正式封版申请草案，不是正式封版结果。"])
    return "\n".join(lines)


def build_evidence_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {item['存在']} | {item['通过']} | {item['实际状态值']} | {item['路径']} |"
        for item in report["当前证据"]
    ]
    return "\n".join(
        [
            "# 当前证据清单",
            "",
            "| 编号 | 名称 | 存在 | 通过 | 实际状态 | 路径 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def build_confirm_md(report: dict[str, Any]) -> str:
    lines = ["# 仍需总管确认项", ""]
    lines.extend(f"- {item}" for item in report["仍需总管确认项"])
    return "\n".join(lines)


def build_prohibited_md(report: dict[str, Any]) -> str:
    rows = [f"| {name} | {value} |" for name, value in report["禁止自动执行项"].items()]
    return "\n".join(["# 禁止自动执行项", "", "| 项目 | 当前允许状态 |", "| --- | --- |", *rows, ""])


def build_cover_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 使用者交付封面简版",
            "",
            "## 当前可用",
            "",
            "- 可阅读稳定版候选交付封面、证据清单与最终复核结果。",
            "- 可做只读核对、交接说明、异常定位和下一轮低风险补样。",
            "- 可作为提交总管审批的正式封版申请草案材料。",
            "",
            "## 当前不可用",
            "",
            "- 不代表正式封版已经完成。",
            "- 不开放企业微信真实发送、n8n 触发、券商/交易、税局/财税软件、真实视频渲染或发布。",
            "- 不重载 19310/19302，不修改服务配置、总管面板或一键接续包。",
            "",
            f"生成时间：{report['生成时间']}",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版候选正式封版申请草案与最终交付封面收紧包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 草案性质：{report['草案性质']}",
            f"- 当前证据：{report['指标']['证据总数']} 项，已通过 {report['指标']['证据通过']} 项。",
            f"- 禁止自动执行项：{report['指标']['禁止自动执行项']} 项，全部保持 false。",
            "",
            "## 输出文件",
            "",
            f"- 申请条件：{CONDITIONS_MD}",
            f"- 当前证据清单：{EVIDENCE_MD}",
            f"- 仍需总管确认项：{CONFIRM_MD}",
            f"- 禁止自动执行项：{PROHIBITED_MD}",
            f"- 使用者交付封面简版：{COVER_MD}",
            "",
            "## 封面收紧口径",
            "",
            "- 可以提交申请草案，不可以宣称正式封版已完成。",
            "- 可以交付只读证据入口，不可以暗示真实外部动作已开放。",
            "- 可以继续补样和复核，不可以自动转正式规则。",
            "",
        ]
    )


def main() -> int:
    evidence = [source_summary(item) for item in SOURCE_FILES]
    report = {
        "名称": "稳定版候选正式封版申请草案与最终交付封面收紧包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "formal_freeze_request_draft_ready",
        "草案性质": "正式封版申请草案，不是正式封版",
        "申请条件": APPLICATION_CONDITIONS,
        "当前证据": evidence,
        "仍需总管确认项": CONFIRMATION_ITEMS,
        "禁止自动执行项": PROHIBITED_ACTIONS,
        "使用者交付封面简版": {
            "可用": ["阅读", "交接", "只读核对", "异常定位", "提交总管审批草案"],
            "不可用": ["正式封版", "真实外部动作", "服务重载", "配置修改", "自动转正式规则"],
        },
        "指标": {
            "证据总数": len(evidence),
            "证据通过": sum(1 for item in evidence if item["通过"]),
            "禁止自动执行项": len(PROHIBITED_ACTIONS),
            "需总管确认项": len(CONFIRMATION_ITEMS),
        },
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "申请条件": str(CONDITIONS_MD),
            "当前证据清单": str(EVIDENCE_MD),
            "仍需总管确认项": str(CONFIRM_MD),
            "禁止自动执行项": str(PROHIBITED_MD),
            "使用者交付封面简版": str(COVER_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(CONDITIONS_MD, build_conditions_md(report))
    write_text(EVIDENCE_MD, build_evidence_md(report))
    write_text(CONFIRM_MD, build_confirm_md(report))
    write_text(PROHIBITED_MD, build_prohibited_md(report))
    write_text(COVER_MD, build_cover_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "证据通过": report["指标"]["证据通过"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
