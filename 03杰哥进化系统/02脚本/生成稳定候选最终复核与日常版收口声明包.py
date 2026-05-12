# -*- coding: utf-8 -*-
"""生成稳定候选最终复核与日常版收口声明包。

只生成候选声明和只读复核资料，不正式封版，不修改运行配置或正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "62稳定候选最终复核与日常版收口声明包"
LATEST_JSON = OUTPUT_DIR / "稳定候选最终复核与日常版收口声明包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定候选最终复核与日常版收口声明包_最新.md"
DAILY_CLOSEOUT_MD = OUTPUT_DIR / "日常可用交付版收口声明_最新.md"
STABLE_REVIEW_MD = OUTPUT_DIR / "稳定版候选最终复核清单_最新.md"
BOUNDARY_MD = OUTPUT_DIR / "最终复核边界说明_最新.md"


REVIEW_EVIDENCE: list[dict[str, Any]] = [
    {
        "编号": "SFR-001",
        "名称": "日常可用交付版一键只读总回归",
        "路径": str(EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"),
        "收口口径": "11/11 通过，错误数=0。",
    },
    {
        "编号": "SFR-002",
        "名称": "自主巡检快照",
        "路径": str(EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"),
        "收口口径": "总体状态=pass，失败=0。",
    },
    {
        "编号": "SFR-003",
        "名称": "稳定版候选最终总索引与收口验收包",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版候选最终总索引与收口验收包验收" / "stable-candidate-final-master-index-closeout-verify-最新.json"),
        "收口口径": "最终总索引 13 项通过，错误数=0。",
    },
    {
        "编号": "SFR-004",
        "名称": "稳定版候选最终回传与可交付声明包",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定版候选最终回传与可交付声明包验收" / "stable-candidate-final-delivery-statement-verify-最新.json"),
        "收口口径": "可交付声明成立，核心证据失败=0。",
    },
    {
        "编号": "SFR-005",
        "名称": "稳定候选补强与三日巡检启动包",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定候选补强与三日巡检启动包验收" / "stable-candidate-hardening-three-day-patrol-verify-最新.json"),
        "收口口径": "首日样本通过，三日达标=false，未伪装长周期。",
    },
    {
        "编号": "SFR-006",
        "名称": "稳定候选异常样例库与演练包",
        "路径": str(EVOLUTION_ROOT / "04日志" / "稳定候选异常样例库与演练包验收" / "stable-candidate-exception-samples-drill-verify-最新.json"),
        "收口口径": "L1-L5 覆盖，演练失败=0。",
    },
]


DAILY_CLOSEOUT = {
    "声明级别": "日常可用交付版候选收口",
    "可用体验": [
        "企业微信公共入口可本地预演，职责分流可验。",
        "税收业务可输出待复核草案摘要。",
        "股票研究展示口径已去交易化。",
        "视频脚本、分镜、预检可走，真实渲染/发布仍阻断。",
        "智能进化可沉淀候选和只读验收，不转正式规则。",
    ],
    "仍需注意": [
        "这不是开放真实外部执行。",
        "19310/19302 重载仍需总管确认。",
        "n8n、券商、税局、财税软件、真实视频发布仍关闭。",
    ],
}


BOUNDARY_NOTES = [
    "日常版可以按候选收口使用，但不是法律、税务、交易、发布意义上的正式执行系统。",
    "稳定版候选可交付，但正式封版仍需总管确认。",
    "三日巡检目前只有首日样本，不能说长周期已经达标。",
    "后续施工只允许继续低风险候选包、只读验收、样本积累和文档交接增强。",
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
    "正式封版": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_daily_closeout_md(report: dict[str, Any]) -> str:
    data = report["日常版收口声明"]
    lines = ["# 日常可用交付版收口声明", "", f"- 声明级别：{data['声明级别']}", "", "## 可用体验", ""]
    lines.extend([f"- {item}" for item in data["可用体验"]])
    lines.extend(["", "## 仍需注意", ""])
    lines.extend([f"- {item}" for item in data["仍需注意"]])
    return "\n".join(lines)


def build_stable_review_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['编号']} | {item['名称']} | {item['收口口径']} | {item['路径']} |" for item in report["最终复核证据"]]
    return "\n".join(["# 稳定版候选最终复核清单", "", "| 编号 | 名称 | 收口口径 | 路径 |", "| --- | --- | --- | --- |", *rows, ""])


def build_boundary_md(report: dict[str, Any]) -> str:
    lines = ["# 最终复核边界说明", ""]
    lines.extend([f"- {item}" for item in report["边界说明"]])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定候选最终复核与日常版收口声明包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 最终复核证据：{len(report['最终复核证据'])}",
            f"- 边界说明：{len(report['边界说明'])}",
            "",
            "## 输出文件",
            "",
            f"- 日常可用交付版收口声明：{DAILY_CLOSEOUT_MD}",
            f"- 稳定版候选最终复核清单：{STABLE_REVIEW_MD}",
            f"- 最终复核边界说明：{BOUNDARY_MD}",
            "",
            "## 核心口径",
            "",
            "- 日常可用交付版可以候选收口。",
            "- 稳定版仍是候选可交付，不是正式封版。",
            "- 不修改正式规则、运行配置、总管面板或原一键接续包。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定候选最终复核与日常版收口声明包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_final_review_daily_closeout_ready",
        "最终复核证据": REVIEW_EVIDENCE,
        "日常版收口声明": DAILY_CLOSEOUT,
        "边界说明": BOUNDARY_NOTES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "日常可用交付版收口声明": str(DAILY_CLOSEOUT_MD),
            "稳定版候选最终复核清单": str(STABLE_REVIEW_MD),
            "最终复核边界说明": str(BOUNDARY_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(DAILY_CLOSEOUT_MD, build_daily_closeout_md(report))
    write_text(STABLE_REVIEW_MD, build_stable_review_md(report))
    write_text(BOUNDARY_MD, build_boundary_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "最终复核证据": len(REVIEW_EVIDENCE), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
