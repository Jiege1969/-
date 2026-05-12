# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"
PREVIEW_JSON = OUT_DIR / "涉税业务分析契约影子样例复核_最新.json"
PREVIEW_MD = OUT_DIR / "涉税业务分析契约影子样例复核_最新.md"
REPORT_JSON = OUT_DIR / "涉税业务分析契约影子样例复核验收_最新.json"
REPORT_MD = OUT_DIR / "涉税业务分析契约影子样例复核验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON)
    results = preview.get("样例复核结果", [])
    checks = [
        check("复核JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("复核Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("复核样例数量不少于2", preview.get("样例数量", 0) >= 2, preview.get("样例数量")),
        check("风险数量为0", preview.get("风险数量") == 0, results),
        check("所有样例契约状态为待复核类", all(item.get("契约状态") in {"pending_review", "draft", "evidence_ready"} for item in results), results),
        check("所有样例不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in results), results),
        check("所有样例具备政策依据和人工复核项", all(item.get("政策依据数量", 0) > 0 and item.get("人工复核项数量", 0) > 0 for item in results), results),
        check("下一步队列指向企业微信dry-run复检", any("dry-run" in item.get("事项", "") for item in preview.get("下一步自动队列", [])), preview.get("下一步自动队列", [])),
    ]
    safety = preview.get("安全边界", {})
    required_false = [
        "是否联网",
        "是否下载",
        "是否调用模型推理",
        "是否写正式业务库",
        "是否生成正式税务结论",
        "是否接电子税务局",
        "是否接财税软件",
        "是否触发n8n",
        "是否企业微信真实发送",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "涉税业务分析契约影子样例复核验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 涉税业务分析契约影子样例复核验收",
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
