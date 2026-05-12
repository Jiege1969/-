# -*- coding: utf-8 -*-
"""
生成本轮三线并行回收收口报告。

作用：
- 自动读取 01智能、02扩展、03进化 三条线固定回收报告。
- 自动判断是否仍待执行、是否存在高风险动作、是否存在明显文件冲突。
- 生成 00总管本轮三线回收报告，供后续进度重算和总体汇总读取。

安全边界：
- 只读三线回收报告。
- 只写 00总管并行回收目录和运行状态目录。
- 不重新执行子系统业务脚本，不发企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE_DIR = MANAGER / "03数据" / "运行状态"
RECOVERY_DIR = MANAGER / "03数据" / "并行回收"

REPORTS = {
    "01智能系统": RECOVERY_DIR / "01智能系统_本轮回收报告_最新.md",
    "02扩展系统": RECOVERY_DIR / "02扩展系统_本轮回收报告_最新.md",
    "03进化系统": RECOVERY_DIR / "03进化系统_本轮回收报告_最新.md",
}

MANAGER_REPORT_JSON = RECOVERY_DIR / "00总管_本轮三线回收报告_最新.json"
MANAGER_REPORT_MD = RECOVERY_DIR / "00总管_本轮三线回收报告_最新.md"
STATE_REPORT_JSON = STATE_DIR / "本轮三线并行回收收口报告_最新.json"
STATE_REPORT_MD = STATE_DIR / "本轮三线并行回收收口报告_最新.md"
INTELLIGENCE_BLOCKER_REVIEW = STATE_DIR / "00总管_01智能系统阻断项复核_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def section_value(text: str, title: str) -> str:
    pattern = rf"【{re.escape(title)}】\s*(.*?)(?=\n【|\Z)"
    match = re.search(pattern, text, re.S)
    if not match:
        return ""
    return match.group(1).strip()


def parse_report(system: str, path: Path) -> dict[str, Any]:
    text = read_text(path)
    pending = (not text) or "状态：待执行" in text or "通过 0/0" in text
    high_risk_value = section_value(text, "高风险动作确认")
    high_risk = "：是" in high_risk_value or ":是" in high_risk_value or "真实发送：是" in high_risk_value
    modified = section_value(text, "修改文件")
    added = section_value(text, "新增文件")
    validation = section_value(text, "验收结果")
    validation_counts = parse_validation_counts(validation)
    progress = section_value(text, "进度影响建议")
    conflict_risk = section_value(text, "冲突风险")
    return {
        "系统": system,
        "路径": str(path),
        "存在": path.exists(),
        "待执行": pending,
        "高风险动作": high_risk,
        "高风险动作说明": high_risk_value,
        "新增文件": extract_paths(added),
        "修改文件": extract_paths(modified),
        "验收结果": validation,
        "验收计数": validation_counts,
        "验收失败数": validation_counts.get("失败", 0),
        "验收阻断项": validation_counts.get("阻断项", 0),
        "进度影响建议": progress,
        "冲突风险": conflict_risk,
        "文本长度": len(text),
    }


def parse_validation_counts(text: str) -> dict[str, int]:
    result = {"通过": 0, "总数": 0, "失败": 0, "阻断项": 0}
    if not text:
        return result
    passed = re.search(r"通过\s*(\d+)\s*/\s*(\d+)", text)
    failed = re.search(r"失败\s*(\d+)", text)
    blockers = re.search(r"阻断项\s*(\d+)", text)
    if passed:
        result["通过"] = int(passed.group(1))
        result["总数"] = int(passed.group(2))
    if failed:
        result["失败"] = int(failed.group(1))
    if blockers:
        result["阻断项"] = int(blockers.group(1))
    return result


def extract_paths(text: str) -> list[str]:
    if not text:
        return []
    candidates: list[str] = []
    for raw in re.split(r"[\n,，;；]+", text):
        item = raw.strip().strip("-").strip()
        if not item:
            continue
        if "D:/" in item or "D:\\" in item or item.endswith((".md", ".json", ".py", ".txt")):
            candidates.append(item.replace("\\", "/"))
    return candidates


def find_file_conflicts(parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    owners: dict[str, list[str]] = {}
    for item in parsed:
        for path in item["修改文件"]:
            owners.setdefault(path, []).append(item["系统"])
    conflicts = []
    for path, systems in owners.items():
        if len(set(systems)) > 1:
            conflicts.append({"文件": path, "系统": sorted(set(systems))})
    return conflicts


def reviewed_validation_blockers(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    review_text = read_text(INTELLIGENCE_BLOCKER_REVIEW)
    reviewed: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for item in items:
        if (
            item.get("系统") == "01智能系统"
            and "不是交付失败阻断" in review_text
            and "不需要退回 01 修复" in review_text
        ):
            copied = dict(item)
            copied["复核结论"] = "阻断项为安全阻断用例计数，已由00总管复核为非交付失败阻断"
            reviewed.append(copied)
        else:
            unresolved.append(item)
    return reviewed, unresolved


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 00总管 本轮三线并行回收收口报告",
        f"生成时间：{report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 三线是否全部完成：{report['三线是否全部完成']}",
        f"- 阻断数量：{report['阻断数量']}",
        f"- 文件冲突数量：{len(report['文件冲突'])}",
        f"- 高风险动作数量：{len(report['高风险动作'])}",
        "",
        "## 三线状态",
    ]
    for item in report["三线状态"]:
        state = "待执行" if item["待执行"] else "已回收"
        risk = "有高风险" if item["高风险动作"] else "无高风险"
        validation = item.get("验收计数", {})
        lines.append(
            f"- {item['系统']}：{state}；{risk}；验收失败 {validation.get('失败', 0)}；"
            f"阻断项 {validation.get('阻断项', 0)}；报告：`{item['路径']}`"
        )
    lines.extend(["", "## 文件冲突"])
    if report["文件冲突"]:
        for item in report["文件冲突"]:
            lines.append(f"- {item['文件']}：{', '.join(item['系统'])}")
    else:
        lines.append("- 未发现多个施工框同时修改同一文件。")
    lines.extend(["", "## 高风险动作"])
    if report["高风险动作"]:
        for item in report["高风险动作"]:
            lines.append(f"- {item['系统']}：{item['高风险动作说明']}")
    else:
        lines.append("- 未发现企业微信真实发送、n8n、券商接口、自动交易或正式库写入被打开。")
    lines.extend(["", "## 验收失败和阻断项"])
    if report["未解决验收阻断"]:
        for item in report["未解决验收阻断"]:
            lines.append(f"- {item['系统']}：失败 {item['验收失败数']}；阻断项 {item['验收阻断项']}；验收结果 `{item['验收结果']}`")
    else:
        lines.append("- 未发现未解决的验收失败或非零阻断项。")
    if report["已复核验收阻断"]:
        lines.append("")
        lines.append("已复核为非失败阻断：")
        for item in report["已复核验收阻断"]:
            lines.append(f"- {item['系统']}：{item.get('复核结论', '')}")
    lines.extend(["", "## 进度处理建议", report["进度处理建议"], "", "## 下一步", report["下一步"], ""])
    return "\n".join(lines)


def main() -> int:
    parsed = [parse_report(system, path) for system, path in REPORTS.items()]
    pending = [item for item in parsed if item["待执行"]]
    high_risk = [item for item in parsed if item["高风险动作"]]
    file_conflicts = find_file_conflicts(parsed)
    validation_blockers = [item for item in parsed if item.get("验收失败数", 0) > 0 or item.get("验收阻断项", 0) > 0]
    reviewed_blockers, unresolved_validation_blockers = reviewed_validation_blockers(validation_blockers)
    blockers = len(pending) + len(high_risk) + len(file_conflicts) + len(unresolved_validation_blockers)
    all_done = not pending

    if pending:
        conclusion = "待子系统完成"
        progress_advice = "三条线尚未全部写入有效回收报告，本轮不调整全盘进度和剩余工时。"
        next_step = "等待01智能、02扩展、03进化写入固定回收报告后，再重新运行本脚本。"
    elif high_risk or file_conflicts or unresolved_validation_blockers:
        conclusion = "需阻断复核"
        progress_advice = "发现高风险动作、文件冲突、验收失败或非零阻断项，本轮不进入总体汇总，不直接调整进度。"
        next_step = "先由00总管复核阻断项性质：若为后续待办则登记为下一轮任务；若为交付阻断则退回对应子系统修复。处理完成后再重跑总管回收。"
    else:
        conclusion = "可进入进度重算"
        progress_advice = "三线回收报告均已写入且未发现阻断，可进入总管进度重算、接续包刷新和总体汇总。"
        next_step = "运行总管进度重算与接续包刷新；随后生成总体系统阶段汇总。"

    report = {
        "名称": "00总管本轮三线并行回收收口报告",
        "生成时间": now_text(),
        "结论": conclusion,
        "三线是否全部完成": all_done,
        "阻断数量": blockers,
        "三线状态": parsed,
        "待执行": pending,
        "文件冲突": file_conflicts,
        "高风险动作": high_risk,
        "验收阻断": validation_blockers,
        "已复核验收阻断": reviewed_blockers,
        "未解决验收阻断": unresolved_validation_blockers,
        "进度处理建议": progress_advice,
        "下一步": next_step,
        "安全边界": {
            "重新执行子系统业务脚本": False,
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    write_json(MANAGER_REPORT_JSON, report)
    write_text(MANAGER_REPORT_MD, build_markdown(report))
    write_json(STATE_REPORT_JSON, report)
    write_text(STATE_REPORT_MD, build_markdown(report))
    print(json.dumps({"状态": conclusion, "三线是否全部完成": all_done, "阻断数量": blockers}, ensure_ascii=False))
    return 0 if conclusion != "需冲突处理" else 1


if __name__ == "__main__":
    raise SystemExit(main())
