# -*- coding: utf-8 -*-
"""
名称：验证闸口纠偏持续施工规则包.py
作用：验证闸口纠偏持续施工规则包已生成，且正确区分自动继续、先纠偏再继续和继续硬阻断。
触发方式：python 验证闸口纠偏持续施工规则包.py
依赖：Python标准库；生成闸口纠偏持续施工规则包.py。
所属系统：03杰哥进化系统
安全边界：只运行本地生成和验收；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建闸口纠偏持续施工规则包验收脚本。
标识：evolution-gate-correction-continuous-work-verify
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


def main() -> int:
    root = system_root()
    generator = root / "02脚本" / "生成闸口纠偏持续施工规则包.py"
    latest_json = root / "03数据" / "09闸口纠偏" / "闸口纠偏持续施工规则包_最新.json"
    latest_md = root / "03数据" / "09闸口纠偏" / "闸口纠偏持续施工规则包_最新.md"
    log_dir = root / "04日志" / "闸口纠偏验收"

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
    decision = report.get("持续施工判定", {})
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    correction_items = report.get("可自动纠偏的过期闸口", [])
    hard_blocks = report.get("仍需硬阻断的真实动作", [])

    add_check(checks, "用户最新口径已记录", "不要拘泥旧规定" in report.get("用户最新口径", ""), report.get("用户最新口径", ""))
    add_check(checks, "过期闸口纠偏不少于4项", len(correction_items) >= 4, len(correction_items))
    add_check(checks, "持续施工判定包含自动继续", len(decision.get("自动继续", [])) >= 5, decision)
    add_check(checks, "持续施工判定包含先纠偏再继续", len(decision.get("先纠偏再继续", [])) >= 3, decision)
    add_check(checks, "持续施工判定包含继续阻断", len(decision.get("继续阻断", [])) >= 3, decision)
    add_check(checks, "硬阻断保留交易和资金动作", all(item in hard_blocks for item in ["券商接口", "自动交易", "下单", "资金账户配置"]), hard_blocks)
    add_check(checks, "低风险本地施工允许继续", "03进化系统本地规则候选" in decision.get("自动继续", []), decision)
    add_check(checks, "小样本验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未修改股票系统业务脚本", safety.get("修改股票系统业务脚本") is False, safety)
    add_check(checks, "未修改总管进度口径", safety.get("修改总管进度口径") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-gate-correction-continuous-work-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-gate-correction-continuous-work-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-gate-correction-continuous-work-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
