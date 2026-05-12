# 风险等级：R0
# 标识：READONLY
# 作用：只读验证清债请求是否具备源头审计、资产身份分类、写入风险评估和扫描边界材料。
# 禁止：不删除文件，不修改源头脚本，不运行 W1/W2/W3 脚本，不触发 n8n/企业微信/券商接口。

import argparse
import json
import sys
from pathlib import Path


DEFAULT_RULES = Path(r"D:\杰哥智能化系统\00杰哥系统总管\01配置\施工风险等级与清债许可规则.json")


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def as_path(value):
    if not value:
        return None
    return Path(str(value))


def check_required_documents(request, required_names):
    docs = request.get("documents") or {}
    results = []
    for name in required_names:
        path = as_path(docs.get(name))
        exists = bool(path and path.exists() and path.is_file())
        results.append({
            "name": name,
            "path": str(path) if path else "",
            "exists": exists,
        })
    return results


def check_boundary(request, required_boundary_names):
    boundary = request.get("scan_boundary") or {}
    results = []
    for name in required_boundary_names:
        value = boundary.get(name)
        ok = value is not None
        if name == "scan_scope":
            ok = isinstance(value, list) and len(value) > 0
        elif name == "hit_count":
            ok = isinstance(value, int) and value >= 0
        elif name == "uncovered_scope":
            ok = isinstance(value, list)
        results.append({
            "name": name,
            "present": ok,
            "value": value,
        })
    return results


def evaluate(rules, request):
    gate = rules.get("cleanup_permission_gate") or {}
    required_docs = gate.get("required_documents") or [
        "source_audit_report",
        "asset_identity_classification",
        "write_risk_assessment",
    ]
    required_boundary = gate.get("boundary_requirements") or [
        "scan_scope",
        "hit_count",
        "uncovered_scope",
    ]

    doc_results = check_required_documents(request, required_docs)
    boundary_results = check_boundary(request, required_boundary)

    missing_docs = [item for item in doc_results if not item["exists"]]
    missing_boundary = [item for item in boundary_results if not item["present"]]
    self_certification = str(request.get("self_certification", "")).lower() in {"true", "yes", "1"}
    requested_actions = request.get("requested_actions") or []
    requested_write = any(str(action).upper().startswith(("W1", "W2", "W3", "DELETE", "MODIFY", "MOVE")) for action in requested_actions)

    if missing_docs or missing_boundary or self_certification:
        permission = "DENY_WRITE_OPS_ALLOW_R0_ONLY"
        write_ops_allowed = False
        r0_only_allowed = True
    elif requested_write:
        permission = "READY_FOR_MANUAL_REVIEW"
        write_ops_allowed = False
        r0_only_allowed = True
    else:
        permission = "ALLOW_R0_ONLY"
        write_ops_allowed = False
        r0_only_allowed = True

    reasons = []
    if missing_docs:
        reasons.append("missing_required_documents")
    if missing_boundary:
        reasons.append("missing_scan_boundary")
    if self_certification:
        reasons.append("self_certification_forbidden")
    if requested_write and not (missing_docs or missing_boundary or self_certification):
        reasons.append("write_actions_require_manual_review")
    if not reasons:
        reasons.append("r0_request_materials_complete")

    return {
        "tool": "R0_verify_cleanup_permissions",
        "risk_level": "R0",
        "rules_version": rules.get("version"),
        "verification_script_status": (gate.get("verification_script_status") or "unknown"),
        "task_id": request.get("task_id", ""),
        "batch_id": request.get("batch_id", ""),
        "permission": permission,
        "write_ops_allowed": write_ops_allowed,
        "r0_only_allowed": r0_only_allowed,
        "reasons": reasons,
        "document_checks": doc_results,
        "boundary_checks": boundary_results,
        "requested_actions": requested_actions,
        "hard_intercept_integrated": False,
        "notes": [
            "This tool is read-only and only evaluates cleanup permission materials.",
            "READY_FOR_MANUAL_REVIEW is not write approval.",
            "No cleanup, deletion, source modification, service call, n8n trigger, WeCom send, broker API call, or model inference is performed."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="R0 read-only cleanup permission verifier")
    parser.add_argument("--request", required=True, help="Path to cleanup permission request JSON")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="Path to risk and cleanup permission rules JSON")
    args = parser.parse_args()

    rules_path = Path(args.rules)
    request_path = Path(args.request)

    if not rules_path.exists():
        print(json.dumps({"error": "rules_not_found", "path": str(rules_path)}, ensure_ascii=False, indent=2))
        return 2
    if not request_path.exists():
        print(json.dumps({"error": "request_not_found", "path": str(request_path)}, ensure_ascii=False, indent=2))
        return 2

    rules = read_json(rules_path)
    request = read_json(request_path)
    result = evaluate(rules, request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
