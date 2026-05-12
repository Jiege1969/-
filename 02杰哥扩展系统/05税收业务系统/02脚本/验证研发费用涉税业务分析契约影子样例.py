# -*- coding: utf-8 -*-
"""
名称：验证研发费用涉税业务分析契约影子样例.py
作用：验收研发费用专项涉税业务分析契约影子样例。
安全边界：只读检查；不联网、不下载、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"
SHADOW = OUT_DIR / "研发费用涉税业务分析契约影子样例_最新.json"
SHADOW_MD = OUT_DIR / "研发费用涉税业务分析契约影子样例_最新.md"
REPORT_JSON = OUT_DIR / "研发费用涉税业务分析契约影子样例验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用涉税业务分析契约影子样例验收_最新.md"


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
    report = load_json(SHADOW)
    shadow = report.get("影子样例", {})
    shadow_text = json.dumps(shadow, ensure_ascii=False)
    required_fields = ["政策依据", "依据层级", "适用条件", "业务事实", "资料缺口", "风险点", "置信度", "人工复核项", "输出边界"]
    safety = report.get("安全边界", {})
    checks = [
        check("影子样例JSON存在", SHADOW.exists(), str(SHADOW)),
        check("影子样例Markdown存在", SHADOW_MD.exists(), str(SHADOW_MD)),
        check("契约状态为pending_review", shadow.get("契约状态") == "pending_review", shadow.get("契约状态")),
        check("引用准备度门禁not_ready", shadow.get("准备度门禁状态") == "not_ready" and "不得输出研发费用加计扣除适用判断" in shadow.get("准备度门禁结论", ""), {"状态": shadow.get("准备度门禁状态"), "结论": shadow.get("准备度门禁结论")}),
        check("字段齐备", all(field in shadow for field in required_fields), shadow),
        check("政策依据数量不少于5", len(shadow.get("政策依据", [])) >= 5, len(shadow.get("政策依据", []))),
        check("包含财税119号但不直接放行", any(item.get("文号") == "财税〔2015〕119号" and item.get("是否当前适用依据候选") is False for item in shadow.get("政策依据", [])), shadow.get("政策依据", [])),
        check("业务事实包含补充字段", len(shadow.get("业务事实", {}).get("事实补充字段", [])) >= 8, shadow.get("业务事实", {})),
        check("资料缺口包含政策链和事实缺口", any("政策链" in item for item in shadow.get("资料缺口", [])) and any("企业主体" in item for item in shadow.get("资料缺口", [])), shadow.get("资料缺口", [])),
        check("风险点禁止直接结论", any("不得输出可以享受或不能享受" in item for item in shadow.get("风险点", [])), shadow.get("风险点", [])),
        check("门禁限制传递到影子样例", any("正式税务意见" in item for item in shadow.get("门禁限制", [])), shadow.get("门禁限制", [])),
        check("置信度为low", shadow.get("置信度") == "low", shadow.get("置信度")),
        check("不生成正式税务结论", shadow.get("是否生成正式税务结论") is False, shadow.get("是否生成正式税务结论")),
        check("不接正式入口", shadow.get("是否接正式入口") is False, shadow.get("是否接正式入口")),
        check("禁用confirmed_conclusion", "confirmed_conclusion" not in shadow_text, "未命中"),
        check("不含股票口径", "L3" not in shadow_text and "推荐等级" not in shadow_text and "价位" not in shadow_text, "未命中"),
        check("高风险动作全部关闭", all(value is False for value in safety.values()), safety),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "研发费用涉税业务分析契约影子样例验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不生成正式税务结论。",
    }
    write_json(REPORT_JSON, result)
    lines = [
        "# 研发费用涉税业务分析契约影子样例验收",
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
