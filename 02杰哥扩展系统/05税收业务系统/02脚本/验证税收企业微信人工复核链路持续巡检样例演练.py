# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains(data: Any, keyword: str) -> bool:
    return keyword in json.dumps(data, ensure_ascii=False)


def main() -> int:
    preview = load_json(PREVIEW_JSON)
    results = preview.get("样例结果", [])
    boundaries = preview.get("安全边界", {})
    blocked = [item for item in results if item.get("识别结果") == "阻断"]
    healthy = [item for item in results if item.get("识别结果") == "通过"]

    checks = [
        check("样例演练JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("样例演练Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明本地样例演练", contains(preview, "本地样例演练") and contains(preview, "不创建自动化任务"), preview.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(preview, "政策证据底座") and contains(preview, "待复核分析草案"), preview.get("系统定位")),
        check("引用持续巡检规则", contains(preview.get("引用规则", ""), "持续巡检规则"), preview.get("引用规则")),
        check("样例数量不少于6", preview.get("样例数量", 0) >= 6, preview.get("样例数量")),
        check("所有样例符合预期", preview.get("不符合预期数量", 1) == 0, preview.get("样例结果", [])),
        check("健康样例通过", any(item.get("样例ID") == "patrol_case_001" and item.get("识别结果") == "通过" for item in healthy), healthy),
        check("阻断样例不少于5个", len(blocked) >= 5, blocked),
        check("识别验收报告缺失", contains(blocked, "验收报告缺失"), blocked),
        check("识别真实发送红线漂移", contains(blocked, "真实发送") and contains(blocked, "红线漂移"), blocked),
        check("识别正式税务结论口径", contains(blocked, "正式税务结论"), blocked),
        check("识别总管越权修改", contains(blocked, "越权漂移"), blocked),
        check("识别已完成项回流", contains(blocked, "已完成项回流"), blocked),
        check("下一步建议包含整改模板", contains(preview.get("下一步建议", []), "整改模板"), preview.get("下一步建议", [])),
    ]
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路持续巡检样例演练验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路持续巡检样例演练验收",
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
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
