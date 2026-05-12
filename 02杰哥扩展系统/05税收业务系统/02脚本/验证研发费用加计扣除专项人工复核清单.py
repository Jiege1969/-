# -*- coding: utf-8 -*-
"""
名称：验证研发费用加计扣除专项人工复核清单.py
作用：验收研发费用加计扣除专项人工复核清单是否覆盖证据、事实、闸口和安全边界。
安全边界：只读检查；不联网、不下载、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
PREVIEW = OUT_DIR / "研发费用加计扣除政策链补齐预演_最新.json"
CHECKLIST = OUT_DIR / "研发费用加计扣除专项人工复核清单_最新.json"
CHECKLIST_MD = OUT_DIR / "研发费用加计扣除专项人工复核清单_最新.md"
REPORT_JSON = OUT_DIR / "研发费用加计扣除专项人工复核清单验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用加计扣除专项人工复核清单验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    preview = load_json(PREVIEW, {"证据卡片": []})
    report = load_json(CHECKLIST)
    evidence_rows = report.get("证据复核清单", [])
    fact_rows = report.get("业务事实补充清单", [])
    gates = report.get("放行闸口", [])
    safety = report.get("安全边界", {})
    checks = [
        check("政策链预演存在", PREVIEW.exists(), str(PREVIEW)),
        check("专项复核清单JSON存在", CHECKLIST.exists(), str(CHECKLIST)),
        check("专项复核清单Markdown存在", CHECKLIST_MD.exists(), str(CHECKLIST_MD)),
        check("清单保持待复核口径", report.get("链条状态") == "pending_review" and "不形成正式税务结论" in report.get("复核结论口径", ""), report.get("复核结论口径", "")),
        check("证据复核覆盖全部证据卡", len(evidence_rows) == len(preview.get("证据卡片", [])) and len(evidence_rows) >= 1, {"清单": len(evidence_rows), "证据卡": len(preview.get("证据卡片", []))}),
        check("财税119复核重点存在", any("财税〔2015〕119号" in row.get("文号", "") and any("联合发文来源" in focus or "正式发布机关" in focus for focus in row.get("复核重点", [])) for row in evidence_rows), evidence_rows),
        check("案例只作风险提示", all(any("案例仅用于事实识别" in focus for focus in row.get("复核重点", [])) for row in evidence_rows if row.get("依据层级") == "案例"), evidence_rows),
        check("业务事实字段不少于8项", len(fact_rows) >= 8, fact_rows),
        check("业务事实包含创新性和费用归集", all(any(key in row.get("字段", "") for row in fact_rows) for key in ["技术不确定性", "费用归集"]), fact_rows),
        check("放行闸口阻止直接结论", any("不得输出可以享受或不能享受" in gate for gate in gates), gates),
        check("政策链缺口随清单保留", len(report.get("政策链缺口", [])) >= 1, report.get("政策链缺口", [])),
        check("不生成正式税务结论", safety.get("是否生成正式税务结论") is False, safety),
        check("高风险动作全部关闭", all(value is False for value in safety.values()), safety),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "研发费用加计扣除专项人工复核清单验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不生成正式税务结论。",
    }
    write_json(REPORT_JSON, result)
    lines = [
        "# 研发费用加计扣除专项人工复核清单验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": result["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
