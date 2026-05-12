# -*- coding: utf-8 -*-
"""
名称：验证研发费用业务事实采集模板.py
作用：验收研发费用业务事实采集模板的字段覆盖、放行规则和安全边界。
安全边界：只读检查；不联网、不下载、不测算金额、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "30研发费用业务事实采集模板"
TEMPLATE_JSON = OUT_DIR / "研发费用业务事实采集模板_最新.json"
TEMPLATE_MD = OUT_DIR / "研发费用业务事实采集模板_最新.md"
REPORT_JSON = OUT_DIR / "研发费用业务事实采集模板验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用业务事实采集模板验收_最新.md"


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
    template = load_json(TEMPLATE_JSON)
    fields = template.get("字段", [])
    field_names = {item.get("字段") for item in fields}
    categories = {item.get("类别") for item in fields}
    safety = template.get("安全边界", {})
    required_names = {
        "企业名称",
        "纳税人识别号",
        "纳税人类型",
        "所属年度",
        "研发项目名称",
        "项目研发目标",
        "拟突破核心技术",
        "研发费用总额",
        "是否涉及不适用行业",
        "是否涉及不适用活动",
        "研发支出辅助账",
        "费用归集明细",
    }
    checks = [
        check("模板JSON存在", TEMPLATE_JSON.exists(), str(TEMPLATE_JSON)),
        check("模板Markdown存在", TEMPLATE_MD.exists(), str(TEMPLATE_MD)),
        check("模板状态为draft", template.get("模板状态") == "draft", template.get("模板状态")),
        check("字段数量不少于25", len(fields) >= 25, len(fields)),
        check("必填字段数量不少于15", template.get("必填字段数量", 0) >= 15, template.get("必填字段数量")),
        check("关键字段齐备", required_names.issubset(field_names), sorted(required_names - field_names)),
        check("字段类别覆盖主体项目费用排除资料", all(item in categories for item in ["主体信息", "项目事实", "费用信息", "排除事项", "资料清单"]), sorted(categories)),
        check("所有字段保持待填写", all(item.get("人工核验状态") == "待填写" for item in fields), fields),
        check("放行规则禁止缺字段时判断", any("必填字段未补齐" in item and "不得生成适用判断" in item for item in template.get("放行规则", [])), template.get("放行规则", [])),
        check("放行规则禁止金额自动测算", any("不自动测算" in item for item in template.get("放行规则", [])), template.get("放行规则", [])),
        check("不测算金额", safety.get("是否测算金额") is False, safety),
        check("不生成正式税务结论", safety.get("是否生成正式税务结论") is False, safety),
        check("高风险动作全部关闭", all(value is False for value in safety.values()), safety),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "研发费用业务事实采集模板验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不测算金额、不生成正式税务结论。",
    }
    write_json(REPORT_JSON, report)
    lines = [
        "# 研发费用业务事实采集模板验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
