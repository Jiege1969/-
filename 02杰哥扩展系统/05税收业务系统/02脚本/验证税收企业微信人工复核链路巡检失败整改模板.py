# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板验收_最新.md"


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
    templates = preview.get("整改模板", [])
    boundaries = preview.get("安全边界", {})
    required_types = ["验收报告缺失", "验收失败", "红线漂移", "正式结论口径", "总管越权修改", "已完成项回流"]
    required_fields = ["问题编号", "发现时间", "触发规则", "影响范围", "整改建议", "人工复核人", "再校验脚本"]

    checks = [
        check("整改模板JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("整改模板Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明不修改真实资产", contains(preview, "不修改真实资产") and contains(preview, "不是正式税务结论"), preview.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(preview, "政策证据底座") and contains(preview, "待复核分析草案"), preview.get("系统定位")),
        check("引用持续巡检样例演练", contains(preview.get("引用演练", ""), "持续巡检样例演练"), preview.get("引用演练")),
        check("演练阻断样例数量不少于5", preview.get("演练阻断样例数量", 0) >= 5, preview.get("演练阻断样例数量")),
        check("整改模板数量不少于6", len(templates) >= 6, len(templates)),
    ]
    for item in required_types:
        checks.append(check(f"包含整改类型：{item}", contains(templates, item), item))
    for item in required_fields:
        checks.append(check(f"包含必填字段：{item}", contains(templates, item), item))
    checks.extend([
        check("统一要求禁止自动回写真实资产", contains(preview.get("统一处置要求", []), "不得自动回写真实资产"), preview.get("统一处置要求", [])),
        check("统一要求红线只登记阻断", contains(preview.get("统一处置要求", []), "只登记阻断"), preview.get("统一处置要求", [])),
        check("下一步建议包含再校验清单", contains(preview.get("下一步建议", []), "再校验清单"), preview.get("下一步建议", [])),
    ])
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路巡检失败整改模板验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检失败整改模板验收",
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
