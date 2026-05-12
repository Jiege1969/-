# -*- coding: utf-8 -*-
"""生成稳定交付版三日达标判定器与样本采集标准包。

只读取现有三日巡检样本台账和防伪包，给出当前是否达标、缺口和采集标准；
不生成第2/3自然日样本，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包"

LATEST_JSON = OUTPUT_DIR / "稳定交付版三日达标判定器与样本采集标准包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付版三日达标判定器与样本采集标准包_最新.md"
STANDARD_JSON = OUTPUT_DIR / "稳定版自然日样本采集标准_最新.json"
STANDARD_MD = OUTPUT_DIR / "稳定版自然日样本采集标准_最新.md"
DECISION_JSON = OUTPUT_DIR / "稳定版三日达标判定结果_最新.json"
DECISION_MD = OUTPUT_DIR / "稳定版三日达标判定结果_最新.md"

SAMPLE_LEDGER = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
ANTI_FAKE_VERIFY = EVOLUTION_ROOT / "04日志" / "三日巡检样本防伪与次日待执行卡包验收" / "three-day-patrol-anti-fake-nextday-card-verify-最新.json"
DAY2_GATE_VERIFY = EVOLUTION_ROOT / "04日志" / "稳定交付版次日复验待执行闸口包验收" / "stable-delivery-day2-recheck-pending-gate-verify-最新.json"
DAY1_RECHECK_VERIFY = EVOLUTION_ROOT / "04日志" / "稳定交付版首日复验执行与问题回收包验收" / "stable-delivery-day1-recheck-issue-intake-verify-最新.json"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "预生成第2自然日样本": False,
    "预生成第3自然日样本": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_date(text: str) -> datetime:
    return datetime.strptime(text[:10], "%Y-%m-%d")


def unique_pass_dates(samples: list[dict[str, Any]]) -> list[str]:
    dates = sorted({item.get("样本日期", "") for item in samples if item.get("样本日期") and item.get("当日状态") == "pass"})
    return dates


def build_standard() -> dict[str, Any]:
    return {
        "名称": "稳定版自然日样本采集标准",
        "标准": [
            "必须是 3 个不同自然日样本，同一天重复运行只能覆盖同日样本。",
            "每个自然日样本必须来自只读巡检或只读复验结果，失败数必须为 0。",
            "样本日期不得早于实际系统日期，不得预生成第2/3自然日样本。",
            "任一红线动作、服务未确认重载、正式规则自动写入，均判定三日达标失败。",
            "三日达标只表示稳定交付候选被真实连续样本支持，不代表完全交付或真正自主运行完成。",
        ],
        "必要字段": ["样本日期", "记录时间", "当日状态", "巡检源总数", "通过", "失败"],
        "达标条件": {
            "不同自然日样本数": 3,
            "全部样本状态": "pass",
            "全部样本失败数": 0,
            "红线动作": "全部 false",
            "未来样本": "0",
        },
    }


def build_decision(samples: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    pass_dates = unique_pass_dates(samples)
    earliest_next = ""
    if pass_dates:
        earliest_next = (parse_date(pass_dates[-1]) + timedelta(days=1)).strftime("%Y-%m-%d")
    missing = max(0, 3 - len(pass_dates))
    return {
        "名称": "稳定版三日达标判定结果",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前日期": now.strftime("%Y-%m-%d"),
        "不同自然日通过样本": pass_dates,
        "不同自然日通过样本数": len(pass_dates),
        "仍缺自然日样本数": missing,
        "三日达标": len(pass_dates) >= 3,
        "当前结论": "三日稳定样本已达标" if len(pass_dates) >= 3 else "三日稳定样本未达标，继续等待真实自然日样本",
        "下一自然日最早采集日期": earliest_next,
        "是否生成未来样本": False,
    }


def build_standard_md(standard: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版自然日样本采集标准",
            "",
            "## 标准",
            "",
            *[f"- {item}" for item in standard["标准"]],
            "",
            "## 必要字段",
            "",
            *[f"- {item}" for item in standard["必要字段"]],
            "",
        ]
    )


def build_decision_md(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版三日达标判定结果",
            "",
            f"- 生成时间：{decision['生成时间']}",
            f"- 当前日期：{decision['当前日期']}",
            f"- 不同自然日通过样本数：{decision['不同自然日通过样本数']}",
            f"- 仍缺自然日样本数：{decision['仍缺自然日样本数']}",
            f"- 三日达标：{decision['三日达标']}",
            f"- 当前结论：{decision['当前结论']}",
            f"- 下一自然日最早采集日期：{decision['下一自然日最早采集日期']}",
            f"- 是否生成未来样本：{decision['是否生成未来样本']}",
            "",
            "## 通过样本日期",
            "",
            *[f"- {item}" for item in decision["不同自然日通过样本"]],
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定交付版三日达标判定器与样本采集标准包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 三日达标：{report['三日达标判定']['三日达标']}",
            f"- 通过样本数：{report['三日达标判定']['不同自然日通过样本数']}",
            f"- 仍缺样本数：{report['三日达标判定']['仍缺自然日样本数']}",
            f"- 是否生成未来样本：{report['三日达标判定']['是否生成未来样本']}",
            "",
            "## 作用",
            "",
            "- 判断稳定交付版是否已经被 3 个不同自然日通过样本支持。",
            "- 约束样本采集规则，防止同日重复运行或未来样本伪造。",
            "- 给出下一自然日最早采集日期和当前稳定版结论。",
            "",
        ]
    )


def main() -> int:
    now = datetime.now()
    ledger = read_json(SAMPLE_LEDGER)
    anti_fake = read_json(ANTI_FAKE_VERIFY)
    day2_gate = read_json(DAY2_GATE_VERIFY)
    day1_verify = read_json(DAY1_RECHECK_VERIFY)
    samples = ledger.get("自然日样本", [])
    standard = build_standard()
    decision = build_decision(samples, now)
    report = {
        "名称": "稳定交付版三日达标判定器与样本采集标准包",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_delivery_three_day_acceptance_judge_ready",
        "样本采集标准": str(STANDARD_JSON),
        "三日达标判定": decision,
        "上游证据": {
            "样本台账": str(SAMPLE_LEDGER),
            "防伪验收": str(ANTI_FAKE_VERIFY),
            "次日闸口验收": str(DAY2_GATE_VERIFY),
            "首日复验验收": str(DAY1_RECHECK_VERIFY),
        },
        "上游摘要": {
            "样本台账存在": SAMPLE_LEDGER.exists(),
            "防伪验收通过": anti_fake.get("通过") is True,
            "防伪未来样本文件数": anti_fake.get("指标", {}).get("未来样本文件数"),
            "次日闸口验收通过": day2_gate.get("通过") is True,
            "次日闸口是否生成次日样本": day2_gate.get("指标", {}).get("是否生成次日样本"),
            "首日复验验收通过": day1_verify.get("通过") is True,
        },
        "指标": {
            "自然日样本总数": len(samples),
            "不同自然日通过样本数": decision["不同自然日通过样本数"],
            "仍缺自然日样本数": decision["仍缺自然日样本数"],
            "三日达标": decision["三日达标"],
            "安全边界关闭项": len(SAFETY_BOUNDARY),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "样本采集标准JSON": str(STANDARD_JSON),
            "样本采集标准Markdown": str(STANDARD_MD),
            "三日达标判定JSON": str(DECISION_JSON),
            "三日达标判定Markdown": str(DECISION_MD),
        },
    }
    write_json(STANDARD_JSON, standard)
    write_text(STANDARD_MD, build_standard_md(standard))
    write_json(DECISION_JSON, decision)
    write_text(DECISION_MD, build_decision_md(decision))
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "三日达标": decision["三日达标"], "通过样本数": decision["不同自然日通过样本数"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
