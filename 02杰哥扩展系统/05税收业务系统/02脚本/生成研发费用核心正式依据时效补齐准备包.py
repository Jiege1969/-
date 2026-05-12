# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
SOURCE_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.json"
OUT_JSON = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.json"
OUT_MD = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def task_type(slot: dict[str, Any]) -> str:
    status = slot.get("槽位状态", "")
    if status == "missing_local_evidence":
        return "缺本地证据卡"
    if status == "local_evidence_present_but_validity_missing":
        return "已有本地证据但时效缺失"
    if status == "query_candidate_only":
        return "仅有官方查询候选"
    if status == "evidence_ready_pending_human_validity":
        return "已有候选但仍需人工时效核验"
    return "待人工判定"


def build_task(slot: dict[str, Any]) -> dict[str, Any]:
    matched = slot.get("匹配证据", [])
    candidates = slot.get("官方查询候选", [])
    gaps = slot.get("缺口", [])
    kind = task_type(slot)
    action = "人工复核"
    if kind == "缺本地证据卡":
        action = "准备人工提供或后续受控下载的登记字段清单"
    elif kind == "已有本地证据但时效缺失":
        action = "人工核验官方来源和全文有效状态，不得自动放行"
    elif kind == "仅有官方查询候选":
        action = "保留候选清单，等待受控下载或人工提供原文后生成本地证据卡"
    elif kind == "已有候选但仍需人工时效核验":
        action = "复核上下位关系和适用期间，不能单独支撑业务结论"

    return {
        "槽位ID": slot.get("槽位ID"),
        "槽位名称": slot.get("槽位名称"),
        "期望依据层级": slot.get("期望依据层级"),
        "当前状态": slot.get("槽位状态"),
        "任务类型": kind,
        "补齐动作": action,
        "匹配证据数量": len(matched),
        "官方查询候选数量": len(candidates),
        "缺口": gaps,
        "候选资料": [
            {
                "标题": item.get("标题"),
                "文号": item.get("文号"),
                "文件时效": item.get("文件时效"),
                "来源链接": item.get("来源链接"),
                "是否当前适用依据候选": item.get("是否当前适用依据候选"),
                "阻断原因": item.get("阻断原因", []),
            }
            for item in matched
        ],
        "官方查询候选": [
            {
                "标题": item.get("标题"),
                "文号": item.get("文号"),
                "文件时效": item.get("文件时效"),
                "来源链接": item.get("来源链接"),
                "处理状态": item.get("处理状态"),
                "阻断原因": item.get("阻断原因", []),
            }
            for item in candidates
        ],
        "人工复核项": slot.get("人工复核项", []),
        "是否进入当前适用依据候选": bool(slot.get("是否进入当前适用依据候选")),
        "是否生成正式税务结论": False,
        "处理状态": "pending_review" if slot.get("缺口") or not slot.get("是否进入当前适用依据候选") else "evidence_ready_pending_review",
    }


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# 研发费用核心正式依据时效补齐准备包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 槽位数量：{report['槽位数量']}",
        f"- 待补齐槽位数量：{report['待补齐槽位数量']}",
        "",
        "## 补齐任务",
        "",
    ]
    for task in report["补齐任务"]:
        lines.extend([
            f"### {task['槽位名称']}",
            f"- 任务类型：{task['任务类型']}",
            f"- 补齐动作：{task['补齐动作']}",
            f"- 匹配证据数量：{task['匹配证据数量']}",
            f"- 官方查询候选数量：{task['官方查询候选数量']}",
            f"- 是否进入当前适用依据候选：{task['是否进入当前适用依据候选']}",
            f"- 处理状态：{task['处理状态']}",
            "",
        ])
    lines.extend(["## 下一步自动队列", ""])
    for item in report["下一步自动队列"]:
        lines.append(f"- {item['优先级']} {item['事项']}：{item['边界']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = load_json(SOURCE_JSON)
    slots = source.get("核心依据时效矩阵", [])
    tasks = [build_task(slot) for slot in slots]
    pending = [task for task in tasks if task["处理状态"] == "pending_review"]

    report = {
        "名称": "研发费用核心正式依据时效补齐准备包",
        "生成时间": now,
        "资产身份": "研发费用专题政策证据底座补齐准备包，不是税务结论库。",
        "来源文件": str(SOURCE_JSON),
        "结论": "完成，待补齐槽位已拆解为人工复核和受控补齐任务",
        "槽位数量": len(slots),
        "待补齐槽位数量": len(pending),
        "补齐任务": tasks,
        "下一步自动队列": [
            {
                "优先级": "L2",
                "事项": "税收研发费用加计扣除后续比例延续政策本地证据卡补齐准备",
                "原因": "核心时效缺口已经拆解，后续比例、延续和行业范围政策仍需形成本地证据卡准备包。",
                "是否可自动推进": True,
                "边界": "只基于现有官方查询候选和本地证据报告生成准备包；不联网、不下载、不生成正式税务结论。",
            }
        ],
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用模型推理": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report)
    print(json.dumps({"状态": "完成", "槽位数量": len(slots), "待补齐槽位数量": len(pending), "输出": str(OUT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
