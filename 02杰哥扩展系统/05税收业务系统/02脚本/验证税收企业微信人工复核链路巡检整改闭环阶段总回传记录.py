# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录验收_最新.md"


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
    record = load_json(PREVIEW_JSON)
    summary = record.get("阶段摘要", {})
    transfer = record.get("回传口径", {})
    boundaries = record.get("安全边界", {})
    checks = [
        check("总回传JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("总回传Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份不是正式入口或正式结论", contains(record, "不是正式入口放行") and contains(record, "不是正式税务结论"), record.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(record, "政策证据底座") and contains(record, "待复核分析草案"), record.get("系统定位")),
        check("引用阶段收口索引", contains(record.get("来源文件", {}), "阶段收口索引"), record.get("来源文件", {})),
        check("巡检整改闭环模块数量不少于4", summary.get("巡检整改闭环模块数量", 0) >= 4, summary),
        check("巡检整改闭环缺失数量为0", summary.get("巡检整改闭环缺失数量", 1) == 0, summary),
        check("巡检整改闭环失败数量为0", summary.get("巡检整改闭环失败数量", 1) == 0, summary),
        check("当前总收口失败数量为0", summary.get("当前阶段总收口失败数量", 1) == 0, summary),
        check("回传要求总管只读整合", transfer.get("是否需要总管整合") is True and transfer.get("是否允许自动实施总管修改") is False, transfer),
        check("下一步包含持续巡检入口说明", contains(record.get("下一步建议", []), "持续巡检入口说明"), record.get("下一步建议", [])),
    ]
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路巡检整改闭环阶段总回传记录验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环阶段总回传记录验收",
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
