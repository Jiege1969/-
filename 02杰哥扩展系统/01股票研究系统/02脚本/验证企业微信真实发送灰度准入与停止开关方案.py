# -*- coding: utf-8 -*-
"""
名称：验证企业微信真实发送灰度准入与停止开关方案.py
作用：验收236企业微信真实发送灰度准入与停止开关方案是否只生成本地准入包，且继续阻断真实发送、n8n、服务重启和交易。
安全边界：只读236准入包、24草稿和关键入口源码；只写236验收报告；不调用发送器、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "236企业微信真实发送灰度准入与停止开关方案"
PLAN_JSON = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案_最新.json"
PLAN_MD = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案_最新.md"
SHORT_JSON = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信真实发送灰度准入与停止开关方案验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    plan = load_json(PLAN_JSON)
    plan_md = read_text(PLAN_MD)
    short = load_json(SHORT_JSON)
    actions = plan.get("实际动作", {})
    gates = plan.get("发送前硬闸口", [])
    upstream = plan.get("上游验收", [])
    stop_switches = plan.get("灰度方案", {}).get("停止开关", [])
    manual_gates = plan.get("灰度方案", {}).get("人工确认闸口", [])
    short_actions = short.get("实际动作", {})

    checks = [
        check(PLAN_JSON.exists() and PLAN_MD.exists(), "236准入方案产物存在", str(PLAN_JSON)),
        check(plan.get("允许真实发送") is False, "方案不允许直接真实发送", plan.get("允许真实发送")),
        check(plan.get("允许n8n启用") is False, "方案不允许启用n8n", plan.get("允许n8n启用")),
        check(plan.get("允许服务重启") is False, "方案不允许服务重启", plan.get("允许服务重启")),
        check(all(value is False for value in actions.values()), "本方案高风险实际动作全部为False", actions),
        check(len(upstream) >= 5 and all(item.get("结论") == "通过" and item.get("失败数量") == 0 for item in upstream), "上游验收全部通过", upstream),
        check(len(gates) >= 8 and all(item.get("通过") is True for item in gates), "发送前硬闸口全部通过", gates),
        check(short.get("模板模式") == "v21_template_dry_run", "24草稿仍为v21 dry-run", short.get("模板模式")),
        check(all(value is False for value in short_actions.values()), "24草稿实际动作全关闭", short_actions),
        check(len(stop_switches) >= 5 and "停止开关" in plan_md, "停止开关方案完整", stop_switches),
        check(len(manual_gates) >= 4 and "人工确认" in plan_md, "人工确认闸口完整", manual_gates),
        check("不传 --real-send" in plan_md and "n8n" in plan_md, "文本明确默认不发送且不启用n8n", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信真实发送灰度准入与停止开关方案验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "调用公共受控发送器": False,
            "发送企业微信": False,
            "触发n8n": False,
            "重启服务": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案验收_最新.json"
    latest_md = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
