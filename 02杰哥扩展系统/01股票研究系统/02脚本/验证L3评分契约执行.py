# -*- coding: utf-8 -*-
"""
名称：验证L3评分契约执行.py
作用：验收单股L3评分报告是否遵守L3评分契约，包括分项权重、总分、结论阈值、置信度和缺口口径。
触发方式：python 验证L3评分契约执行.py
安全边界：只读本地L3评分报告和市场风格日表；只写验收报告；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EXPECTED_ITEMS = {
    "技术结构": 40,
    "基本面/资金": 20,
    "政策事件": 20,
    "市场风格适配": 20,
}
VALID_CONFIDENCE = {"high", "medium", "low"}
STALE_MARKET_WORDS = ["市场风格partial", "市场风格 partial", "市场风格未结构化", "市场风格完整性", "市场风格状态为partial"]


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


def conclusion_for_score(score: float) -> str:
    if score >= 80:
        return "重点关注"
    if score >= 60:
        return "可纳入观察"
    return "暂不建议关注"


def active_score_files(root: Path) -> list[Path]:
    score_dir = base_dir(root) / "单股L3评分"
    files = [p for p in score_dir.glob("*.json") if p.name != "单股L3评分_最新.json"]
    # Prefer the财报补证 shadow reports for sample coverage; keep ordinary latest reports as additional checked assets.
    return sorted(files, key=lambda p: p.name)


def validate_report(path: Path, market_confirmed: bool) -> dict[str, Any]:
    obj = load_json(path, {}) or {}
    blocking: list[str] = []
    warnings: list[str] = []
    total_score = obj.get("total_score")
    item_scores = obj.get("item_scores", [])
    confidence = obj.get("confidence", {})
    confidence_level = confidence.get("level") if isinstance(confidence, dict) else confidence
    conclusion = obj.get("conclusion_text")

    if not isinstance(total_score, (int, float)) or not 0 <= float(total_score) <= 100:
        blocking.append("total_score必须在0-100之间")
        total = 0.0
    else:
        total = float(total_score)

    if not isinstance(item_scores, list) or len(item_scores) != 4:
        blocking.append("item_scores必须包含4个分项")
        item_scores = []

    seen_items: set[str] = set()
    summed = 0.0
    has_missing = False
    for item in item_scores:
        name = str(item.get("item") or "")
        seen_items.add(name)
        max_score = item.get("max_score")
        score = item.get("score")
        missing = item.get("missing", [])
        if name not in EXPECTED_ITEMS:
            blocking.append(f"未知分项：{name}")
        elif max_score != EXPECTED_ITEMS[name]:
            blocking.append(f"{name} max_score应为{EXPECTED_ITEMS[name]}")
        if not isinstance(score, (int, float)):
            blocking.append(f"{name} score不是数字")
        elif isinstance(max_score, (int, float)) and not 0 <= float(score) <= float(max_score):
            blocking.append(f"{name} score超出0-max_score")
        else:
            summed += float(score)
        if not isinstance(missing, list):
            blocking.append(f"{name} missing必须为数组")
        elif missing:
            has_missing = True
    for item_name in EXPECTED_ITEMS:
        if item_name not in seen_items:
            blocking.append(f"缺少分项：{item_name}")

    if isinstance(total_score, (int, float)) and abs(summed - float(total_score)) > 0.2:
        blocking.append(f"分项得分合计{summed:.1f}与total_score {float(total_score):.1f}不一致")

    if conclusion not in {"重点关注", "可纳入观察", "暂不建议关注", "风险复核"}:
        blocking.append("conclusion_text不是允许结论词")
    elif conclusion != "风险复核" and isinstance(total_score, (int, float)) and conclusion != conclusion_for_score(float(total_score)):
        blocking.append(f"conclusion_text与分数阈值不一致，应为{conclusion_for_score(float(total_score))}")

    if confidence_level not in VALID_CONFIDENCE:
        blocking.append("confidence.level必须为high/medium/low")
    if confidence_level == "high" and has_missing:
        blocking.append("存在missing时confidence不能为high")

    text = json.dumps(obj, ensure_ascii=False)
    stale_hits = [word for word in STALE_MARKET_WORDS if word in text]
    if market_confirmed and stale_hits:
        blocking.append("市场风格已confirmed但评分报告仍含旧口径：" + "、".join(stale_hits))

    if not obj.get("evidence_summary"):
        warnings.append("缺少evidence_summary")
    if not obj.get("missing_summary"):
        warnings.append("缺少missing_summary")

    return {
        "file": str(path),
        "file_name": path.name,
        "total_score": total_score,
        "summed_item_score": round(summed, 2),
        "conclusion_text": conclusion,
        "confidence_level": confidence_level,
        "blocking": blocking,
        "warnings": warnings,
        "passed": not blocking,
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['file_name']} | {item['passed']} | {item['total_score']} | {item['summed_item_score']} | {item['conclusion_text']} | {item['confidence_level']} |"
        for item in report["reports"]
    ]
    lines = [
        "# L3评分契约执行验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体状态：{report['status']}",
        "",
        "| 文件 | 通过 | 总分 | 分项合计 | 结论 | 置信度 |",
        "|---|---:|---:|---:|---|---|",
        *rows,
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocking"]] or ["- 无"])
    lines.extend(["", "## 提醒项", ""])
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
    market = load_json(base / "market_style_daily_latest.json", {}) or {}
    market_confirmed = str(market.get("status") or "").lower() == "confirmed"
    reports = [validate_report(path, market_confirmed) for path in active_score_files(root)]
    blocking = [f"{item['file_name']}：{problem}" for item in reports for problem in item["blocking"]]
    warnings = [f"{item['file_name']}：{warning}" for item in reports for warning in item["warnings"]]
    status = "passed" if not blocking else "failed"
    report = {
        "名称": "L3评分契约执行验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": status,
        "market_style_status": market.get("status"),
        "summary": {
            "report_count": len(reports),
            "passed_count": sum(1 for item in reports if item["passed"]),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
        },
        "reports": reports,
        "blocking": blocking,
        "warnings": warnings,
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    json_path = base / "L3评分契约执行验收_最新.json"
    md_path = base / "L3评分契约执行验收_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": status, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
