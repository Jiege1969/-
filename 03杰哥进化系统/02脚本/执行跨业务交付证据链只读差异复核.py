# -*- coding: utf-8 -*-
"""执行跨业务交付证据链只读差异复核。"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION / "03数据" / "94跨业务交付证据链冻结快照与差异复核包"
SOURCE_JSON = DATA_DIR / "证据源清单_最新.json"
SNAPSHOT_JSON = DATA_DIR / "冻结快照_最新.json"
SNAPSHOT_MD = DATA_DIR / "冻结快照_最新.md"
BASELINE_JSON = DATA_DIR / "冻结基线_最新.json"
DIFF_JSON = DATA_DIR / "差异复核报告_最新.json"
DIFF_MD = DATA_DIR / "差异复核报告_最新.md"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(source: dict[str, Any]) -> dict[str, Any]:
    path = Path(source["path"])
    exists = path.is_file()
    item: dict[str, Any] = {**source, "exists": exists, "size": None, "sha256": None, "mtime": None}
    if exists:
        stat = path.stat()
        item.update({"size": stat.st_size, "sha256": sha256(path), "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")})
    return item


def make_snapshot(sources: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [inspect(source) for source in sources]
    return {"name": "跨业务交付证据链冻结快照", "generated_at": now(), "readonly": True, "source_count": len(entries), "missing_count": sum(not e["exists"] for e in entries), "entries": entries}


def by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in report.get("entries", [])}


def make_diff(sources: list[dict[str, Any]], current: dict[str, Any], baseline: dict[str, Any], baseline_created: bool) -> dict[str, Any]:
    current_map = by_id(current)
    baseline_map = by_id(baseline)
    missing: list[dict[str, str]] = []
    diffs: list[dict[str, Any]] = []
    for source in sources:
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
    return {"name": "跨业务交付证据链只读差异复核报告", "generated_at": now(), "readonly": True, "baseline_created": baseline_created, "baseline_path": str(BASELINE_JSON), "snapshot_path": str(SNAPSHOT_JSON), "source_count": len(sources), "missing_count": len(missing), "diff_count": len(diffs), "missing": missing, "diffs": diffs}


def snapshot_md(report: dict[str, Any]) -> str:
    lines = ["# 跨业务交付证据链冻结快照", "", f"- generated_at: {report['generated_at']}", f"- readonly: {report['readonly']}", f"- missing_count: {report['missing_count']}", "", "| ID | exists | size | sha256 | mtime | 路径 |", "| --- | --- | ---: | --- | --- | --- |"]
    lines += [f"| {e['id']} | {e['exists']} | {e['size']} | {e['sha256']} | {e['mtime']} | {e['path']} |" for e in report["entries"]]
    return "\n".join(lines) + "\n"


def diff_md(report: dict[str, Any]) -> str:
    lines = ["# 跨业务交付证据链只读差异复核报告", "", f"- generated_at: {report['generated_at']}", f"- readonly: {report['readonly']}", f"- baseline_created: {report['baseline_created']}", f"- missing_count: {report['missing_count']}", f"- diff_count: {report['diff_count']}", ""]
    lines.append("未发现缺失或哈希差异。" if not report["missing"] and not report["diffs"] else "存在缺失或差异，详见 JSON。")
    return "\n".join(lines) + "\n"


def main() -> int:
    if not SOURCE_JSON.exists():
        print(json.dumps({"passed": False, "readonly": True, "error_count": 1, "missing_count": 0, "diff_count": 0, "error": f"证据源清单不存在: {SOURCE_JSON}"}, ensure_ascii=False))
        return 1
    manifest = read_json(SOURCE_JSON)
    sources = manifest.get("sources", [])
    current = make_snapshot(sources)
    baseline_created_now = not BASELINE_JSON.exists()
    if baseline_created_now:
        baseline = {**current, "name": "跨业务交付证据链冻结基线", "baseline_created": True, "baseline_created_at": current["generated_at"]}
        write_json(BASELINE_JSON, baseline)
    else:
        baseline = read_json(BASELINE_JSON)
    baseline_created = bool(baseline_created_now or baseline.get("baseline_created") or baseline.get("baseline_created_at"))
    report = make_diff(sources, current, baseline, baseline_created)
    write_json(SNAPSHOT_JSON, current)
    SNAPSHOT_MD.write_text(snapshot_md(current), encoding="utf-8")
    write_json(DIFF_JSON, report)
    DIFF_MD.write_text(diff_md(report), encoding="utf-8")
    passed = report["missing_count"] == 0 and report["diff_count"] == 0
    print(json.dumps({"passed": passed, "readonly": True, "baseline_created": baseline_created, "source_count": len(sources), "missing_count": report["missing_count"], "diff_count": report["diff_count"], "output": str(DIFF_JSON)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
