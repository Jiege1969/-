# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"
REVIEW_JSON = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.json"
PREVIEW_JSON = OUT_DIR / "税收政策证据底座字段缺口补强预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收政策证据底座字段缺口补强预演_最新.md"
REPORT_JSON = OUT_DIR / "税收政策证据底座字段缺口补强预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收政策证据底座字段缺口补强预演验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    review = load_json(REVIEW_JSON)
    preview = load_json(PREVIEW_JSON)
    drafts = preview.get("补强草案", [])
    checks = []

    checks.append(check("复核来源JSON存在", REVIEW_JSON.exists(), str(REVIEW_JSON)))
    checks.append(check("补强预演JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("补强预演Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("缺口数量承接复核结果", preview.get("缺口数量") == review.get("字段缺口数量"), {"补强": preview.get("缺口数量"), "复核": review.get("字段缺口数量")}))
    checks.append(check("补强草案数量不超过缺口数量", preview.get("补强草案数量", 0) <= preview.get("缺口数量", 0), {"草案": preview.get("补强草案数量"), "缺口": preview.get("缺口数量")}))
    checks.append(check("所有补强草案均为待复核状态", all(item.get("处理状态") == "pending_review" for item in drafts), drafts))
    checks.append(check("所有补强草案不回写正式字段", all(item.get("是否回写正式字段") is False for item in drafts), drafts))
    checks.append(check("所有补强草案不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in drafts), drafts))
    checks.append(check("补强草案包含人工复核要求", all(item.get("人工复核要求") for item in drafts), drafts))
    checks.append(check("下一步队列仍限定不生成正式税务结论", all("不生成正式税务结论" in item.get("边界", "") for item in preview.get("下一步自动队列", [])), preview.get("下一步自动队列", [])))

    safety = preview.get("安全边界", {})
    required_false = [
        "是否联网",
        "是否下载",
        "是否覆盖原始资料",
        "是否回写正式字段",
        "是否写正式业务规则",
        "是否生成正式税务结论",
        "是否触发n8n",
        "是否企业微信真实发送",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收政策证据底座字段缺口补强预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收政策证据底座字段缺口补强预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
