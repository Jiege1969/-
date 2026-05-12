# -*- coding: utf-8 -*-
"""
名称：验证股票交付闭环规则沉淀自动评审小样本.py
作用：验证股票交付闭环规则沉淀与自动评审小样本生成成功，并确认验收检查字段、自动固化边界和安全边界完整。
触发方式：python 验证股票交付闭环规则沉淀自动评审小样本.py
依赖：Python标准库；生成股票交付闭环规则沉淀自动评审小样本.py。
所属系统：03杰哥进化系统
安全边界：只运行03本地生成和验收；不修改总管进度配置，不修改01智能系统中台代码，不修改02扩展系统业务脚本，不发送企业微信真实消息，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建规则沉淀与自动评审小样本验收脚本。
标识：evolution-stock-delivery-rule-deposit-auto-review-sample-verify
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
    generator = root / "02脚本" / "生成股票交付闭环规则沉淀自动评审小样本.py"
    latest_json = root / "03数据" / "21股票交付闭环规则沉淀自动评审小样本" / "股票交付闭环规则沉淀自动评审小样本_最新.json"
    latest_md = root / "03数据" / "21股票交付闭环规则沉淀自动评审小样本" / "股票交付闭环规则沉淀自动评审小样本_最新.md"
    log_dir = root / "04日志" / "股票交付闭环规则沉淀自动评审小样本验收"
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
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    report = load_json(latest_json) if latest_json.exists() else {}
    samples = report.get("规则沉淀小样本", [])
    sample = report.get("小样本验收", {})
    safety = report.get("安全边界", {})
    add_check(checks, "规则小样本数量为6", int(report.get("规则小样本数量", 0) or 0) == 6, report.get("规则小样本数量"))
    add_check(checks, "每条规则都有验收检查", all(item.get("验收检查", {}).get("验收检查ID") for item in samples), samples)
    add_check(checks, "问题复盘规则约束字段完整", sample.get("每条规则有问题复盘规则约束验收检查") is True, sample)
    add_check(checks, "自动评审场景数量为6", sample.get("自动评审场景数量为6") is True, sample)
    add_check(checks, "可自动固化数量为3", sample.get("可自动固化数量为3") is True, sample)
    add_check(checks, "人工确认数量为3", sample.get("人工确认数量为3") is True, sample)
    add_check(checks, "未误生成投资经验", sample.get("反馈等待机制未误生成投资经验") is True, sample)
    add_check(checks, "小样本验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未修改总管进度配置", safety.get("修改总管进度配置") is False, safety)
    add_check(checks, "未修改01智能系统中台代码", safety.get("修改01智能系统中台代码") is False, safety)
    add_check(checks, "未修改02扩展系统业务脚本", safety.get("修改02扩展系统业务脚本") is False, safety)
    add_check(checks, "未发送企业微信真实消息", safety.get("发送企业微信真实消息") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)
    add_check(checks, "未反向覆盖业务输出", safety.get("反向覆盖业务输出") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-rule-deposit-auto-review-sample-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-stock-delivery-rule-deposit-auto-review-sample-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-stock-delivery-rule-deposit-auto-review-sample-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
