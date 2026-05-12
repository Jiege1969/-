# -*- coding: utf-8 -*-
"""
名称：执行第三自然日归因式前置判定.py
作用：只读判定第三自然日样本不是机械等日期，而是按前置样本、失败归因、复验证据、红线和自然日独立性共同判断。
触发方式：python 执行第三自然日归因式前置判定.py
安全边界：只读读取台账、回执、自检、总回归和规则；只在总管03数据输出报告；不预生成未来样本、不触发n8n、不发送企业微信、不写正式库、不重启服务。
标识：third-natural-day-causal-gate-readonly-check
"""

from __future__ import annotations

import json
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "第三自然日归因式前置判定_最新.json"
OUT_MD = OUT_DIR / "第三自然日归因式前置判定_最新.md"

RULE_MD = ROOT / "03杰哥进化系统" / "规则库" / "自然日样本归因式判定规则_v1.0.md"
LEDGER_JSON = ROOT / "03杰哥进化系统" / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
JUDGE_JSON = ROOT / "03杰哥进化系统" / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"
PREFLIGHT_JSON = ROOT / "00杰哥系统总管" / "03数据" / "开机施工准备" / "startup_construction_preflight_latest.json"
DAILY_JSON = ROOT / "03杰哥进化系统" / "03数据" / "44日常可用交付版一键只读总回归" / "日常可用交付版一键只读总回归_最新.json"
FS06_ORIGINAL = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "FS_06_第二自然日样本执行回执_20260509_未入账.json"
FS06_REVIEW = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "FS_06_第二自然日同日修复后复核入账回执_20260509.json"
DUR001_FIX = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "DUR001_职责分流受控修复回执_20260509.json"
THIRD_CARD = ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "20260510_正式稳定第三自然日执行指令卡.md"

EARLIEST_THIRD_DAY = date(2026, 5, 10)
TRUSTED_TIME_URLS = [
    "https://www.microsoft.com",
    "https://www.baidu.com",
    "https://www.cloudflare.com",
]


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def check(condition: bool, name: str, ok_detail: str, fail_detail: str) -> dict[str, Any]:
    return {
        "检查项": name,
        "通过": bool(condition),
        "归因": ok_detail if condition else fail_detail,
    }


def trusted_time_evidence() -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    dates: list[str] = []
    for url in TRUSTED_TIME_URLS:
        item: dict[str, Any] = {"url": url, "ok": False}
        try:
            req = Request(url, method="HEAD", headers={"User-Agent": "jiege-stability-time-check/1.0"})
            with urlopen(req, timeout=5) as resp:
                header = resp.headers.get("Date")
            if header:
                dt = parsedate_to_datetime(header).astimezone(ZoneInfo("Asia/Shanghai"))
                item.update({"ok": True, "date_header": header, "asia_shanghai_date": dt.date().isoformat()})
                dates.append(dt.date().isoformat())
            else:
                item["error"] = "missing Date header"
        except Exception as exc:
            item["error"] = str(exc)
        evidence.append(item)

    consensus = None
    if dates:
        consensus = max(set(dates), key=dates.count)
    return {"consensus_date": consensus, "sources": evidence}


def natural_day_time_gate(local_today: date) -> dict[str, Any]:
    evidence = trusted_time_evidence()
    trusted_date_text = evidence.get("consensus_date")
    trusted_date = date.fromisoformat(trusted_date_text) if trusted_date_text else None
    if local_today < EARLIEST_THIRD_DAY:
        ok = True
        reason = "本机日期尚未达到第三自然日，不允许入账；此时可信时间源只作参考，不作放行条件。"
    elif trusted_date is None:
        ok = False
        reason = "本机日期已达到或声称达到第三自然日，但缺少可信外部时间证据，不能仅凭可手工修改的系统时间入账。"
    elif trusted_date != local_today:
        ok = False
        reason = f"本机日期为{local_today.isoformat()}，可信时间为{trusted_date.isoformat()}，存在时间一致性风险。"
    else:
        ok = True
        reason = "本机日期与可信外部时间一致，可进入第三自然日独立性判断。"
    return {
        "ok": ok,
        "reason": reason,
        "local_date": local_today.isoformat(),
        "trusted_date": trusted_date.isoformat() if trusted_date else None,
        "evidence": evidence,
    }


