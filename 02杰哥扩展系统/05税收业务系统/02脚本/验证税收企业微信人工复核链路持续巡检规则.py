# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.json"
PREVIEW_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.md"
REPORT_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则验收_最新.json"
REPORT_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则验收_最新.md"


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
    rules = load_json(PREVIEW_JSON)
    baseline = rules.get("当前基线", {})
    boundaries = rules.get("安全边界", {})
    rule_groups = rules.get("规则组", [])

    checks = [
        check("持续巡检规则JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("持续巡检规则Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明不是自动化任务", contains(rules, "不是自动化任务") and contains(rules, "不启动服务"), rules.get("资产身份")),
        check("系统定位保持政策证据底座与待复核草案", contains(rules, "政策证据底座") and contains(rules, "待复核分析草案"), rules.get("系统定位")),
        check("包含阶段收口索引来源", contains(rules.get("巡检来源", {}), "阶段收口索引"), rules.get("巡检来源", {})),
        check("包含一键本地预检来源", contains(rules.get("巡检来源", {}), "一键本地预检"), rules.get("巡检来源", {})),
        check("包含阶段总回传记录来源", contains(rules.get("巡检来源", {}), "阶段总回传记录"), rules.get("巡检来源", {})),
        check("规则组不少于4组", len(rule_groups) >= 4, len(rule_groups)),
        check("包含资产身份一致性规则", contains(rule_groups, "资产身份一致性"), rule_groups),
        check("包含验收完整性规则", contains(rule_groups, "验收完整性"), rule_groups),
        check("包含红线边界规则", contains(rule_groups, "红线边界"), rule_groups),
        check("包含总管对齐规则", contains(rule_groups, "总管对齐"), rule_groups),
        check("阶段模块数量不少于11", baseline.get("阶段模块数量", 0) >= 11, baseline),
        check("阶段失败数量为0", baseline.get("阶段失败数量", 0) == 0, baseline),
        check("一键预检脚本数量不少于12", baseline.get("一键预检脚本数量", 0) >= 12, baseline),
        check("一键预检失败数量为0", baseline.get("一键预检失败数量", 0) == 0, baseline),
        check("阶段总回传记录存在", baseline.get("阶段总回传记录存在") is True, baseline),
        check("漂移判定包含红线漂移", contains(rules.get("漂移判定", []), "红线漂移"), rules.get("漂移判定", [])),
        check("下一步建议包含样例演练", contains(rules.get("下一步建议", []), "样例演练"), rules.get("下一步建议", [])),
    ]
    for key, value in boundaries.items():
        checks.append(check(f"安全边界关闭：{key}", value is False, value))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路持续巡检规则验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路持续巡检规则验收",
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
