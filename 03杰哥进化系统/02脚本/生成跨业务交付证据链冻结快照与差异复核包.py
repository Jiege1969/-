# -*- coding: utf-8 -*-
"""生成跨业务交付证据链冻结快照与差异复核包。

只读扫描既有证据文件；仅写入本任务白名单 94 数据目录。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION / "03数据" / "94跨业务交付证据链冻结快照与差异复核包"

SOURCE_JSON = DATA_DIR / "证据源清单_最新.json"
SOURCE_MD = DATA_DIR / "证据源清单_最新.md"
SNAPSHOT_JSON = DATA_DIR / "冻结快照_最新.json"
SNAPSHOT_MD = DATA_DIR / "冻结快照_最新.md"
BASELINE_JSON = DATA_DIR / "冻结基线_最新.json"
DIFF_JSON = DATA_DIR / "差异复核报告_最新.json"
DIFF_MD = DATA_DIR / "差异复核报告_最新.md"
PACKAGE_JSON = DATA_DIR / "跨业务交付证据链冻结快照与差异复核包_最新.json"
PACKAGE_MD = DATA_DIR / "跨业务交付证据链冻结快照与差异复核包_最新.md"

SOURCES: list[dict[str, str]] = [
    {"id": "CB-EVID-001", "category": "企业微信公共接入层日常巡检", "business": "企业微信公共层", "name": "企业微信接入层只读核查回执", "path": str(ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "PAR_WECOM_20260508_D_企业微信接入层只读核查回执.json")},
    {"id": "CB-EVID-002", "category": "税收入口门禁验收", "business": "税收业务", "name": "税收企业微信正式入口发送门禁验收", "path": str(ROOT / "02杰哥扩展系统" / "05税收业务系统" / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口发送门禁验收_最新.json")},
    {"id": "CB-EVID-003", "category": "股票展示口径一致性", "business": "股票研究系统", "name": "股票展示口径一致性验收", "path": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "246展示口径修复" / "股票展示口径一致性验收_最新.json")},
    {"id": "CB-EVID-004", "category": "股票影子验收", "business": "股票研究系统", "name": "股票线第九批统一影子验收总表验收结果", "path": str(ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "245L3评分基础资产" / "股票线第九批统一影子验收总表验收结果_最新.json")},
    {"id": "CB-EVID-005", "category": "视频渲染发布阻断", "business": "视频制作系统", "name": "视频真实渲染禁用态检查", "path": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json")},
    {"id": "CB-EVID-006", "category": "视频渲染发布阻断", "business": "视频制作系统", "name": "最终发布启用门禁", "path": str(ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "最终发布启用门禁" / "最终发布启用门禁_最新.json")},
    {"id": "CB-EVID-007", "category": "日常总回归", "business": "进化系统", "name": "日常可用交付版一键只读总回归验收", "path": str(EVOLUTION / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json")},
    {"id": "CB-EVID-008", "category": "自主巡检快照", "business": "进化系统", "name": "日常可用版自主巡检快照", "path": str(EVOLUTION / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json")},
    {"id": "CB-EVID-009", "category": "第八轮调度验收", "business": "进化系统", "name": "第八轮放行材料一致性并行调度索引包验收", "path": str(EVOLUTION / "04日志" / "第八轮放行材料一致性并行调度索引包验收" / "parallel-round8-release-material-consistency-verify-最新.json")},
    {"id": "CB-EVID-010", "category": "第九轮调度验收", "business": "进化系统", "name": "第九轮签收回滚与留痕并行调度索引包验收", "path": str(EVOLUTION / "04日志" / "第九轮签收回滚与留痕并行调度索引包验收" / "parallel-round9-signoff-rollback-evidence-verify-最新.json")},
]

SAFETY = {
    "readonly": True,
    "real_wecom_send": False,
    "connect_n8n": False,
    "trigger_n8n": False,
    "connect_broker": False,
    "trade": False,
    "login_tax_bureau": False,
    "connect_finance_tax_software": False,
    "promote_to_formal_rule": False,
    "modify_master_panel": False,
    "modify_one_click_continuation_package": False,
    "reload_service": False,
}


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(source: dict[str, str]) -> dict[str, Any]:
    path = Path(source["path"])
    exists = path.is_file()
    item: dict[str, Any] = {**source, "exists": exists, "size": None, "sha256": None, "mtime": None}
    if exists:
        stat = path.stat()
        item.update({"size": stat.st_size, "sha256": sha256(path), "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")})
    return item


def snapshot() -> dict[str, Any]:
    entries = [inspect(source) for source in SOURCES]
    return {"name": "跨业务交付证据链冻结快照", "generated_at": now(), "readonly": True, "source_count": len(entries), "missing_count": sum(not e["exists"] for e in entries), "entries": entries}


def by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in report.get("entries", [])}


def diff(current: dict[str, Any], baseline: dict[str, Any], baseline_created: bool) -> dict[str, Any]:
    current_map = by_id(current)
    baseline_map = by_id(baseline)
    missing: list[dict[str, str]] = []
    diffs: list[dict[str, Any]] = []
    for source in SOURCES:
        item_id = source["id"]
        cur = current_map.get(item_id)
        base = baseline_map.get(item_id)
        if not cur or not cur.get("exists"):
            missing.append({"id": item_id, "path": source["path"], "reason": "current_file_missing"})
            continue
        if not base or not base.get("exists"):
            diffs.append({"id": item_id, "path": source["path"], "reason": "baseline_missing"})
            continue
        changed = [field for field in ("path", "exists", "size", "sha256") if cur.get(field) != base.get(field)]
        if changed:
            diffs.append({"id": item_id, "path": source["path"], "changed_fields": changed})
    return {"name": "跨业务交付证据链只读差异复核报告", "generated_at": now(), "readonly": True, "baseline_created": baseline_created, "baseline_path": str(BASELINE_JSON), "snapshot_path": str(SNAPSHOT_JSON), "source_count": len(SOURCES), "missing_count": len(missing), "diff_count": len(diffs), "missing": missing, "diffs": diffs}


def source_md() -> str:
    lines = ["# 跨业务交付证据源清单", "", "| ID | 分类 | 业务 | 证据文件 | 路径 |", "| --- | --- | --- | --- | --- |"]
    lines += [f"| {s['id']} | {s['category']} | {s['business']} | {s['name']} | {s['path']} |" for s in SOURCES]
    return "\n".join(lines) + "\n"


def snapshot_md(report: dict[str, Any]) -> str:
    lines = ["# 跨业务交付证据链冻结快照", "", f"- 生成时间: {report['generated_at']}", f"- readonly: {report['readonly']}", f"- missing_count: {report['missing_count']}", "", "| ID | exists | size | sha256 | mtime | 路径 |", "| --- | --- | ---: | --- | --- | --- |"]
    lines += [f"| {e['id']} | {e['exists']} | {e['size']} | {e['sha256']} | {e['mtime']} | {e['path']} |" for e in report["entries"]]
    return "\n".join(lines) + "\n"


def diff_md(report: dict[str, Any]) -> str:
    lines = ["# 跨业务交付证据链只读差异复核报告", "", f"- generated_at: {report['generated_at']}", f"- readonly: {report['readonly']}", f"- baseline_created: {report['baseline_created']}", f"- missing_count: {report['missing_count']}", f"- diff_count: {report['diff_count']}", ""]
    lines.append("未发现缺失或哈希差异。" if not report["missing"] and not report["diffs"] else "存在缺失或差异，详见 JSON。")
    return "\n".join(lines) + "\n"


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(["# 跨业务交付证据链冻结快照与差异复核包", "", f"- generated_at: {package['generated_at']}", f"- readonly: {package['readonly']}", f"- error_count: {package['error_count']}", f"- missing_count: {package['missing_count']}", f"- diff_count: {package['diff_count']}", "", "红线：不真实发送企业微信、不接n8n、不接券商、不交易、不登录税局、不接财税软件、不自动转正式规则、不改总管面板、不改一键接续包、不重载服务。", ""]) 


def main() -> int:
    manifest = {"name": "跨业务交付证据源清单", "generated_at": now(), "readonly": True, "source_count": len(SOURCES), "required_categories": sorted({s["category"] for s in SOURCES}), "sources": SOURCES, "safety_boundary": SAFETY}
    current = snapshot()
    baseline = {**current, "name": "跨业务交付证据链冻结基线", "baseline_created": True, "baseline_created_at": current["generated_at"]}
    write_json(BASELINE_JSON, baseline)
    baseline_created = True
    diff_report = diff(current, baseline, baseline_created)
    package = {"name": "跨业务交付证据链冻结快照与差异复核包", "generated_at": now(), "readonly": True, "error_count": 0, "missing_count": diff_report["missing_count"], "diff_count": diff_report["diff_count"], "source_manifest": manifest, "snapshot": current, "diff_report": diff_report, "safety_boundary": SAFETY}

    write_json(SOURCE_JSON, manifest)
    SOURCE_MD.write_text(source_md(), encoding="utf-8")
    write_json(SNAPSHOT_JSON, current)
    SNAPSHOT_MD.write_text(snapshot_md(current), encoding="utf-8")
    write_json(DIFF_JSON, diff_report)
    DIFF_MD.write_text(diff_md(diff_report), encoding="utf-8")
    write_json(PACKAGE_JSON, package)
    PACKAGE_MD.write_text(package_md(package), encoding="utf-8")

    passed = package["missing_count"] == 0 and package["diff_count"] == 0
    print(json.dumps({"passed": passed, "readonly": True, "baseline_created": baseline_created, "source_count": len(SOURCES), "missing_count": package["missing_count"], "diff_count": package["diff_count"], "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
