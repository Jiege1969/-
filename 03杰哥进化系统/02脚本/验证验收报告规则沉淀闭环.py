# -*- coding: utf-8 -*-
"""
名称：验证验收报告规则沉淀闭环.py
作用：验证验收报告规则沉淀闭环生成链路、闭环字段、自动/人工固化分级和安全边界。
触发方式：python 验证验收报告规则沉淀闭环.py
依赖：Python标准库；生成验收报告规则沉淀闭环.py。
所属系统：03杰哥进化系统
安全边界：只运行本地生成和验收；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建验收报告规则沉淀闭环验收脚本。
标识：evolution-acceptance-rule-loop-verify
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
    generator = root / "02脚本" / "生成验收报告规则沉淀闭环.py"
    latest_json = root / "03数据" / "08规则沉淀" / "验收报告规则沉淀闭环_最新.json"
    latest_md = root / "03数据" / "08规则沉淀" / "验收报告规则沉淀闭环_最新.md"
    log_dir = root / "04日志" / "规则沉淀验收"

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
    add_check(checks, "最新JSON闭环包存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown闭环包存在", latest_md.exists(), str(latest_md))

    report = load_json(latest_json) if latest_json.exists() else {}
    rules = report.get("提取规则", [])
    safety = report.get("安全边界", {})
    sample = report.get("小样本验收", {})
    assets = report.get("现有资产盘点", {})

    add_check(checks, "盘点现有复盘评审规则文件", int(assets.get("复盘评审规则固化相关文件数", 0) or 0) > 0, assets)
    add_check(checks, "来源覆盖股票系统", sample.get("跨系统覆盖", {}).get("股票系统报告") is True, sample)
    add_check(checks, "来源覆盖总管系统", sample.get("跨系统覆盖", {}).get("总管系统报告") is True, sample)
    add_check(checks, "提取规则不少于6条", len(rules) >= 6, len(rules))
    add_check(
        checks,
        "闭环字段完整",
        all(all(key in item and item.get(key) for key in ["问题", "复盘", "规则", "下次施工约束"]) for item in rules),
        [item.get("规则ID") for item in rules],
    )
    add_check(checks, "存在自动固化候选", len(report.get("自动固化规则", [])) >= 6, len(report.get("自动固化规则", [])))
    add_check(checks, "人工确认闸口已风险分级", any(item.get("固化级别") == "风险分级后固化" for item in rules), [item.get("固化级别") for item in rules])
    add_check(checks, "小样本验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未修改股票系统业务脚本", safety.get("修改股票系统业务脚本") is False, safety)
    add_check(checks, "未修改总管进度口径", safety.get("修改总管进度口径") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)
    add_check(checks, "未反向覆盖业务输出", safety.get("反向覆盖业务输出") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-acceptance-rule-loop-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
        "安全边界": {
            "修改股票系统业务脚本": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output = log_dir / f"evolution-acceptance-rule-loop-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-acceptance-rule-loop-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