def daily_status_is_pass(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    return data.get("总体状态") == "pass" and int(data.get("失败", 0) or 0) == 0


def preflight_core_pass(preflight: Any) -> bool:
    if not isinstance(preflight, dict):
        return False
    construction = preflight.get("construction", {})
    if not isinstance(construction, dict):
        return False
    ai_base = construction.get("v3_ai_base_healthcheck", {})
    architecture = construction.get("architecture_debt_check", {})
    readiness_chain = construction.get("readiness_chain", [])
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
        and isinstance(ai_base, dict)
        and ai_base.get("ok") is True
        and isinstance(architecture, dict)
        and architecture_ok
        and not non_circular_warnings
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today()
    ledger = read_json(LEDGER_JSON)
    judge = read_json(JUDGE_JSON)
    preflight = read_json(PREFLIGHT_JSON)
    daily = read_json(DAILY_JSON)
    fs06_review_text = read_text(FS06_REVIEW)
    third_card_text = read_text(THIRD_CARD)
    time_gate = natural_day_time_gate(today)

    samples = ledger.get("自然日样本", []) if isinstance(ledger, dict) else []
    passed_dates = sorted({
        item.get("样本日期")
        for item in samples
        if isinstance(item, dict) and item.get("当日状态") == "pass" and item.get("样本日期")
    })

    preconditions = [
        check(RULE_MD.exists(), "归因式判定规则存在", "规则已建立，日期不是唯一闸口。", "缺少自然日样本归因式判定规则。"),
        check(passed_dates == ["2026-05-08", "2026-05-09"], "前两个自然日样本存在", "已存在2026-05-08和2026-05-09两个通过样本。", f"当前通过样本为{passed_dates}。"),
        check(FS06_ORIGINAL.exists() and FS06_REVIEW.exists() and DUR001_FIX.exists(), "第二自然日事实双账完整", "原始失败、同日复核、修复回执均存在。", "第二自然日原始失败、复核或修复回执缺失。"),
        check("P1-B" in fs06_review_text and "同日修复后复核入账" in fs06_review_text, "第二自然日归因成立", "DUR-001已归因为P1-B局部职责/路由缺口并同日复核入账。", "第二自然日P1-B归因或同日复核入账证据不足。"),
        check(preflight_core_pass(preflight), "开机施工准备自检通过", "开机核心依赖链、架构旧债、智能底座均通过，不再被稳定/三日判定自身循环阻断。", "开机核心依赖链或架构旧债检查未通过。"),
        check(time_gate["ok"], "自然日时间可信性通过", time_gate["reason"], time_gate["reason"]),
        check(daily_status_is_pass(daily), "日常可用总回归通过", "日常可用交付版一键只读总回归为pass且失败数为0。", "日常可用交付版一键只读总回归未通过。"),
        check(isinstance(judge, dict) and judge.get("不同自然日通过样本数") == 2 and judge.get("仍缺自然日样本数") == 1, "三日判定口径一致", "当前为2/3，仍缺1个真实自然日样本。", "三日判定结果与2/3、缺1口径不一致。"),
        check("红线" in third_card_text and "失败处理" in third_card_text, "第三日执行卡包含红线与失败处理", "第三日执行卡要求红线扫描和失败归因处理。", "第三日执行卡缺少红线或失败处理口径。"),
    ]

    preconditions_ok = all(item["通过"] for item in preconditions)
    basis_date = date.fromisoformat(time_gate["trusted_date"]) if time_gate.get("trusted_date") else today
    independent_day_ok = bool(time_gate["ok"]) and basis_date >= EARLIEST_THIRD_DAY

    if preconditions_ok and independent_day_ok:
        decision = "ready_to_collect_third_day_sample"
        conclusion = "前置归因条件和自然日独立性均满足，可进入第三自然日只读样本采集。"
    elif preconditions_ok and not independent_day_ok:
        decision = "preconditions_ready_waiting_for_independent_natural_day"
        conclusion = "前置归因条件已满足；当前不能入账的原因不是空等，而是第三个独立自然日尚未到。今天可确认前置链路，明天仍需开机自检、总回归、红线和失败归因复验。"
    else:
        decision = "blocked_by_cause"
        conclusion = "第三自然日样本前置条件存在明确缺口，必须先按归因修复或补证。"

    report = {
        "名称": "第三自然日归因式前置判定",
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "当前日期": today.isoformat(),
        "可信时间判定": time_gate,
        "最早第三自然日": EARLIEST_THIRD_DAY.isoformat(),
        "自然日独立性满足": independent_day_ok,
        "前置归因条件满足": preconditions_ok,
        "判定状态": decision,
        "结论": conclusion,
        "检查结果": preconditions,
        "安全边界": {
            "预生成未来样本": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "重启服务": False,
            "交易": False,
            "办理税务": False,
            "发布视频": False,
        },
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 第三自然日归因式前置判定",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前日期：{report['当前日期']}",
        f"- 可信时间日期：{time_gate.get('trusted_date')}",
        f"- 可信时间判定：{time_gate.get('ok')}，{time_gate.get('reason')}",
        f"- 最早第三自然日：{report['最早第三自然日']}",
        f"- 自然日独立性满足：{report['自然日独立性满足']}",
        f"- 前置归因条件满足：{report['前置归因条件满足']}",
        f"- 判定状态：`{report['判定状态']}`",
        "",
        "## 结论",
        "",
        report["结论"],
        "",
        "## 检查结果",
        "",
        "| 检查项 | 通过 | 归因 |",
        "| --- | --- | --- |",
    ]
    for item in preconditions:
        lines.append(f"| {item['检查项']} | {item['通过']} | {item['归因']} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 未预生成未来样本。",
        "- 未触发 n8n。",
        "- 未发送企业微信。",
        "- 未写正式库。",
        "- 未重启服务。",
        "- 未交易、未办税、未发布视频。",
    ])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"判定状态": decision, "前置归因条件满足": preconditions_ok, "自然日独立性满足": independent_day_ok, "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if preconditions_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
