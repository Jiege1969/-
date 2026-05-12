import json
import sys
from pathlib import Path


ARCHIVE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\14低风险小样本许可令只读归档入口一致性包")
ARCHIVE_JSON = ARCHIVE_DIR / "低风险小样本许可令只读归档入口一致性包_20260505_V.json"
ARCHIVE_MD = ARCHIVE_DIR / "低风险小样本许可令只读归档入口一致性包_20260505_V.md"
Q_JSON = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\13低风险小样本许可令只读签发草案包\低风险小样本许可令只读签发草案_20260505_Q.json")
N_JSON = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\03数据\13可用入口清单操作卡包\可用入口清单操作卡包_20260505_N.json")

EXPECTED_CANDIDATES = {
    "read_only_pull",
    "draft_generation",
    "internal_report_circulation",
}

EXPECTED_ENTRIES = {
    "stock_analysis",
    "enterprise_wechat_assistant",
    "knowledge_base_readonly_qa",
    "content_office_draft",
    "video_production_preplan",
    "tax_readonly_evidence_chain",
}

REQUIRED_FORBIDDEN = {
    "enterprise_wechat_scale_up",
    "n8n_formal_trigger",
    "formal_database_write",
    "real_media_conversion",
    "formal_tax_judgement",
    "broker_interface",
    "automatic_trading",
}

REQUIRED_FALSE_BOUNDARY_FLAGS = [
    "external_system_called",
    "enterprise_wechat_scale_up",
    "enterprise_wechat_real_send",
    "n8n_workflow_imported",
    "n8n_workflow_enabled",
    "n8n_formal_triggered",
    "production_database_written",
    "formal_knowledge_base_written",
    "vector_database_written",
    "real_media_converted",
    "tax_formal_judgement_made",
    "broker_interface_called",
    "automatic_trading_triggered",
]


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ids(items, key):
    return {item.get(key) for item in items}


def main():
    failures = []
    archive = load_json(ARCHIVE_JSON)
    q_package = load_json(Q_JSON)
    n_package = load_json(N_JSON)
    markdown = ARCHIVE_MD.read_text(encoding="utf-8")

    q_candidates = ids(q_package.get("only_allowed_future_candidates", []), "candidate_id")
    archive_candidates = ids(archive.get("candidate_classes", []), "candidate_id")
    if q_candidates != EXPECTED_CANDIDATES:
        failures.append(f"Q candidate set mismatch: {sorted(q_candidates)}")
    if archive_candidates != EXPECTED_CANDIDATES:
        failures.append(f"archive candidate set mismatch: {sorted(archive_candidates)}")

    n_entries = ids(n_package.get("entries", []), "entry_id")
    archive_entries = ids(archive.get("available_entries", []), "entry_id")
    if n_entries != EXPECTED_ENTRIES:
        failures.append(f"N entry set mismatch: {sorted(n_entries)}")
    if archive_entries != EXPECTED_ENTRIES:
        failures.append(f"archive entry set mismatch: {sorted(archive_entries)}")

    q_forbidden = ids(q_package.get("still_forbidden_actions", []), "action_id")
    archive_forbidden = ids(archive.get("still_forbidden_actions", []), "action_id")
    if not REQUIRED_FORBIDDEN.issubset(q_forbidden):
        failures.append(f"Q missing forbidden actions: {sorted(REQUIRED_FORBIDDEN - q_forbidden)}")
    if archive_forbidden != REQUIRED_FORBIDDEN:
        failures.append(f"archive forbidden set mismatch: {sorted(archive_forbidden)}")

    if archive.get("real_action_count") != 0:
        failures.append("archive real_action_count must be 0")

    boundary = archive.get("execution_boundary", {})
    if boundary.get("real_actions_triggered") != 0:
        failures.append("execution_boundary.real_actions_triggered must be 0")
    for flag in REQUIRED_FALSE_BOUNDARY_FLAGS:
        if boundary.get(flag) is not False:
            failures.append(f"execution boundary flag must be false: {flag}")

    write_scope = archive.get("write_scope_confirmation", {})
    if write_scope.get("extension_system_new_files_only") is not True:
        failures.append("extension_system_new_files_only must be true")
    if write_scope.get("other_workers_files_modified") is not False:
        failures.append("other_workers_files_modified must be false")
    if write_scope.get("work_system_touched") is not False:
        failures.append("work_system_touched must be false")
    if write_scope.get("work_system_status") != "paused":
        failures.append("work_system_status must be paused")

    for candidate in archive.get("candidate_classes", []):
        covered = set(candidate.get("covered_entry_ids", []))
        if covered != EXPECTED_ENTRIES:
            failures.append(f"{candidate.get('candidate_id')} coverage mismatch: {sorted(covered)}")

    for entry in archive.get("available_entries", []):
        entry_id = entry.get("entry_id", "<unknown>")
        mapped_candidates = set(entry.get("candidate_consistency", []))
        if mapped_candidates != EXPECTED_CANDIDATES:
            failures.append(f"{entry_id} candidate consistency mismatch: {sorted(mapped_candidates)}")
        if entry.get("consistent") is not True:
            failures.append(f"{entry_id} consistent must be true")
        if not entry.get("forbidden_action_alignment"):
            failures.append(f"{entry_id} missing forbidden_action_alignment")

    q_boundary = q_package.get("execution_boundary", {})
    if q_package.get("status") != "readonly_issuance_draft_only":
        failures.append("Q status must remain readonly_issuance_draft_only")
    if q_package.get("real_action_count") != 0:
        failures.append("Q real_action_count must be 0")
    if q_boundary.get("n8n_formal_triggered") is not False:
        failures.append("Q n8n_formal_triggered must be false")

    n_non_execution = n_package.get("non_execution_guarantee", {})
    if n_non_execution.get("real_actions_triggered") != 0:
        failures.append("N real_actions_triggered must be 0")
    if n_package.get("work_system_boundary", {}).get("touched") is not False:
        failures.append("N work system boundary must remain untouched")

    review = archive.get("consistency_review", {})
    for key in (
        "every_entry_maps_to_all_three_candidates",
        "every_candidate_covers_all_six_entries",
        "forbidden_actions_match_required_boundary",
        "n_entry_real_actions_remain_closed",
        "q_permission_remains_readonly_draft_only",
        "work_system_paused_and_untouched",
        "passed",
    ):
        if review.get(key) is not True:
            failures.append(f"consistency_review.{key} must be true")

    for term in (
        "只读拉取",
        "草稿生成",
        "内部报告流转",
        "股票分析",
        "企业微信助手",
        "知识库只读问答",
        "内容办公草稿",
        "视频制作预案",
        "税收只读证据链",
        "本职工作系统：暂停",
        "真实动作数量：0",
    ):
        if term not in markdown:
            failures.append(f"markdown missing term: {term}")

    result = {
        "archive_json": str(ARCHIVE_JSON),
        "archive_markdown": str(ARCHIVE_MD),
        "q_json": str(Q_JSON),
        "n_json": str(N_JSON),
        "checked_candidate_count": len(archive_candidates),
        "checked_candidates": sorted(archive_candidates),
        "checked_entry_count": len(archive_entries),
        "checked_entries": sorted(archive_entries),
        "checked_required_forbidden_actions": sorted(REQUIRED_FORBIDDEN),
        "every_entry_maps_to_all_three_candidates": not failures,
        "every_candidate_covers_all_six_entries": not failures,
        "real_actions_triggered": 0,
        "work_system_touched": False,
        "readonly_validation": True,
        "network_required": False,
        "writes_files": False,
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
