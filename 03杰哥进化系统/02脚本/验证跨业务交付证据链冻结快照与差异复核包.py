# -*- coding: utf-8 -*-
"""验收跨业务交付证据链冻结快照与差异复核包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION / "03数据" / "94跨业务交付证据链冻结快照与差异复核包"
LOG_DIR = EVOLUTION / "04日志" / "跨业务交付证据链冻结快照与差异复核包验收"

SOURCE_JSON = DATA_DIR / "证据源清单_最新.json"
SOURCE_MD = DATA_DIR / "证据源清单_最新.md"
SNAPSHOT_JSON = DATA_DIR / "冻结快照_最新.json"
SNAPSHOT_MD = DATA_DIR / "冻结快照_最新.md"
BASELINE_JSON = DATA_DIR / "冻结基线_最新.json"
DIFF_JSON = DATA_DIR / "差异复核报告_最新.json"
DIFF_MD = DATA_DIR / "差异复核报告_最新.md"
PACKAGE_JSON = DATA_DIR / "跨业务交付证据链冻结快照与差异复核包_最新.json"
PACKAGE_MD = DATA_DIR / "跨业务交付证据链冻结快照与差异复核包_最新.md"
LATEST_LOG = LOG_DIR / "cross-business-delivery-evidence-freeze-diff-verify-最新.json"

REQUIRED_FILES = [SOURCE_JSON, SOURCE_MD, SNAPSHOT_JSON, SNAPSHOT_MD, BASELINE_JSON, DIFF_JSON, DIFF_MD, PACKAGE_JSON, PACKAGE_MD]
REQUIRED_CATEGORIES = {"企业微信公共接入层日常巡检", "股票展示口径一致性", "视频渲染发布阻断", "日常总回归", "自主巡检快照", "第八轮调度验收", "第九轮调度验收"}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"输出文件不存在: {path}")

    manifest = read_json(SOURCE_JSON) if SOURCE_JSON.exists() else {}
    snapshot = read_json(SNAPSHOT_JSON) if SNAPSHOT_JSON.exists() else {}
    diff = read_json(DIFF_JSON) if DIFF_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}

    sources = manifest.get("sources", [])
    categories = {source.get("category") for source in sources}
    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        errors.append("证据源清单缺少分类: " + ", ".join(missing_categories))

    for name, report in [("证据源清单", manifest), ("冻结快照", snapshot), ("差异复核", diff), ("总包", package)]:
        if report.get("readonly") is not True:
            errors.append(f"{name} readonly 必须为 true")

    if len(sources) < 10:
        errors.append("证据源数量不得少于 10")
    if snapshot.get("source_count") != len(sources):
        errors.append("冻结快照 source_count 与证据源清单不一致")
    if diff.get("source_count") != len(sources):
        errors.append("差异复核 source_count 与证据源清单不一致")

    snapshot_missing = int(snapshot.get("missing_count", 0) or 0)
    diff_missing = int(diff.get("missing_count", 0) or 0)
    diff_count = int(diff.get("diff_count", 0) or 0)
    missing_count = max(snapshot_missing, diff_missing)
    if snapshot_missing:
        errors.append(f"冻结快照存在缺失文件: {snapshot_missing}")
    if diff_missing:
        errors.append(f"差异复核存在缺失文件: {diff_missing}")
    if diff_count:
        errors.append(f"差异复核存在哈希差异: {diff_count}")

    for entry in snapshot.get("entries", []):
        if entry.get("exists") is not True:
            errors.append(f"证据文件不存在: {entry.get('id')} {entry.get('path')}")
        if not entry.get("sha256"):
            errors.append(f"证据文件缺少 sha256: {entry.get('id')}")
        if entry.get("size") is None:
            errors.append(f"证据文件缺少 size: {entry.get('id')}")
        if not entry.get("mtime"):
            errors.append(f"证据文件缺少 mtime: {entry.get('id')}")

    safety = package.get("safety_boundary") or manifest.get("safety_boundary") or {}
    if safety.get("readonly") is not True:
        errors.append("安全边界 readonly 必须为 true")
    for key in ["real_wecom_send", "connect_n8n", "trigger_n8n", "connect_broker", "trade", "login_tax_bureau", "connect_finance_tax_software", "promote_to_formal_rule", "modify_master_panel", "modify_one_click_continuation_package", "reload_service"]:
        if safety.get(key) is not False:
            errors.append(f"安全边界 {key} 必须为 false")

    report = {
        "name": "跨业务交付证据链冻结快照与差异复核包验收",
        "generated_at": now(),
        "passed": len(errors) == 0,
        "readonly": True,
        "error_count": len(errors),
        "missing_count": missing_count,
        "diff_count": diff_count,
        "source_count": len(sources),
        "baseline_created": diff.get("baseline_created", False),
        "errors": errors,
        "outputs": {"source_json": str(SOURCE_JSON), "snapshot_json": str(SNAPSHOT_JSON), "baseline_json": str(BASELINE_JSON), "diff_json": str(DIFF_JSON), "package_json": str(PACKAGE_JSON)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
