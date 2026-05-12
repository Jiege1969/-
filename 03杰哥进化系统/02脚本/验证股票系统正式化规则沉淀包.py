# -*- coding: utf-8 -*-
"""
名称：验证股票系统正式化规则沉淀包.py
作用：验证用户明确提出的股票系统正式化规则已在03进化系统本地沉淀，并形成可验收检查项候选。
触发方式：python 验证股票系统正式化规则沉淀包.py
依赖：Python标准库；生成股票系统正式化规则沉淀包.py。
所属系统：03杰哥进化系统
安全边界：只运行03本地生成和验收；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建用户明确规则沉淀验收脚本。
标识：evolution-user-stock-formalization-rules-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
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


def contains_any(items: list[dict[str, Any]], field: str, words: list[str]) -> bool:
    return any(all(word in str(item.get(field, "")) for word in words) for item in items)


def main() -> int:
    root = system_root()
    generator = root / "02脚本" / "生成股票系统正式化规则沉淀包.py"
    latest_json = root / "03数据" / "16用户明确规则沉淀" / "股票系统正式化规则沉淀包_最新.json"
    latest_md = root / "03数据" / "16用户明确规则沉淀" / "股票系统正式化规则沉淀包_最新.md"
    log_dir = root / "04日志" / "用户明确规则沉淀验收"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON规则包存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown规则包存在", latest_md.exists(), str(latest_md))
    report = load_json(latest_json) if latest_json.exists() else {}
    rules = report.get("规则清单", [])
    candidates = report.get("本地检查项候选", [])
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    auto = report.get("自动固化建议", {})
    names = {item.get("规则名称") for item in rules}
    expected_names = {
        "正式覆盖前必须备份",
        "正式发送前必须白名单灰度",
        "影子验证通过后才能切正式口径",
        "_最新 文件必须有回滚证据",
        "企业微信、n8n、券商接口、自动交易必须分级隔离",
    }
    add_check(checks, "规则数量为5", int(report.get("规则数量", 0) or 0) == 5, report.get("规则数量"))
    add_check(checks, "五条用户明确规则全部存在", expected_names.issubset(names), sorted(names))
    add_check(checks, "硬边界数量不少于3", int(report.get("硬边界数量", 0) or 0) >= 3, report.get("硬边界数量"))
    add_check(checks, "自动检查数量不少于2", int(report.get("自动检查数量", 0) or 0) >= 2, report.get("自动检查数量"))
    add_check(checks, "包含正式覆盖备份约束", contains_any(rules, "下次施工约束", ["覆盖", "备份"]), rules)
    add_check(checks, "包含正式发送白名单灰度约束", contains_any(rules, "规则", ["白名单", "灰度"]), rules)
    add_check(checks, "包含影子验证切正式约束", contains_any(rules, "规则", ["影子验证", "正式口径"]), rules)
    add_check(checks, "包含_最新回滚证据约束", contains_any(rules, "规则", ["_最新", "回滚证据"]), rules)
    isolation_text = "\n".join(str(rule.get("规则", "")) + "\n" + str(rule.get("下次施工约束", "")) for rule in rules)
    add_check(checks, "分级隔离覆盖企业微信", "企业微信" in isolation_text, isolation_text)
    add_check(checks, "分级隔离覆盖n8n", "n8n" in isolation_text, isolation_text)
    add_check(checks, "分级隔离覆盖券商接口", "券商接口" in isolation_text, isolation_text)
    add_check(checks, "分级隔离覆盖自动交易", "自动交易" in isolation_text, isolation_text)
    add_check(checks, "本地检查项数量等于5", len(candidates) == 5, len(candidates))
    add_check(checks, "检查项ID唯一", len({item.get("检查项ID") for item in candidates}) == len(candidates), candidates)
    add_check(checks, "可自动固化规则明确", len(auto.get("可自动固化", [])) == 2, auto)
    add_check(checks, "人工确认或硬边界规则明确", len(auto.get("仍需人工确认或硬边界保留", [])) == 3, auto)
    add_check(checks, "小样本验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未写回股票系统", safety.get("写回股票系统") is False, safety)
    add_check(checks, "未修改股票脚本", safety.get("修改股票脚本") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-user-stock-formalization-rules-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-user-stock-formalization-rules-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-user-stock-formalization-rules-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
