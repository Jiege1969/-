# -*- coding: utf-8 -*-
"""
名称：验证阶段性多业务联调通过封版候选.py
作用：只读验证阶段性多业务联调通过封版候选记录及配套清单。
触发方式：python 验证阶段性多业务联调通过封版候选.py
依赖：Python标准库。
所属系统：03杰哥进化系统
安全边界：只读候选文件并写03日志；不写正式规则，不修改运行配置，不触发服务重载，不真实发送。
标识：multi-business-integration-passed-freeze-candidate-verify
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
    data_dir = root / "03数据" / "39阶段性多业务联调通过封版候选"
    record_path = data_dir / "阶段性多业务联调通过候选记录_最新.json"
    available_path = data_dir / "可用能力清单候选_最新.json"
    blocked_path = data_dir / "仍阻断能力清单候选_最新.json"
    regression_path = data_dir / "后续回归测试建议_最新.json"
    suggestions_path = data_dir / "只读验收建议_最新.json"
    report_path = data_dir / "阶段性多业务联调通过封版候选回传_最新.md"
    log_dir = root / "04日志" / "阶段性多业务联调通过封版候选验收"

    checks: list[dict[str, Any]] = []
    for name, path in [
        ("候选记录存在", record_path),
        ("可用能力清单候选存在", available_path),
        ("仍阻断能力清单候选存在", blocked_path),
        ("后续回归测试建议存在", regression_path),
        ("只读验收建议存在", suggestions_path),
        ("回传报告存在", report_path),
    ]:
        add_check(checks, name, path.exists(), str(path))

    record = load_json(record_path) if record_path.exists() else {}
    available = load_json(available_path) if available_path.exists() else {}
    blocked = load_json(blocked_path) if blocked_path.exists() else {}
    regression = load_json(regression_path) if regression_path.exists() else {}
    suggestions = load_json(suggestions_path) if suggestions_path.exists() else {}

    facts = record.get("本轮已通过事实", [])
    add_check(checks, "候选记录包含10条通过事实", len(facts) == 10, len(facts))
    add_check(checks, "封版候选状态正确", record.get("封版候选状态") == "candidate_freeze_only", record.get("封版候选状态"))
    add_check(checks, "需总管确认后才能升级", record.get("需总管确认后才能升级") is True, record.get("需总管确认后才能升级"))

    available_items = available.get("可用能力候选", [])
    available_names = " ".join(item.get("能力名称", "") + item.get("通过事实", "") for item in available_items)
    add_check(checks, "可用能力候选数量为8", available.get("能力数量") == 8 and len(available_items) == 8, available.get("能力数量"))
    for keyword in ["企业微信", "19310", "19302", "税收", "职责分流", "股票", "视频", "n8n"]:
        add_check(checks, f"可用能力覆盖{keyword}", keyword in available_names, keyword)

    blocked_items = blocked.get("仍阻断能力候选", [])
    blocked_text = " ".join(item.get("能力名称", "") + item.get("当前口径", "") for item in blocked_items)
    add_check(checks, "仍阻断能力候选数量为10", blocked.get("阻断能力数量") == 10 and len(blocked_items) == 10, blocked.get("阻断能力数量"))
    for keyword in ["真实发送", "n8n", "服务重载", "券商", "交易", "电子税务局", "财税软件", "真实渲染", "真实发布", "总管面板"]:
        add_check(checks, f"阻断能力覆盖{keyword}", keyword in blocked_text, keyword)

    regression_items = regression.get("回归建议", [])
    add_check(checks, "后续回归建议不少于8条", len(regression_items) >= 8, len(regression_items))
    add_check(checks, "所有回归建议有禁止动作", all(bool(item.get("禁止动作")) for item in regression_items), len(regression_items))

    suggestion_items = suggestions.get("验收建议", [])
    add_check(checks, "只读验收建议不少于6条", len(suggestion_items) >= 6, len(suggestion_items))
    add_check(checks, "只读验收禁止动作包含服务重载", "触发服务重载" in suggestions.get("只读验收禁止动作", []), suggestions.get("只读验收禁止动作"))

    forbidden_keys = [
        "写正式规则",
        "修改运行配置",
        "触发服务重载",
        "真实发送企业微信",
        "接n8n",
        "接券商",
        "交易",
        "登录电子税务局",
        "接财税软件",
        "修改总管面板",
        "修改一键接续包",
    ]
    add_check(checks, "候选记录红线关闭", safety_all_false(record.get("安全边界", {}), forbidden_keys), record.get("安全边界", {}))
    add_check(checks, "可用清单红线关闭", safety_all_false(available.get("安全边界", {}), forbidden_keys), available.get("安全边界", {}))
    add_check(checks, "阻断清单红线关闭", safety_all_false(blocked.get("安全边界", {}), forbidden_keys), blocked.get("安全边界", {}))
    add_check(checks, "回归建议红线关闭", safety_all_false(regression.get("安全边界", {}), forbidden_keys), regression.get("安全边界", {}))
    add_check(checks, "只读验收建议红线关闭", safety_all_false(suggestions.get("安全边界", {}), forbidden_keys), suggestions.get("安全边界", {}))

    touched_redline = {
        "写正式规则": False,
        "修改运行配置": False,
        "触发服务重载": False,
        "真实发送企业微信": False,
        "接n8n": False,
        "接券商": False,
        "交易": False,
        "登录电子税务局": False,
        "接财税软件": False,
        "修改总管面板": False,
        "修改一键接续包": False,
    }
    add_check(checks, "本验证未触碰红线", all(value is False for value in touched_redline.values()), touched_redline)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "multi-business-integration-passed-freeze-candidate-verify",
        "所属系统": "03杰哥进化系统",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": {
            "候选记录": str(record_path),
            "可用能力清单候选": str(available_path),
            "仍阻断能力清单候选": str(blocked_path),
            "后续回归测试建议": str(regression_path),
            "只读验收建议": str(suggestions_path),
            "回传报告": str(report_path)
        },
        "红线动作": touched_redline,
    }
    output = log_dir / f"multi-business-integration-passed-freeze-candidate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "multi-business-integration-passed-freeze-candidate-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
