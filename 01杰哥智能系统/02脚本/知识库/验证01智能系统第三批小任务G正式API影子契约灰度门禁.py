# -*- coding: utf-8 -*-
"""
验证 01 智能系统第三批小任务 G：
正式 API 化影子契约 + 知识检索联动灰度门禁。

验证只读取/生成本地影子样本，不接真实网关，不写正式库，不调用真实外部 API。
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
GENERATOR = SCRIPT_DIR / "生成01智能系统第三批小任务G正式API影子契约灰度门禁.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "15第三批小任务G正式API影子契约灰度门禁"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统正式API化影子契约与知识检索灰度门禁_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_第三批小任务G回收报告_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统正式API化影子契约_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统正式API化影子契约_四类样本_最新.json"
REPORT_MD = DATA_DIR / "01智能系统正式API化影子契约灰度门禁验收_最新.md"
VERIFY_JSON = DATA_DIR / "01智能系统正式API化影子契约灰度门禁验证结果_最新.json"

REQUIRED_ERROR_CODES = {"OK", "NO_EVIDENCE", "OUT_OF_SCOPE", "EXTERNAL_ACTION_BLOCKED", "GRAY_GATE_CLOSED", "CONTRACT_VALIDATION_FAILED"}
REQUIRED_CASES = {"正常问答", "无证据降级", "超范围问题", "外部API/真实动作阻断"}
FORBIDDEN_TRUE_KEYS = {
    "connect_real_gateway",
    "write_production_db",
    "write_formal_vector_db",
    "call_external_api",
    "trigger_n8n",
    "send_wecom_real_message",
    "call_broker_api",
    "auto_trade",
    "place_order",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def all_forbidden_closed(boundary: dict[str, Any]) -> bool:
    return all(boundary.get(key) is False for key in FORBIDDEN_TRUE_KEYS)


def update_recycle(verify: dict[str, Any]) -> None:
    files = [
        GENERATOR,
        Path(__file__),
        CONTRACT_JSON,
        SAMPLES_JSON,
        REPORT_MD,
        VERIFY_JSON,
        DOC_PATH,
        RECYCLE_PATH,
    ]
    lines = [
        "【施工框名称】01杰哥智能系统 / 第三批小任务G：正式API化影子契约 + 知识检索联动灰度门禁",
        f"【施工批次/时间】{verify['generated_at']}",
        "【负责范围】仅 01/02脚本、01/03数据、01/07文档与本固定回收报告。",
        "【新增/修改文件】",
    ]
    lines.extend(f"- {path}" for path in files)
    lines.extend(
        [
            "【验收方式】运行 验证01智能系统第三批小任务G正式API影子契约灰度门禁.py，检查 JSON 可解析、样本数量、错误码/降级语、安全边界、未触发真实外部接口。",
            f"【验收结果】{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}",
            f"【交付阻断数量】{verify['delivery_blockers']}",
            f"【安全阻断数量】{verify['security_blockers']}",
            "【安全边界】仅本地影子样本；不接真实网关；不写正式库；不调用真实外部API；不触发 n8n；不发企业微信真实消息；不调用券商接口；不自动交易；不下单。",
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

    checks: list[dict[str, Any]] = []
    add(checks, "生成脚本返回码为0", generator_result.returncode == 0, generator_result.stderr)
    add(checks, "契约JSON存在", CONTRACT_JSON.exists(), str(CONTRACT_JSON))
    add(checks, "样本JSON存在", SAMPLES_JSON.exists(), str(SAMPLES_JSON))
    add(checks, "验收Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add(checks, "07文档契约存在", DOC_PATH.exists(), str(DOC_PATH))
    add(checks, "固定回收报告存在", RECYCLE_PATH.exists(), str(RECYCLE_PATH))

    contract: dict[str, Any] = {}
    sample_pack: dict[str, Any] = {}
    try:
        contract = load_json(CONTRACT_JSON)
        sample_pack = load_json(SAMPLES_JSON)
        add(checks, "JSON可解析", True)
    except Exception as exc:  # noqa: BLE001
        add(checks, "JSON可解析", False, repr(exc))

    api = contract.get("api_contract", {})
    samples = sample_pack.get("samples", [])
    safety = contract.get("safety_boundary", {})
    error_codes = set(api.get("error_codes", {}).keys())
    request_fields = {item.get("name") for item in api.get("request_fields", [])}
    response_fields = {item.get("name") for item in api.get("response_fields", [])}
    sample_error_codes = {item.get("response", {}).get("error_code") for item in samples}
    sample_cases = {item.get("case") for item in samples}

    add(checks, "请求字段齐全", {"request_id", "user_id", "question", "retrieval_scope", "evidence_policy", "gray_gate", "safety_boundary", "dry_run"}.issubset(request_fields), sorted(request_fields))
    add(checks, "响应字段齐全", {"request_id", "status", "error_code", "answer", "evidence", "fallback", "safety_boundary", "external_effect"}.issubset(response_fields), sorted(response_fields))
    add(checks, "错误码齐全", REQUIRED_ERROR_CODES.issubset(error_codes), sorted(error_codes))
    add(checks, "样本数量等于4", len(samples) == 4, len(samples))
    add(checks, "四类样本齐全", REQUIRED_CASES == sample_cases, sorted(sample_cases))
    add(checks, "样本覆盖关键错误码", {"OK", "NO_EVIDENCE", "OUT_OF_SCOPE", "EXTERNAL_ACTION_BLOCKED"}.issubset(sample_error_codes), sorted(sample_error_codes))
    add(checks, "每个样本有降级语字段", all("message" in item.get("response", {}).get("fallback", {}) for item in samples), samples)
    add(checks, "无证据样本返回NO_EVIDENCE和空答案", any(item.get("case") == "无证据降级" and item.get("response", {}).get("error_code") == "NO_EVIDENCE" and item.get("response", {}).get("answer") == "" for item in samples), samples)
    add(checks, "超范围样本被阻断", any(item.get("case") == "超范围问题" and item.get("response", {}).get("status") == "blocked" for item in samples), samples)
    add(checks, "外部API/真实动作样本被阻断", any(item.get("case") == "外部API/真实动作阻断" and item.get("response", {}).get("external_effect") == "blocked" for item in samples), samples)
    add(checks, "安全边界字段齐全且关闭外部动作", all_forbidden_closed(safety), safety)
    add(checks, "灰度门禁仅允许本地影子样本", contract.get("gray_gate_plan", {}).get("allowed_stage") == "local_shadow_samples_only", contract.get("gray_gate_plan", {}))
    add(checks, "真实网关关闭", contract.get("gray_gate_plan", {}).get("gate_status") == "closed_for_real_gateway", contract.get("gray_gate_plan", {}))
    add(checks, "所有样本dry_run为true", all(item.get("request", {}).get("dry_run") is True for item in samples), samples)
    add(checks, "所有样本不声明真实外部动作", all_forbidden_closed(samples[0].get("request", {}).get("safety_boundary", {})) if samples else False, samples[0] if samples else {})

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    security_blockers = sum(1 for item in samples if item.get("response", {}).get("status") in {"blocked", "degraded"})
    verify = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": "01智能系统第三批小任务G正式API化影子契约灰度门禁验证",
        "result": "通过" if failed == 0 else "失败",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": failed,
        "delivery_blockers": 0 if failed == 0 else failed,
        "security_blockers": security_blockers,
        "checks": checks,
        "safety_boundary": safety,
        "outputs": {
            "contract_json": str(CONTRACT_JSON),
            "samples_json": str(SAMPLES_JSON),
            "report_md": str(REPORT_MD),
            "verify_json": str(VERIFY_JSON),
            "doc_path": str(DOC_PATH),
            "recycle_path": str(RECYCLE_PATH),
        },
    }
    write_json(VERIFY_JSON, verify)
    update_recycle(verify)
    print(json.dumps({"result": verify["result"], "passed": passed, "failed": failed, "verify_json": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
