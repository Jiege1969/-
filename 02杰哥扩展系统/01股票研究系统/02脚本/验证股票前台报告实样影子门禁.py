# -*- coding: utf-8 -*-
"""验证股票前台报告实样影子门禁。

验证目标不是强行要求当前真实报告全部通过，而是确认影子门禁能稳定读到真实报告、
能给出缺口清单，并且不会把否定式安全边界误判成真实外发或交易执行。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "03数据" / "289股票前台报告实样影子门禁"
ASSET_PATH = DATA_DIR / "股票前台报告实样影子门禁_最新.json"
RESULT_JSON = DATA_DIR / "股票前台报告实样影子门禁验收_最新.json"
RESULT_MD = DATA_DIR / "股票前台报告实样影子门禁验收_最新.md"


def load_asset() -> dict:
    if not ASSET_PATH.exists():
        return {}
    return json.loads(ASSET_PATH.read_text(encoding="utf-8-sig"))


def main() -> None:
    errors: list[str] = []
    asset = load_asset()
    if asset.get("name") != "股票前台报告实样影子门禁":
        errors.append("资产名称不正确")
    if asset.get("status") != "shadow_gate_only":
        errors.append("必须保持影子门禁状态")
    if asset.get("report_count", 0) <= 0:
        errors.append("必须读到至少一份真实单股报告")
    if len(asset.get("reports", [])) != asset.get("report_count"):
        errors.append("报告数量统计不一致")
    if not asset.get("next_rule"):
        errors.append("必须写入前台报告固化规则")
    for flag, value in asset.get("safety_boundary", {}).items():
        if value is not True:
            errors.append(f"安全边界 {flag} 必须为 true")
    for item in asset.get("reports", []):
        if not item.get("file"):
            errors.append("报告项缺少文件路径")
        if "must_fix" not in item or "review_items" not in item:
            errors.append(f"{item.get('file', '未知报告')} 缺少缺口字段")
        if item.get("hard_forbidden_hits"):
            errors.append(f"{item.get('file', '未知报告')} 出现真实硬禁词：{item['hard_forbidden_hits']}")
    if asset.get("review_total", 0) == 0:
        errors.append("当前阶段应至少识别一类前台报告表达复核点")
    result = {
        "name": "股票前台报告实样影子门禁验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "passed": not errors,
        "errors": errors,
        "metrics": {
            "report_count": asset.get("report_count", 0),
            "passed_count": asset.get("passed_count", 0),
            "must_fix_total": asset.get("must_fix_total", 0),
            "review_total": asset.get("review_total", 0),
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票前台报告实样影子门禁验收",
        "",
        f"- 生成时间：{result['generated_at']}",
        f"- 是否通过：{'是' if result['passed'] else '否'}",
        f"- 检查报告数：{result['metrics']['report_count']}",
        f"- 报告已通过数：{result['metrics']['passed_count']}",
        f"- 必改缺口数：{result['metrics']['must_fix_total']}",
        f"- 复核提示数：{result['metrics']['review_total']}",
        "",
        "## 验收问题",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
