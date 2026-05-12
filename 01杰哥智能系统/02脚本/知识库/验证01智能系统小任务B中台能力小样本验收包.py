# -*- coding: utf-8 -*-
"""
验证 01 智能系统小任务 B 小样本验收包。

验证范围：
- 报告、JSON、样本数量、异常降级、安全边界。
- 不接真实外部 API，不触发 n8n，不发送企业微信，不调用券商接口，不自动交易，不写正式库。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
SCRIPT_DIR = SMART_ROOT / "02脚本" / "知识库"
GENERATOR = SCRIPT_DIR / "生成01智能系统小任务B中台能力小样本验收包.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "14小任务B中台能力验收"
REPORT_JSON = DATA_DIR / "01智能系统小任务B中台能力验收_最新.json"
REPORT_MD = DATA_DIR / "01智能系统小任务B中台能力验收_最新.md"
DOC_PATH = SMART_ROOT / "07文档" / "01智能系统小任务B中台能力补齐小样本验收报告_最新.md"
VERIFY_JSON = DATA_DIR / "01智能系统小任务B中台能力验收_验证结果_最新.json"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_本轮小任务B回收报告_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def update_recycle(report: dict[str, Any], verify: dict[str, Any]) -> None:
    lines = [
        "【施工框名称】01智能系统小任务B：知识检索 + 中台能力 + 异常处理闭环小样本验收",
        f"【施工批次/时间】{report.get('generated_at', '')}",
        "【负责范围】仅 01杰哥智能系统授权目录与固定并行回收报告。",
        "【新增/修改文件】",
    ]
    for path in report.get("outputs", {}).values():
        lines.append(f"- {path}")
    lines.extend(
        [
            f"- {VERIFY_JSON}",
            "【验收方式】运行 验证01智能系统小任务B中台能力小样本验收包.py，检查报告、JSON、样本数量、异常降级、安全边界。",
            f"【验收结果】{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}",
            f"【阻断项数量】{report.get('acceptance', {}).get('blocked_count', 0)}",
            "【安全边界】未触发 n8n；未发送企业微信真实消息；未调用券商接口；未自动交易；未写正式库；未修改股票核心脚本；未修改 00 总管进度入口；未修改 02/03 系统。",
            "【后续正式接入口径】由总管回收后统一决定；建议先做只读 API 契约、影子流量、灰度门禁和人工确认，再考虑接入正式入口。",
            "【阻断项】0 个不可继续阻断；2 个高风险动作样本已按规则阻断。",
            "",
        ]
    )
    write_text(RECYCLE_PATH, "\n".join(lines))


def main() -> int:
    generator_result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    report = load_json(REPORT_JSON)
    samples = report.get("samples", [])
    capabilities = report.get("capabilities", [])
    exception_strategy = report.get("exception_strategy", [])
    safety = report.get("safety_boundary", {})
    output_paths = report.get("outputs", {})

    checks: list[dict[str, Any]] = []
    add(checks, "生成脚本返回码为0", generator_result.returncode == 0, generator_result.stderr)
    add(checks, "最新JSON存在", REPORT_JSON.exists(), str(REPORT_JSON))
    add(checks, "最新Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add(checks, "07文档报告存在", DOC_PATH.exists(), str(DOC_PATH))
    add(checks, "固定回收报告存在", RECYCLE_PATH.exists(), str(RECYCLE_PATH))
    add(checks, "能力清单不少于6项", len(capabilities) >= 6, len(capabilities))
    add(checks, "样本数量不少于4项", len(samples) >= 4, len(samples))
    add(checks, "包含知识检索样本", any(item.get("expected_route") == "知识检索" for item in samples), samples)
    add(checks, "包含状态读取样本", any(item.get("expected_route") == "状态读取" for item in samples), samples)
    add(checks, "包含高风险阻断样本", any(item.get("sample_output", {}).get("mode") == "blocked" for item in samples), samples)
    add(checks, "至少2个阻断样本", sum(1 for item in samples if item.get("sample_output", {}).get("mode") == "blocked") >= 2, samples)
    add(checks, "每个样本都有异常降级", all(item.get("fallback") for item in samples), samples)
    add(checks, "异常降级策略不少于4项", len(exception_strategy) >= 4, exception_strategy)
    add(checks, "后续正式接入口径完整", all(item.get("formal_ingress") for item in capabilities), capabilities)
    add(checks, "输出文件均在授权范围或固定回收路径", all(str(path).startswith(str(SMART_ROOT / "03数据")) or str(path).startswith(str(SMART_ROOT / "07文档")) or str(path) == str(RECYCLE_PATH) for path in output_paths.values()), output_paths)
    add(checks, "不触发n8n", safety.get("trigger_n8n") is False, safety)
    add(checks, "不发企业微信真实消息", safety.get("send_wecom_real_message") is False, safety)
    add(checks, "不调用券商接口", safety.get("call_broker_api") is False, safety)
    add(checks, "不自动交易", safety.get("auto_trade") is False, safety)
    add(checks, "不写正式库", safety.get("write_production_db") is False and safety.get("write_formal_vector_db") is False, safety)
    add(checks, "不修改股票核心脚本", safety.get("modify_stock_core_script") is False, safety)
    add(checks, "不修改00进度入口", safety.get("modify_00_progress_entry") is False, safety)
    add(checks, "不修改02/03系统", safety.get("modify_02_or_03_system") is False, safety)

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    verify = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": "01智能系统小任务B中台能力补齐小样本验收验证",
        "result": "通过" if failed == 0 else "失败",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": failed,
        "checks": checks,
        "report_json": str(REPORT_JSON),
        "report_markdown": str(REPORT_MD),
        "safety_boundary": safety,
        "blocked_count": report.get("acceptance", {}).get("blocked_count", 0),
    }
    write_json(VERIFY_JSON, verify)
    update_recycle(report, verify)
    print(json.dumps({"result": verify["result"], "passed": passed, "failed": failed, "verify_json": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
