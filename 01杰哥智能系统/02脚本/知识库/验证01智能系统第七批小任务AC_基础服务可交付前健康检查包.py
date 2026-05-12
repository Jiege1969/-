# -*- coding: utf-8 -*-
"""
验证 01 智能系统第七批小任务 AC：
基础服务可交付前健康检查包。

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
GENERATOR = SCRIPT_DIR / "生成01智能系统第七批小任务AC_基础服务可交付前健康检查包.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "18第七批小任务AC基础服务可交付前健康检查包"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第七批小任务AC_基础服务可交付前健康检查包_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_第七批小任务AC健康检查回收报告_最新.md"

PACKAGE_JSON = DATA_DIR / "01智能系统第七批小任务AC_基础服务可交付前健康检查包_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第七批小任务AC_健康检查样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第七批小任务AC_验收报告_最新.md"
VERIFY_JSON = DATA_DIR / "01智能系统第七批小任务AC_验证结果_最新.json"

REQUIRED_HEALTH_ITEMS = {"API契约", "错误码", "降级", "知识检索联动", "日志字段", "异常处理"}
REQUIRED_ERROR_CODES = {
    "OK",
    "AC_CONTRACT_MISMATCH",
    "AC_ERROR_CODE_GAP",
    "AC_KNOWLEDGE_LINK_DEGRADED",
    "AC_LOG_FIELD_MISSING",
    "AC_EXCEPTION_UNHANDLED",
    "AC_SAFETY_BOUNDARY_VIOLATION",
}
REQUIRED_REQUEST_FIELDS = {"request_id", "caller", "health_scope", "knowledge_query", "dry_run", "safety_boundary"}
REQUIRED_RESPONSE_FIELDS = {
    "request_id",
    "status",
    "error_code",
    "health_result",
    "degrade_message",
    "fallback_action",
    "log_fields",
    "knowledge_link",
    "safe_to_show_user",
    "requires_human_review",
    "external_effect",
    "formal_store_write",
}
REQUIRED_LOG_FIELDS = {
    "trace_id",
    "request_id",
    "service_name",
    "operation",
    "health_check_item",
    "status",
    "error_code",
    "degrade_reason",
    "fallback_action",
    "knowledge_query_id",
    "evidence_ids",
    "evidence_count",
    "safe_to_show_user",
    "requires_human_review",
    "external_effect",
    "formal_store_write",
    "latency_ms",
    "timestamp",
}
REQUIRED_CASES = {"健康通过", "知识检索证据不足降级", "日志字段缺失阻断", "安全边界异常阻断"}
REQUIRED_EXCEPTIONS = {"contract_missing", "no_evidence", "local_exception", "safety_violation"}
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
        "# 01智能系统第七批小任务AC验收报告",
        "",
        f"- 验收时间：{verify['generated_at']}",
        f"- 验收结果：{verify['result']}",
        f"- 通过/总数：{verify['passed_count']}/{verify['check_count']}",
        f"- 失败数：{verify['failed_count']}",
        f"- 交付阻断数量：{verify['delivery_blockers']}",
        f"- 安全阻断数量：{verify['security_blockers']}",
        "",
        "## 验收覆盖",
        "- API契约：请求字段、响应字段、dry_run、安全边界字段已检查。",
        "- 错误码：OK、契约不一致、错误码缺口、知识检索降级、日志缺失、异常未处理、安全边界违规已覆盖。",
        "- 降级：无证据、契约不一致、日志缺失、本地异常、安全边界违规均有固定降级或阻断口径。",
        "- 知识检索联动：knowledge_query_id、evidence_ids、evidence_count、degrade_reason 已纳入日志和响应要求。",
        "- 日志字段：trace_id、request_id、service_name、operation、health_check_item、status、error_code 等全量字段已检查。",
        "- 异常处理：contract_missing、no_evidence、local_exception、safety_violation 已进入异常矩阵。",
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
        PACKAGE_JSON,
        SAMPLES_JSON,
        ACCEPTANCE_MD,
        VERIFY_JSON,
        DOC_PATH,
        RECYCLE_PATH,
    ]
    lines = [
        "【施工框名称】01杰哥智能系统 / 第七批小任务AC：基础服务可交付前健康检查包",
        f"【施工批次/时间】{verify['generated_at']}",
        "【负责范围】仅 01/02脚本、01/03数据、01/07文档与本固定回收报告。",
        "【新增/修改文件】",
    ]
    lines.extend(f"- {path}" for path in files)
    lines.extend(
        [
            "【验收方式】运行 验证01智能系统第七批小任务AC_基础服务可交付前健康检查包.py，检查 API契约、错误码、降级、知识检索联动、日志字段、异常处理、安全边界和四类样本覆盖。",
            f"【验收结果】{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}",
            f"【交付阻断数量】{verify['delivery_blockers']}",
            f"【安全阻断数量】{verify['security_blockers']}",
            "【样本输出】健康通过；知识检索证据不足降级；日志字段缺失阻断；安全边界异常阻断。",
            "【安全阻断】真实外部API阻断；n8n触发阻断；企业微信真实消息阻断；正式库写入禁用；券商接口/自动交易/下单阻断；本职工作系统触碰阻断。",
            "【安全边界】仅本地影子健康检查包与本地验证；不调用真实外部API；不触发 n8n；不发企业微信真实消息；不写正式库/正式知识库/正式向量库/正式数据库；不调用券商接口；不自动交易；不下单；不触碰本职工作系统。",
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
    for path in [PACKAGE_JSON, SAMPLES_JSON, ACCEPTANCE_MD, DOC_PATH]:
        add(checks, f"文件存在：{path.name}", path.exists(), str(path))

    package: dict[str, Any] = {}
    sample_pack: dict[str, Any] = {}
    try:
        package = load_json(PACKAGE_JSON)
        sample_pack = load_json(SAMPLES_JSON)
        add(checks, "JSON可解析", True)
    except Exception as exc:  # noqa: BLE001
        add(checks, "JSON可解析", False, repr(exc))

    health_items = {item.get("name") for item in package.get("health_items", [])}
    api_contract = package.get("api_contract", {})
    request_fields = {item.get("name") for item in api_contract.get("request_fields", [])}
    response_fields = {item.get("name") for item in api_contract.get("response_fields", [])}
    error_codes = package.get("error_codes", {})
    degradation_policy = package.get("degradation_policy", {})
    knowledge_link = package.get("knowledge_link", {})
    required_log_fields = set(package.get("required_log_fields", []))
    exception_matrix = package.get("exception_matrix", [])
    exception_names = {item.get("exception") for item in exception_matrix}
    samples = sample_pack.get("samples", [])
    cases = {sample.get("case") for sample in samples}
    sample_error_codes = {sample.get("log", {}).get("error_code") for sample in samples}
    safety = package.get("safety_boundary", {})

    add(checks, "六类健康检查项齐全", REQUIRED_HEALTH_ITEMS.issubset(health_items), sorted(health_items))
    add(checks, "请求字段齐全", REQUIRED_REQUEST_FIELDS.issubset(request_fields), sorted(request_fields))
    add(checks, "响应字段齐全", REQUIRED_RESPONSE_FIELDS.issubset(response_fields), sorted(response_fields))
    add(checks, "错误码齐全", REQUIRED_ERROR_CODES.issubset(error_codes), sorted(error_codes))
    add(checks, "错误码结构齐全", all({"status", "severity", "delivery_gate", "message"}.issubset(spec) for spec in error_codes.values()), error_codes)
    add(checks, "降级策略齐全", {"no_evidence", "contract_mismatch", "log_missing", "local_exception", "safety_violation"}.issubset(degradation_policy), degradation_policy)
    add(checks, "知识检索联动字段齐全", {"mode", "index_candidates", "required_response_fields", "no_evidence_policy"}.issubset(knowledge_link), knowledge_link)
    add(checks, "知识检索联动为本地只读", knowledge_link.get("mode") == "local_readonly_index_reference", knowledge_link)
    add(checks, "日志字段齐全", REQUIRED_LOG_FIELDS.issubset(required_log_fields), sorted(required_log_fields))
    add(checks, "异常矩阵齐全", REQUIRED_EXCEPTIONS.issubset(exception_names), sorted(exception_names))
    add(checks, "异常矩阵无真实外部效果", all(item.get("external_effect") in {"none", "blocked"} for item in exception_matrix), exception_matrix)
    add(checks, "四类样本齐全", len(samples) == 4 and REQUIRED_CASES == cases, sorted(cases))
    add(checks, "样本错误码覆盖关键路径", {"OK", "AC_KNOWLEDGE_LINK_DEGRADED", "AC_LOG_FIELD_MISSING", "AC_SAFETY_BOUNDARY_VIOLATION"}.issubset(sample_error_codes), sorted(sample_error_codes))
    add(checks, "每条样本日志字段齐全", all(REQUIRED_LOG_FIELDS.issubset(set(sample.get("log", {}).keys())) for sample in samples), samples)
    add(checks, "样本均不写正式库", all(sample.get("log", {}).get("formal_store_write") is False for sample in samples), samples)
    add(checks, "样本外部效果合法", all(sample.get("log", {}).get("external_effect") in {"none", "blocked"} for sample in samples), samples)
    add(checks, "知识证据不足样本降级且人工复核", any(sample.get("case") == "知识检索证据不足降级" and sample.get("log", {}).get("status") == "degraded" and sample.get("log", {}).get("requires_human_review") is True and sample.get("log", {}).get("evidence_count") == 0 for sample in samples), samples)
    add(checks, "安全边界异常样本被阻断", any(sample.get("case") == "安全边界异常阻断" and sample.get("log", {}).get("external_effect") == "blocked" for sample in samples), samples)
    add(checks, "安全边界关闭真实动作", boundary_closed(safety), safety)

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    verify = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": "01智能系统第七批小任务AC_基础服务可交付前健康检查包验证",
        "result": "通过" if failed == 0 else "失败",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": failed,
        "delivery_blockers": 0 if failed == 0 else failed,
        "security_blockers": 6,
        "checks": checks,
        "outputs": {
            "package_json": str(PACKAGE_JSON),
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
