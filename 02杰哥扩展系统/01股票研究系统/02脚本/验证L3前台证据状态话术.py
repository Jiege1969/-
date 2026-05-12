# -*- coding: utf-8 -*-
"""
名称：验证L3前台证据状态话术.py
作用：验收企业微信前台短答是否如实表达证据状态，防止来源登记、单点观测、未入账数据被写成趋势或强支撑。
触发方式：python 验证L3前台证据状态话术.py
安全边界：只读本地短答验收和行业价格证据卡；只写验收报告；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SAMPLES = [
    {"name": "云南锗业", "code": "sz002428", "price_status": "source_registered"},
    {"name": "天齐锂业", "code": "sz002466", "price_status": "single_observation"},
    {"name": "华虹公司", "code": "sh688347", "price_status": "not_required"},
    {"name": "浙商中拓", "code": "sz000906", "price_status": "not_required"},
    {"name": "正丹股份", "code": "sz300641", "price_status": "source_registered"},
]

OVERCLAIM_WORDS = [
    "趋势反转",
    "趋势支撑",
    "价格趋势已确认",
    "价格已形成支撑",
    "行业价格已入账",
    "trend_ready",
    "连续趋势已形成",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def base_dir(root: Path) -> Path:
    return root / "03数据" / "245L3评分基础资产"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sample_reply(report: dict[str, Any], name: str, code: str) -> str:
    for item in report.get("samples", []) if isinstance(report.get("samples"), list) else []:
        text = json.dumps(item, ensure_ascii=False)
        if name in text and code in text:
            return str(item.get("reply") or item.get("reply_preview") or "")
    return ""


def line_of(reply: str, prefix: str) -> str:
    for line in reply.splitlines():
        if line.startswith(prefix):
            return line
    return ""


def validate_sample(sample: dict[str, str], reply: str) -> dict[str, Any]:
    name = sample["name"]
    code = sample["code"]
    status = sample["price_status"]
    why = line_of(reply, "为什么：")
    missing = line_of(reply, "缺口：")
    combined = why + "\n" + missing
    blocking: list[str] = []
    warnings: list[str] = []

    if not reply:
        blocking.append("未找到前台短答")
    overclaims = [word for word in OVERCLAIM_WORDS if word in reply]
    if overclaims:
        blocking.append("出现证据过度表述：" + "、".join(overclaims))
    stale_market_words = ["市场风格partial", "市场风格 partial", "市场风格未结构化", "市场风格完整性"]
    stale_market_hits = [word for word in stale_market_words if word in reply]
    if stale_market_hits:
        blocking.append("市场风格已confirmed但前台仍出现旧缺口：" + "、".join(stale_market_hits))
    if any(token in reply for token in ["和。", "和；", "、。", "，。"]):
        blocking.append("前台缺口清洗后出现残句或异常标点")
    if "政策事件。" in reply:
        blocking.append("前台缺口出现过短空泛残句：政策事件。")

    if status == "source_registered":
        if not any(token in combined for token in ["未入账", "尚未入账", "来源已登记"]):
            blocking.append("来源登记状态未在前台明确写成未入账/来源登记")
        if any(token in combined for token in ["单点价格观测", "已有单点", "趋势已形成"]):
            blocking.append("来源登记状态被误写成已有价格观测或趋势")
    elif status == "single_observation":
        if not any(token in combined for token in ["单点", "弱参考", "尚未形成5个连续观测点", "尚未形成20个连续观测点"]):
            blocking.append("单点观测状态未在前台明确写成单点/弱参考/未成连续")
        if any(token in combined for token in ["趋势反转", "趋势已形成", "价格趋势已确认"]):
            blocking.append("单点观测被误写成趋势")
    elif status == "not_required":
        if any(token in reply for token in ["行业价格已入账", "价格趋势已确认", "trend_ready"]):
            blocking.append("非强制行业价格样本被写成行业价格已入账或趋势已确认")
        if "行业价格" not in reply:
            warnings.append("前台未显式说明行业价格状态；当前可接受，但后续若加行业价格卡需同步更新")

    if why and len(why) > 150:
        blocking.append("为什么行超过150字")
    if missing and len(missing) > 140:
        warnings.append("缺口行偏长，后续可继续压缩")

    return {
        "name": name,
        "code": code,
        "price_status": status,
        "why_line": why,
        "missing_line": missing,
        "blocking": blocking,
        "warnings": warnings,
        "passed": not blocking,
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['name']} | {item['code']} | {item['price_status']} | {item['passed']} | {'；'.join(item['blocking']) if item['blocking'] else '无'} |"
        for item in report["samples"]
    ]
    lines = [
        "# L3前台证据状态话术验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "| 股票 | 代码 | 行业价格状态 | 通过 | 阻断项 |",
        "|---|---|---|---:|---|",
        *rows,
        "",
        "## 提醒项",
        "",
    ]
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- 无"])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 不真实发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    base = base_dir(root)
    short_report = load_json(base / "L3企业微信短答适配器自动验收_20260507.json", {}) or {}
    rows = [validate_sample(sample, sample_reply(short_report, sample["name"], sample["code"])) for sample in SAMPLES]
    blocking = [f"{item['name']}：{problem}" for item in rows for problem in item["blocking"]]
    warnings = [f"{item['name']}：{warning}" for item in rows for warning in item["warnings"]]
    status = "passed" if not blocking else "failed"
    report = {
        "名称": "L3前台证据状态话术验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "summary": {
            "sample_count": len(rows),
            "passed_count": sum(1 for item in rows if item["passed"]),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        },
        "samples": rows,
        "blocking": blocking,
        "warnings": warnings,
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = base / "L3前台证据状态话术验收_最新.json"
    md_path = base / "L3前台证据状态话术验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
