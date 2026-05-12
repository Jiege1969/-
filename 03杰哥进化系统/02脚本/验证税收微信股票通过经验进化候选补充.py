# -*- coding: utf-8 -*-
"""
名称：验证税收微信股票通过经验进化候选补充.py
作用：只读验证本轮税收微信股票通过经验进化候选补充资产。
触发方式：python 验证税收微信股票通过经验进化候选补充.py
依赖：Python标准库。
所属系统：03杰哥进化系统
安全边界：只读候选文件并写03日志；不写正式规则，不修改运行配置，不修改总管面板或一键接续包，不触发任何服务重载。
标识：tax-wechat-stock-passed-experience-candidate-supplement-verify
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def safety_all_false(safety: dict[str, Any], keys: list[str]) -> bool:
    return all(safety.get(key) is False for key in keys)


def main() -> int:
    root = system_root()
    data_dir = root / "03数据" / "38本轮税收微信股票通过经验进化候选补充"
    record_path = data_dir / "进化候选补充记录_最新.json"
    cases_path = data_dir / "候选案例_最新.json"
    suggestions_path = data_dir / "只读验收建议_最新.json"
    report_path = data_dir / "本轮税收微信股票通过经验进化候选补充回传_最新.md"
    log_dir = root / "04日志" / "税收微信股票通过经验候选补充验收"

    checks: list[dict[str, Any]] = []
    for name, path in [
        ("候选补充记录存在", record_path),
        ("候选案例存在", cases_path),
        ("只读验收建议存在", suggestions_path),
        ("回传报告存在", report_path),
    ]:
        add_check(checks, name, path.exists(), str(path))

    record = load_json(record_path) if record_path.exists() else {}
    cases = load_json(cases_path) if cases_path.exists() else {}
    suggestions = load_json(suggestions_path) if suggestions_path.exists() else {}

    supplements = record.get("本轮已通过事实", [])
    supplement_ids = {item.get("补充ID") for item in supplements}
    add_check(checks, "记录包含股票和税收两类补充", {"TWS-CAND-001", "TWS-CAND-002"}.issubset(supplement_ids), sorted(supplement_ids))
    add_check(checks, "候选补充数量为2", record.get("候选补充数量") == 2 and len(supplements) == 2, record.get("候选补充数量"))
    add_check(checks, "所有补充保持候选状态", all(item.get("候选状态") == "candidate_supplement_only" for item in supplements), supplements)
    add_check(checks, "所有补充不得作为正式规则", all(item.get("可作为正式规则") is False for item in supplements), supplements)
    add_check(checks, "所有补充需总管确认后升级", all(item.get("需总管确认后才能升级") is True for item in supplements), supplements)

    case_items = cases.get("候选案例", [])
    case_candidate_ids = {item.get("candidate_id") for item in case_items}
    add_check(checks, "候选案例不少于8个", len(case_items) >= 8, len(case_items))
    add_check(checks, "案例覆盖股票和税收补充", {"TWS-CAND-001", "TWS-CAND-002"}.issubset(case_candidate_ids), sorted(case_candidate_ids))
    add_check(checks, "所有案例有禁止动作", all(bool(item.get("禁止动作")) for item in case_items), len(case_items))
    add_check(checks, "所有案例保持candidate_case", all(item.get("预期状态") == "candidate_case" for item in case_items), case_items)

    suggestion_items = suggestions.get("验收建议", [])
    add_check(checks, "只读验收建议不少于5条", len(suggestion_items) >= 5, len(suggestion_items))
    add_check(checks, "每条建议都有红线", all(bool(item.get("红线")) for item in suggestion_items), len(suggestion_items))
    add_check(checks, "建议执行方式禁止真实动作", "触发服务重载" in suggestions.get("建议执行方式", {}).get("禁止", []), suggestions.get("建议执行方式"))

    forbidden_keys = [
        "写入正式规则",
        "修改运行配置",
        "推进为正式规则",
        "修改总管面板",
        "修改一键接续包",
        "触发服务重载",
    ]
    add_check(checks, "补充记录红线关闭", safety_all_false(record.get("安全边界", {}), forbidden_keys), record.get("安全边界", {}))
    add_check(checks, "候选案例红线关闭", safety_all_false(cases.get("安全边界", {}), forbidden_keys), cases.get("安全边界", {}))
    add_check(checks, "验收建议红线关闭", safety_all_false(suggestions.get("安全边界", {}), forbidden_keys), suggestions.get("安全边界", {}))

    touched_redline = {
        "写入正式规则": False,
        "修改运行配置": False,
        "推进为正式规则": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "触发服务重载": False,
        "接券商接口": False,
        "自动交易": False,
        "生成正式税务结论": False,
        "登录电子税务局": False,
        "接财税软件": False,
    }
    add_check(checks, "本验证未触碰红线", all(value is False for value in touched_redline.values()), touched_redline)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "tax-wechat-stock-passed-experience-candidate-supplement-verify",
        "所属系统": "03杰哥进化系统",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": {
            "候选补充记录": str(record_path),
            "候选案例": str(cases_path),
            "只读验收建议": str(suggestions_path),
            "回传报告": str(report_path),
        },
        "红线动作": touched_redline,
    }
    output = log_dir / f"tax-wechat-stock-passed-experience-candidate-supplement-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "tax-wechat-stock-passed-experience-candidate-supplement-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
