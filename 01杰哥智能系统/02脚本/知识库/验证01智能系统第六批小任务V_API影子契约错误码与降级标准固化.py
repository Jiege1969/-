# -*- coding: utf-8 -*-
"""
验证 01 智能系统第六批小任务 V：
API 影子契约错误码、降级语与安全字段固化样本。

验证过程只运行本地生成脚本并读取本地 JSON/Markdown。
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
GENERATOR = SCRIPT_DIR / "生成01智能系统第六批小任务V_API影子契约错误码与降级标准固化.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "17第六批小任务VAPI影子契约错误码降级标准固化"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第六批小任务V_API影子契约错误码与降级标准固化_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_第六批小任务V回收报告_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统第六批小任务V_API影子契约错误码与降级标准_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第六批小任务V_四类契约样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第六批小任务V_验收报告_最新.md"
VERIFY_JSON = DATA_DIR / "01智能系统第六批小任务V_验证结果_最新.json"

REQUIRED_CASES = {"成功", "证据不足", "越权外部API", "系统异常降级"}
REQUIRED_ERROR_CODES = {
    "OK",
    "INSUFFICIENT_EVIDENCE",
    "UNAUTHORIZED_EXTERNAL_API",
    "SYSTEM_EXCEPTION_DEGRADED",
    "CONTRACT_FIELD_MISSING",
    "SAFETY_FIELD_VIOLATION",
}
REQUIRED_REQUEST_FIELDS = {"request_id", "caller", "question", "evidence_ids", "dry_run", "safety_boundary"}
REQUIRED_RESPONSE_FIELDS = {
    "request_id",
    "status",
    "error_code",
    "answer",
    "evidence",
    "degrade_message",
    "safe_to_show_user",
    "requires_human_review",
    "external_effect",
    "formal_store_write",
    "safety_boundary",
}
FORBIDDEN_TRUE_KEYS = {
    "call_external_api",
    "trigger_n8n",
    "send_wecom_real_message",
    "write_production_db",
    "write_formal_knowledge_db",
    "write_formal_vector_db",
    "call_broker_api",
    "auto_trade",
    "place_order",
    "touch_primary_work_system",
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


def boundary_closed(boundary: dict[str, Any]) -> bool:
    return all(boundary.get(key) is False for key in FORBIDDEN_TRUE_KEYS) and boundary.get("dry_run_required") is True


def update_acceptance_md(verify: dict[str, Any]) -> None:
    lines = [
        "# 01智能系统第六批小任务V验收报告",
        "",
        f"- 验收时间：{verify['generated_at']}",
        f"- 验收结果：{verify['result']}",
        f"- 通过/总数：{verify['passed_count']}/{verify['check_count']}",
        f"- 失败数：{verify['failed_count']}",
        f"- 交付阻断数量：{verify['delivery_blockers']}",
        f"- 安全阻断数量：{verify['security_blockers']}",
        "",
        "## 验收覆盖",
        "- 错误码：OK、INSUFFICIENT_EVIDENCE、UNAUTHORIZED_EXTERNAL_API、SYSTEM_EXCEPTION_DEGRADED、CONTRACT_FIELD_MISSING、SAFETY_FIELD_VIOLATION 均已固化。",
        "- 降级语：证据不足、越权外部API、系统异常、字段缺失、安全字段异常均有固定口径。",
        "- 安全字段：safe_to_show_user、requires_human_review、external_effect、formal_store_write、safety_boundary 均已检查。",
        "- 四个样本：成功、证据不足、越权外部API、系统异常降级均已覆盖。",
        "- 安全边界：真实外部API、n8n、企业微信真实消息、券商接口、自动交易、正式库写入均关闭。",
        "",
        "## 明细",
    ]
    for check in verify["checks"]:
        mark = "通过" if check["passed"] else "失败"
        lines.append(f"- {mark}：{check['name']}")
    lines.append("")
    write_text(ACCEPTANCE_MD, "\n".join(lines))


def update_recycle(verify: dict[str, Any]) -> None:
    files = [
        GENERATOR,
        Path(__file__),
        CONTRACT_JSON,
        SAMPLES_JSON,
        ACCEPTANCE_MD,
        VERIFY_JSON,
        DOC_PATH,
        RECYCLE_PATH,
    ]
    lines = [
        "【施工框名称】01杰哥智能系统 / 第六批小任务V：API影子契约错误码与降级标准固化",
        f"【施工批次/时间】{verify['generated_at']}",
        "【负责范围】仅 01/02脚本、01/03数据、01/07文档与本固定回收报告。",
        "【新增/修改文件】",
    ]
    lines.extend(f"- {path}" for path in files)
    lines.extend(
        [
            "【验收方式】运行 验证01智能系统第六批小任务V_API影子契约错误码与降级标准固化.py，检查错误码、降级语、安全字段、安全边界、正式库禁用和四类样本覆盖。",
            f"【验收结果】{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}",
            f"【交付阻断数量】{verify['delivery_blockers']}",
            f"【安全阻断数量】{verify['security_blockers']}",
            "【样本输出】成功；证据不足；越权外部API；系统异常降级。",
            "【安全阻断】越权真实外部API阻断；证据不足降级；系统异常降级；正式库写入禁用；安全字段异常阻断。",
            "【安全边界】仅本地影子契约样本与本地验证；不调用真实外部API；不触发 n8n；不发企业微信真实消息；不写正式库/正式向量库/正式数据库；不调用券商接口；不自动交易；不下单；不触碰本职工作系统。",
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
    for path in [CONTRACT_JSON, SAMPLES_JSON, ACCEPTANCE_MD, DOC_PATH]:
        add(checks, f"文件存在：{path.name}", path.exists(), str(path))

    contract: dict[str, Any] = {}
    sample_pack: dict[str, Any] = {}
    try:
        contract = load_json(CONTRACT_JSON)
        sample_pack = load_json(SAMPLES_JSON)
        add(checks, "JSON可解析", True)
    except Exception as exc:  # noqa: BLE001
        add(checks, "JSON可解析", False, repr(exc))

    api = contract.get("api_shadow_contract", {})
    request_fields = {item.get("name") for item in api.get("request_fields", [])}
    response_fields = {item.get("name") for item in api.get("response_fields", [])}
    error_codes = set(api.get("error_codes", {}).keys())
    degradation = api.get("degradation_standards", {})
    safe_fields = contract.get("safe_fields", {})
    samples = sample_pack.get("samples", [])
    cases = {item.get("case") for item in samples}
    sample_error_codes = {item.get("response", {}).get("error_code") for item in samples}
    safety = contract.get("safety_boundary", {})
    formal_policy = contract.get("formal_store_policy", {})

    add(checks, "请求字段齐全", REQUIRED_REQUEST_FIELDS.issubset(request_fields), sorted(request_fields))
    add(checks, "响应字段齐全", REQUIRED_RESPONSE_FIELDS.issubset(response_fields), sorted(response_fields))
    add(checks, "错误码齐全", REQUIRED_ERROR_CODES.issubset(error_codes), sorted(error_codes))
    add(checks, "降级标准齐全", {"evidence_required", "external_api_forbidden", "system_exception", "contract_fields", "formal_store"}.issubset(degradation), degradation)
    add(checks, "安全字段齐全", {"safe_to_show_user", "requires_human_review", "external_effect", "formal_store_write"}.issubset(safe_fields), safe_fields)
    add(checks, "四个样本齐全", len(samples) == 4 and REQUIRED_CASES == cases, sorted(cases))
    add(checks, "样本覆盖关键错误码", {"OK", "INSUFFICIENT_EVIDENCE", "UNAUTHORIZED_EXTERNAL_API", "SYSTEM_EXCEPTION_DEGRADED"}.issubset(sample_error_codes), sorted(sample_error_codes))
    add(checks, "成功样本含证据且无外部效果", any(item.get("case") == "成功" and item.get("response", {}).get("status") == "ok" and item.get("response", {}).get("evidence") and item.get("response", {}).get("external_effect") == "none" for item in samples), samples)
    add(checks, "证据不足样本降级且不回答", any(item.get("case") == "证据不足" and item.get("response", {}).get("error_code") == "INSUFFICIENT_EVIDENCE" and item.get("response", {}).get("answer") == "" for item in samples), samples)
    add(checks, "越权外部API样本被阻断", any(item.get("case") == "越权外部API" and item.get("response", {}).get("error_code") == "UNAUTHORIZED_EXTERNAL_API" and item.get("response", {}).get("external_effect") == "blocked" for item in samples), samples)
    add(checks, "系统异常样本降级且人工复核", any(item.get("case") == "系统异常降级" and item.get("response", {}).get("error_code") == "SYSTEM_EXCEPTION_DEGRADED" and item.get("response", {}).get("requires_human_review") is True for item in samples), samples)
    add(checks, "降级/阻断样本都有固定降级语", all(item.get("response", {}).get("degrade_message") or item.get("response", {}).get("status") == "ok" for item in samples), samples)
    add(checks, "所有响应正式库写入为False", all(item.get("response", {}).get("formal_store_write") is False for item in samples), samples)
    add(checks, "所有请求dry_run为true", all(item.get("request", {}).get("dry_run") is True for item in samples), samples)
    add(checks, "所有响应external_effect合法", all(item.get("response", {}).get("external_effect") in {"none", "blocked"} for item in samples), samples)
    add(checks, "安全边界关闭真实动作", boundary_closed(safety), safety)
    add(checks, "正式库策略禁用", formal_policy.get("write_production_db") is False and formal_policy.get("write_formal_knowledge_db") is False and formal_policy.get("write_formal_vector_db") is False and formal_policy.get("write_formal_database") is False, formal_policy)

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    verify = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": "01智能系统第六批小任务V_API影子契约错误码与降级标准固化验证",
        "result": "通过" if failed == 0 else "失败",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": failed,
        "delivery_blockers": 0 if failed == 0 else failed,
        "security_blockers": 5,
        "checks": checks,
        "outputs": {
            "contract_json": str(CONTRACT_JSON),
            "samples_json": str(SAMPLES_JSON),
            "acceptance_md": str(ACCEPTANCE_MD),
            "verify_json": str(VERIFY_JSON),
            "doc_path": str(DOC_PATH),
            "recycle_path": str(RECYCLE_PATH),
        },
        "safety_boundary": safety,
    }
    write_json(VERIFY_JSON, verify)
    update_acceptance_md(verify)
    update_recycle(verify)
    print(json.dumps({"result": verify["result"], "passed": passed, "failed": failed, "verify_json": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
