# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"
SOURCE_JSON = OUT_DIR / "税收政策证据底座字段补齐预演_最新.json"
REVIEW_JSON = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.json"
REVIEW_MD = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.md"
REPORT_JSON = OUT_DIR / "税收政策证据底座字段补齐预演复核验收_最新.json"
REPORT_MD = OUT_DIR / "税收政策证据底座字段补齐预演复核验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_json(SOURCE_JSON)
    review = load_json(REVIEW_JSON)
    checks = []

    checks.append(check("来源预演JSON存在", SOURCE_JSON.exists(), str(SOURCE_JSON)))
    checks.append(check("复核JSON存在", REVIEW_JSON.exists(), str(REVIEW_JSON)))
    checks.append(check("复核Markdown存在", REVIEW_MD.exists(), str(REVIEW_MD)))
    checks.append(check("复核未修改原始政策资料", review.get("是否修改原始政策资料") is False, review.get("是否修改原始政策资料")))
    checks.append(check("资料数量与来源一致", review.get("资料数量") == len(source.get("资料", [])), {"复核": review.get("资料数量"), "来源": len(source.get("资料", []))}))
    checks.append(check("复核结论不含失败", "失败" not in str(review.get("复核结论", "")), review.get("复核结论")))
    checks.append(check("候选依据风险为零", review.get("候选依据风险数量") == 0, review.get("候选依据风险", [])))
    checks.append(check("正式结论越界风险为零", review.get("正式结论越界风险数量") == 0, review.get("正式结论越界风险", [])))
    checks.append(check("安全边界风险为零", review.get("安全边界风险数量") == 0, review.get("安全边界风险", [])))
    checks.append(check("字段缺口均进入复核口径或允许继续补强", all(item.get("是否已进入待人工复核项") or item.get("处理口径") for item in review.get("字段缺口", [])), review.get("字段缺口", [])))
    checks.append(check("下一步自动队列不生成正式税务结论", all("不生成正式税务结论" in item.get("边界", "") for item in review.get("下一步自动队列", [])), review.get("下一步自动队列", [])))

    safety = review.get("安全边界", {})
    required_false = [
        "是否联网",
        "是否下载",
        "是否覆盖原始资料",
        "是否写正式业务规则",
        "是否生成正式税务结论",
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否读取或保存企业微信凭据",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收政策证据底座字段补齐预演复核验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收政策证据底座字段补齐预演复核验收",
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
