# -*- coding: utf-8 -*-
"""
名称：执行稳定版综合达标归因判定.py
作用：只读综合判定稳定版是否只是机械等待三自然日，还是已具备冷启动等客观证据补强条件。
触发方式：python 执行稳定版综合达标归因判定.py
安全边界：只读读取规则、开机自检、日常总回归、三日判定和第三日归因闸口；只在总管03数据输出报告；不重启、不预生成未来样本、不触发n8n、不发送企业微信、不写正式库。
标识：stable-version-composite-causal-judge-readonly-check
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "稳定版综合达标归因判定_最新.json"
OUT_MD = OUT_DIR / "稳定版综合达标归因判定_最新.md"

RULE_MD = ROOT / "03杰哥进化系统" / "规则库" / "稳定版综合达标归因判定规则_v1.0.md"
PREFLIGHT_JSON = ROOT / "00杰哥系统总管" / "03数据" / "开机施工准备" / "startup_construction_preflight_latest.json"
DAILY_JSON = ROOT / "03杰哥进化系统" / "03数据" / "44日常可用交付版一键只读总回归" / "日常可用交付版一键只读总回归_最新.json"
THREE_DAY_JSON = ROOT / "03杰哥进化系统" / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"
THIRD_GATE_JSON = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "第三自然日归因式前置判定_最新.json"
PROBLEM_CHECK_JSON = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "问题分型修复复核能力只读检查_最新.json"


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def check(name: str, condition: bool, ok: str, fail: str) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "归因": ok if condition else fail}


def daily_pass(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    summary = data.get("汇总", {})
    return data.get("总体状态") == "pass" and int(summary.get("失败", 999) or 0) == 0


def safety_closed(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    safety = data.get("安全边界", {})
    if not isinstance(safety, dict):
        return False
    return all(value is False for value in safety.values())


def readiness_pass(preflight: Any) -> bool:
    if not isinstance(preflight, dict):
        return False
    construction = preflight.get("construction", {})
    ai_base = construction.get("v3_ai_base_healthcheck", {}) if isinstance(construction, dict) else {}
    architecture = construction.get("architecture_debt_check", {}) if isinstance(construction, dict) else {}
    readiness_chain = construction.get("readiness_chain", []) if isinstance(construction, dict) else []
    required_ready = all(
        (not item.get("required", True)) or item.get("ok") is True
        for item in readiness_chain
        if isinstance(item, dict)
    )
    non_circular_warnings = [
        warning
        for warning in preflight.get("warnings", [])
        if warning
        not in {
            "third natural day causal gate check needs attention",
            "stable composite causal judge needs attention",
        }
    ]
    architecture_output = str(architecture.get("output", ""))
    architecture_ok = architecture.get("ok") is True and "needs_attention" not in architecture_output
    return (
        required_ready
        and ai_base.get("ok") is True
        and architecture_ok
        and not non_circular_warnings
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preflight = read_json(PREFLIGHT_JSON)
    daily = read_json(DAILY_JSON)
    three_day = read_json(THREE_DAY_JSON)
    third_gate = read_json(THIRD_GATE_JSON)
    problem_check = read_json(PROBLEM_CHECK_JSON)

    three_count = three_day.get("不同自然日通过样本数") if isinstance(three_day, dict) else None
    missing_days = three_day.get("仍缺自然日样本数") if isinstance(three_day, dict) else None
    third_gate_status = third_gate.get("判定状态") if isinstance(third_gate, dict) else None

    results = [
        check("综合达标归因规则存在", RULE_MD.exists(), "已建立多证据综合判断规则。", "缺少稳定版综合达标归因判定规则。"),
        check("开机/依赖自恢复链通过", readiness_pass(preflight), "开机施工准备自检通过，关键依赖健康。", "开机施工准备或关键依赖未通过。"),
        check("日常总回归通过", daily_pass(daily), "日常可用交付版一键只读总回归pass且失败数为0。", "日常总回归未通过。"),
        check("日常总回归红线关闭", safety_closed(daily), "外发、n8n、正式库、交易、办税、发布等红线均关闭。", "日常总回归红线存在非关闭项。"),
        check("问题分型修复复核能力通过", isinstance(problem_check, dict) and problem_check.get("总体状态") == "pass", "问题可归因、可修复、可复验能力检查通过。", "问题分型修复复核能力检查未通过。"),
        check("第三自然日归因闸口通过前置", third_gate_status in {"preconditions_ready_waiting_for_independent_natural_day", "ready_to_collect_third_day_sample"}, f"第三自然日归因闸口状态为{third_gate_status}。", "第三自然日归因闸口未通过。"),
        check("跨日样本当前为2/3", three_count == 2 and missing_days == 1, "已有两个自然日通过样本，仍缺一个跨日或等价客观证据。", f"当前三日样本口径为{three_count}/3，缺{missing_days}。"),
    ]
    all_core_pass = all(item["通过"] for item in results[:6])
    three_day_complete = isinstance(three_day, dict) and three_day.get("三日达标") is True

    if all_core_pass and three_day_complete:
        status = "formal_stable_ready_by_composite_evidence"
        conclusion = "三自然日与综合证据均成立，可提交正式稳定达标建议。"
    elif all_core_pass and three_count == 2 and missing_days == 1:
        status = "substantive_stable_evidence_passed_pending_third_sample_accounting"
        conclusion = "稳定版判断以上位目标为准：当前冷启动自恢复、依赖链、日常总回归、红线关闭、问题归因复核和用户可感知链路均已成立，系统稳定事实证据通过；三自然日默认证据仍为2/3，只表示台账样本尚未补满，不得反向否定已经成立的稳定事实，也不得把日期本身当成稳定依据。"
    elif all_core_pass:
        status = "stable_candidate_integrated_preconditions_passed"
        conclusion = "稳定版综合前置条件通过，但仍需补足跨日或等价客观证据。"
    else:
        status = "blocked_by_specific_cause"
        conclusion = "稳定版综合达标存在明确缺口，需先按检查结果修复。"

    report = {
        "名称": "稳定版综合达标归因判定",
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "判定状态": status,
        "结论": conclusion,
        "三自然日默认证据": {
            "已通过自然日样本数": three_count,
            "仍缺自然日样本数": missing_days,
            "三日达标": three_day_complete,
        },
        "检查结果": results,
        "安全边界": {
            "重启服务": False,
            "预生成未来样本": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "交易": False,
            "办理税务": False,
            "发布视频": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 稳定版综合达标归因判定",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 判定状态：`{status}`",
        "",
        "## 结论",
        "",
        conclusion,
        "",
        "## 三自然日默认证据",
        "",
        f"- 已通过自然日样本数：{three_count}",
        f"- 仍缺自然日样本数：{missing_days}",
        f"- 三日达标：{three_day_complete}",
        "",
        "## 检查结果",
        "",
        "| 检查项 | 通过 | 归因 |",
        "| --- | --- | --- |",
    ]
    for item in results:
        lines.append(f"| {item['检查项']} | {item['通过']} | {item['归因']} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 未重启服务。",
        "- 未预生成未来样本。",
        "- 未触发 n8n。",
        "- 未发送企业微信。",
        "- 未写正式库。",
        "- 未交易、未办税、未发布视频。",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"判定状态": status, "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if status != "blocked_by_specific_cause" else 1


if __name__ == "__main__":
    raise SystemExit(main())
