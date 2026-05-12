# -*- coding: utf-8 -*-
"""生成稳定版候选最终总索引与收口验收包。

本包只形成稳定版候选收口资料，不正式封版，不修改运行配置/总管面板/一键接续包。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包"
LATEST_JSON = OUTPUT_DIR / "稳定版候选最终总索引与收口验收包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版候选最终总索引与收口验收包_最新.md"
MASTER_INDEX_MD = OUTPUT_DIR / "稳定版候选最终总索引_最新.md"
CLOSEOUT_MD = OUTPUT_DIR / "稳定版候选收口验收清单_最新.md"
READ_ME_MD = OUTPUT_DIR / "稳定版候选交付阅读入口_最新.md"


FINAL_PACKAGES: list[dict[str, Any]] = [
    {
        "编号": "SFC-001",
        "阶段": "日常可用收口",
        "名称": "最终日常可用交付候选回传",
        "路径": str(EVOLUTION_ROOT / "03数据" / "48最终日常可用交付候选回传" / "最终日常可用交付候选回传_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "最终日常可用交付候选回传验收" / "final-daily-usable-delivery-candidate-verify-最新.json"),
    },
    {
        "编号": "SFC-002",
        "阶段": "异常恢复",
        "名称": "稳定交付异常恢复与日志索引包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "49稳定交付异常恢复与日志索引包" / "稳定交付异常恢复与日志索引包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付异常恢复与日志索引包验收" / "stable-delivery-recovery-log-index-verify-最新.json"),
    },
    {
        "编号": "SFC-003",
        "阶段": "复跑续建",
        "名称": "稳定交付异常复跑队列与低风险自动续建包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包" / "稳定交付异常复跑队列与低风险自动续建包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付异常复跑队列与低风险自动续建包验收" / "stable-delivery-rerun-rebuild-package-verify-最新.json"),
    },
    {
        "编号": "SFC-004",
        "阶段": "确认闸口",
        "名称": "稳定交付失败自动分级与总管确认闸口包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "51稳定交付失败自动分级与总管确认闸口包" / "稳定交付失败自动分级与总管确认闸口包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付失败自动分级与总管确认闸口包验收" / "stable-delivery-failure-gate-package-verify-最新.json"),
    },
    {
        "编号": "SFC-005",
        "阶段": "日常运行",
        "名称": "稳定交付日常运行台账与交接验收包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包" / "稳定交付日常运行台账与交接验收包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付日常运行台账与交接验收包验收" / "stable-delivery-daily-ledger-handoff-package-verify-最新.json"),
    },
    {
        "编号": "SFC-006",
        "阶段": "证据冻结候选",
        "名称": "稳定交付跨业务回归证据链与版本冻结候选包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "53稳定交付跨业务回归证据链与版本冻结候选包" / "稳定交付跨业务回归证据链与版本冻结候选包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付跨业务回归证据链与版本冻结候选包验收" / "stable-delivery-evidence-freeze-candidate-verify-最新.json"),
    },
    {
        "编号": "SFC-007",
        "阶段": "封版候选",
        "名称": "稳定版封版候选总验收与剩余缺口清单",
        "路径": str(EVOLUTION_ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收与剩余缺口清单_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定版封版候选总验收与剩余缺口清单验收" / "stable-release-freeze-candidate-acceptance-verify-最新.json"),
    },
    {
        "编号": "SFC-008",
        "阶段": "趋势样本",
        "名称": "稳定交付长周期只读巡检样本与趋势记录包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "55稳定交付长周期只读巡检样本与趋势记录包" / "稳定交付长周期只读巡检样本与趋势记录包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付长周期只读巡检样本与趋势记录包验收" / "stable-delivery-long-term-patrol-trend-verify-最新.json"),
    },
    {
        "编号": "SFC-009",
        "阶段": "使用者交付",
        "名称": "稳定交付使用者交付摘要与非技术操作手册包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "56稳定交付使用者交付摘要与非技术操作手册包" / "稳定交付使用者交付摘要与非技术操作手册包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定交付使用者交付摘要与非技术操作手册包验收" / "stable-delivery-user-handoff-manual-verify-最新.json"),
    },
    {
        "编号": "SFC-010",
        "阶段": "最终索引",
        "名称": "稳定版最终候选索引与接续包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "57稳定版最终候选索引与接续包" / "稳定版最终候选索引与接续包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定版最终候选索引与接续包验收" / "stable-final-candidate-index-continue-verify-最新.json"),
    },
    {
        "编号": "SFC-011",
        "阶段": "可交付声明",
        "名称": "稳定版候选最终回传与可交付声明包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "58稳定版候选最终回传与可交付声明包" / "稳定版候选最终回传与可交付声明包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定版候选最终回传与可交付声明包验收" / "stable-candidate-final-delivery-statement-verify-最新.json"),
    },
    {
        "编号": "SFC-012",
        "阶段": "三日巡检启动",
        "名称": "稳定候选补强与三日巡检启动包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "稳定候选补强与三日巡检启动包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定候选补强与三日巡检启动包验收" / "stable-candidate-hardening-three-day-patrol-verify-最新.json"),
    },
    {
        "编号": "SFC-013",
        "阶段": "异常演练",
        "名称": "稳定候选异常样例库与演练包",
        "路径": str(EVOLUTION_ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例库与演练包_最新.md"),
        "验收": str(EVOLUTION_ROOT / "04日志" / "稳定候选异常样例库与演练包验收" / "stable-candidate-exception-samples-drill-verify-最新.json"),
    },
]


CLOSEOUT_CHECKS = [
    "所有稳定候选阶段包 Markdown 存在。",
    "所有稳定候选阶段包验收 JSON 存在且通过。",
    "一键只读总回归仍通过。",
    "自主巡检快照仍通过。",
    "红线全部保持 false。",
    "三日巡检首日样本已记录，但不伪装三日达标。",
    "稳定版候选可交付声明成立，但不是正式封版。",
]


READING_ENTRY = [
    "先读：稳定版候选可交付声明_最新.md",
    "再读：稳定版候选最终总索引_最新.md",
    "再读：稳定版封版候选总验收与剩余缺口清单_最新.md",
    "遇到故障读：异常恢复手册_最新.md 与 稳定候选异常样例库_最新.md",
    "交接给非技术使用者读：使用者交付摘要_最新.md 与 非技术操作手册_最新.md",
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


def build_master_index_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['阶段']} | {item['名称']} | {item['路径']} | {item['验收']} |"
        for item in report["最终总索引"]
    ]
    return "\n".join(["# 稳定版候选最终总索引", "", "| 编号 | 阶段 | 名称 | 资料路径 | 验收路径 |", "| --- | --- | --- | --- | --- |", *rows, ""])


def build_closeout_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定版候选收口验收清单", ""]
    lines.extend([f"- {item}" for item in report["收口验收项"]])
    return "\n".join(lines)


def build_readme_md(report: dict[str, Any]) -> str:
    lines = ["# 稳定版候选交付阅读入口", ""]
    lines.extend([f"{index}. {item}" for index, item in enumerate(report["阅读入口"], start=1)])
    return "\n".join(lines)


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版候选最终总索引与收口验收包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 最终总索引：{len(report['最终总索引'])}",
            f"- 收口验收项：{len(report['收口验收项'])}",
            "",
            "## 输出文件",
            "",
            f"- 稳定版候选最终总索引：{MASTER_INDEX_MD}",
            f"- 稳定版候选收口验收清单：{CLOSEOUT_MD}",
            f"- 稳定版候选交付阅读入口：{READ_ME_MD}",
            "",
            "## 核心口径",
            "",
            "- 稳定版候选已经形成最终总索引。",
            "- 本包仍是候选收口，不是正式封版。",
            "- 不修改正式规则、运行配置、总管面板或原一键接续包。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定版候选最终总索引与收口验收包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_final_master_index_closeout_ready",
        "最终总索引": FINAL_PACKAGES,
        "收口验收项": CLOSEOUT_CHECKS,
        "阅读入口": READING_ENTRY,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "稳定版候选最终总索引": str(MASTER_INDEX_MD),
            "稳定版候选收口验收清单": str(CLOSEOUT_MD),
            "稳定版候选交付阅读入口": str(READ_ME_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(MASTER_INDEX_MD, build_master_index_md(report))
    write_text(CLOSEOUT_MD, build_closeout_md(report))
    write_text(READ_ME_MD, build_readme_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "最终总索引": len(FINAL_PACKAGES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
