# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引验收_最新.md"


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
    modules = preview.get("模块索引", [])
    boundaries = preview.get("安全边界", {})
    required_modules = ["持续巡检规则", "持续巡检样例演练", "巡检失败整改模板", "巡检整改后再校验清单"]

    checks = [
        check("阶段收口索引JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("阶段收口索引Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明不修改真实资产", contains(preview, "不修改真实资产") and contains(preview, "不是正式税务结论"), preview.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(preview, "政策证据底座") and contains(preview, "待复核分析草案"), preview.get("系统定位")),
        check("模块数量不少于4", preview.get("模块数量", 0) >= 4, preview.get("模块数量")),
        check("缺失数量为0", preview.get("缺失数量", 1) == 0, preview.get("缺失数量")),
        check("失败数量为0", preview.get("失败数量", 1) == 0, preview.get("失败数量")),
        check("阶段结论通过", preview.get("阶段结论") == "通过", preview.get("阶段结论")),
        check("所有模块数据存在", all(item.get("数据是否存在") is True for item in modules), modules),
        check("所有模块验收存在", all(item.get("验收报告是否存在") is True for item in modules), modules),
        check("所有模块验收通过", all(item.get("验收是否通过") is True for item in modules), modules),
        check("下一步包含阶段总回传记录", contains(preview.get("下一步低风险队列", []), "阶段总回传记录"), preview.get("下一步低风险队列", [])),
    ]
    for item in required_modules:
        checks.append(check(f"包含模块：{item}", contains(modules, item), item))
    checks.extend([
        check("阶段护栏禁止正式税务意见", contains(preview.get("阶段护栏", []), "正式税务意见"), preview.get("阶段护栏", [])),
        check("阶段护栏禁止真实发送", contains(preview.get("阶段护栏", []), "真实发送企业微信"), preview.get("阶段护栏", [])),
    ])
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路巡检整改闭环阶段收口索引验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环阶段收口索引验收",
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
