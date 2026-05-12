# -*- coding: utf-8 -*-
"""
验证 01 智能系统第五批小任务 P：
API 影子契约与知识库证据索引联动本地样本预案。

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
GENERATOR = SCRIPT_DIR / "生成01智能系统第五批小任务P_API影子契约证据索引联动样本.py"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "16第五批小任务PAPI影子契约证据索引联动"
DOC_PATH = SMART_ROOT / "07文档" / "API契约" / "01智能系统第五批小任务P_API影子契约与知识库证据索引联动预案_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_第五批小任务P回收报告_最新.md"

CONTRACT_JSON = DATA_DIR / "01智能系统第五批小任务P_API影子契约_最新.json"
EVIDENCE_INDEX_JSON = DATA_DIR / "01智能系统第五批小任务P_知识库证据索引联动样本_最新.json"
SAMPLES_JSON = DATA_DIR / "01智能系统第五批小任务P_四类联动样本_最新.json"
ACCEPTANCE_MD = DATA_DIR / "01智能系统第五批小任务P_验收报告_最新.md"
VERIFY_JSON = DATA_DIR / "01智能系统第五批小任务P_验证结果_最新.json"

REQUIRED_CASES = {"证据命中", "证据过旧降级", "无证据降级", "越权真实外部API阻断"}
REQUIRED_ERROR_CODES = {"OK", "STALE_EVIDENCE", "NO_EVIDENCE", "EXTERNAL_API_BLOCKED", "CONTRACT_FIELD_MISSING", "FORMAL_STORE_DISABLED"}
REQUIRED_REQUEST_FIELDS = {"request_id", "question", "evidence_query", "evidence_policy", "staleness_threshold_days", "dry_run", "safety_boundary"}
REQUIRED_RESPONSE_FIELDS = {"request_id", "status", "error_code", "answer", "evidence_hits", "degrade_message", "external_effect", "formal_store_write", "safety_boundary"}
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
    return all(boundary.get(key) is False for key in FORBIDDEN_TRUE_KEYS)


def update_acceptance_md(verify: dict[str, Any]) -> None:
    lines = [
        "# 01智能系统第五批小任务P验收报告",
        "",
        f"- 验收时间：{verify['generated_at']}",
        f"- 验收结果：{verify['result']}",
        f"- 通过/总数：{verify['passed_count']}/{verify['check_count']}",
        f"- 失败数：{verify['failed_count']}",
        f"- 交付阻断数量：{verify['delivery_blockers']}",
        f"- 安全阻断数量：{verify['security_blockers']}",
        "",
        "## 验收覆盖",
        "- 字段：请求字段、响应字段、证据命中字段、正式库写入字段均已检查。",
        "- 错误码：OK、STALE_EVIDENCE、NO_EVIDENCE、EXTERNAL_API_BLOCKED、CONTRACT_FIELD_MISSING、FORMAL_STORE_DISABLED 均已登记。",
        "- 降级语：证据过旧、无证据、越权外部API、正式库禁用均有固定口径。",
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
        EVIDENCE_INDEX_JSON,
        SAMPLES_JSON,
        ACCEPTANCE_MD,
        VERIFY_JSON,
        DOC_PATH,
        RECYCLE_PATH,
    ]
    lines = [
        "【施工框名称】01杰哥智能系统 / 第五批小任务P：API影子契约与知识库证据索引联动样本",
        f"【施工批次/时间】{verify['generated_at']}",
        "【负责范围】仅 01/02脚本、01/03数据、01/07文档与本固定回收报告。",
        "【新增/修改文件】",
    ]
    lines.extend(f"- {path}" for path in files)
    lines.extend(
        [
            "【验收方式】运行 验证01智能系统第五批小任务P_API影子契约证据索引联动样本.py，检查字段、错误码、降级语、安全边界、正式库禁用和四类样本覆盖。",
            f"【验收结果】{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}",
            f"【交付阻断数量】{verify['delivery_blockers']}",
            f"【安全阻断数量】{verify['security_blockers']}",
            "【安全阻断】越权真实外部API阻断；证据过旧降级；无证据降级；正式库写入禁用。",
            "【安全边界】仅本地影子样本与本地证据索引；不调用真实外部API；不触发 n8n；不发企业微信真实消息；不写正式库/正式向量库/正式数据库；不调用券商接口；不自动交易；不下单；不触碰本职工作系统。",
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
    for path in [CONTRACT_JSON, EVIDENCE_INDEX_JSON, SAMPLES_JSON, ACCEPTANCE_MD, DOC_PATH]:
        add(checks, f"文件存在：{path.name}", path.exists(), str(path))

    contract: dict[str, Any] = {}
    evidence_index: dict[str, Any] = {}
    sample_pack: dict[str, Any] = {}
    try:
        contract = load_json(CONTRACT_JSON)
        evidence_index = load_json(EVIDENCE_INDEX_JSON)
        sample_pack = load_json(SAMPLES_JSON)
        add(checks, "JSON可解析", True)
    except Exception as exc:  # noqa: BLE001
        add(checks, "JSON可解析", False, repr(exc))

    api = contract.get("api_shadow_contract", {})
    request_fields = {item.get("name") for item in api.get("request_fields", [])}
    response_fields = {item.get("name") for item in api.get("response_fields", [])}
    error_codes = set(api.get("error_codes", {}).keys())
    degrade_messages = api.get("degrade_messages", {})
    samples = sample_pack.get("samples", [])
    cases = {item.get("case") for item in samples}
    sample_error_codes = {item.get("response", {}).get("error_code") for item in samples}
    safety = contract.get("safety_boundary", {})
    formal_policy = contract.get("formal_store_policy", {})
    records = evidence_index.get("records", [])

    add(checks, "请求字段齐全", REQUIRED_REQUEST_FIELDS.issubset(request_fields), sorted(request_fields))
    add(checks, "响应字段齐全", REQUIRED_RESPONSE_FIELDS.issubset(response_fields), sorted(response_fields))
    add(checks, "错误码齐全", REQUIRED_ERROR_CODES.issubset(error_codes), sorted(error_codes))
    add(checks, "关键降级语齐全", {"STALE_EVIDENCE", "NO_EVIDENCE", "EXTERNAL_API_BLOCKED", "FORMAL_STORE_DISABLED"}.issubset(degrade_messages), degrade_messages)
    add(checks, "四个样本齐全", len(samples) == 4 and REQUIRED_CASES == cases, sorted(cases))
    add(checks, "样本覆盖关键错误码", {"OK", "STALE_EVIDENCE", "NO_EVIDENCE", "EXTERNAL_API_BLOCKED"}.issubset(sample_error_codes), sorted(sample_error_codes))
    add(checks, "证据命中样本含新鲜证据", any(item.get("case") == "证据命中" and item.get("response", {}).get("status") == "ok" and item.get("response", {}).get("evidence_hits") for item in samples), samples)
    add(checks, "证据过旧样本降级且不回答", any(item.get("case") == "证据过旧降级" and item.get("response", {}).get("error_code") == "STALE_EVIDENCE" and item.get("response", {}).get("answer") == "" for item in samples), samples)
    add(checks, "无证据样本降级且证据为空", any(item.get("case") == "无证据降级" and item.get("response", {}).get("error_code") == "NO_EVIDENCE" and item.get("response", {}).get("evidence_hits") == [] for item in samples), samples)
    add(checks, "越权真实外部API样本被阻断", any(item.get("case") == "越权真实外部API阻断" and item.get("response", {}).get("status") == "blocked" and item.get("response", {}).get("external_effect") == "blocked" for item in samples), samples)
    add(checks, "每个降级/阻断样本都有降级语", all(item.get("response", {}).get("degrade_message") or item.get("response", {}).get("status") == "ok" for item in samples), samples)
    add(checks, "所有响应正式库写入为False", all(item.get("response", {}).get("formal_store_write") is False for item in samples), samples)
    add(checks, "安全边界关闭真实动作", boundary_closed(safety), safety)
    add(checks, "正式库策略禁用", formal_policy.get("write_production_db") is False and formal_policy.get("write_formal_knowledge_db") is False and formal_policy.get("write_formal_vector_db") is False, formal_policy)
    add(checks, "证据索引含fresh和stale", {"fresh", "stale"}.issubset({item.get("freshness") for item in records}), records)
    add(checks, "所有请求dry_run为true", all(item.get("request", {}).get("dry_run") is True for item in samples), samples)

    passed = sum(1 for item in checks if item["passed"])
    failed = len(checks) - passed
    verify = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task": "01智能系统第五批小任务P_API影子契约证据索引联动样本验证",
        "result": "通过" if failed == 0 else "失败",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": failed,
        "delivery_blockers": 0 if failed == 0 else failed,
        "security_blockers": 4,
        "checks": checks,
        "outputs": {
            "contract_json": str(CONTRACT_JSON),
            "evidence_index_json": str(EVIDENCE_INDEX_JSON),
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
