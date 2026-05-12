# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验人工填写CSV表单.py
作用：验证191 CSV人工填写表单可生成、可解析，并能以dry-run方式同步预检。
触发方式：手动验收；注意用户已填写CSV后优先使用197完成后预演检查，避免重新生成CSV。
依赖：生成单股证据核验人工填写CSV表单.py、同步单股证据核验CSV表单到台账.py、191人工填写台账。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验人工填写CSV表单/single-stock-evidence-manual-csv-verify-最新.json。
安全边界：会重新生成CSV并运行同步dry-run，仅用于表单生成器验收；不写正式档案，不导入正式模板，不改评分推荐，不发送企业微信，不触发n8n，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-manual-csv-verify
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_script(root: Path, script_name: str, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(root / "02脚本" / script_name), *(args or [])],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    generator = root / "02脚本" / "生成单股证据核验人工填写CSV表单.py"
    syncer = root / "02脚本" / "同步单股证据核验CSV表单到台账.py"
    csv_path = out_dir / "单股证据核验人工填写CSV表单_最新.csv"
    note_path = out_dir / "单股证据核验人工填写CSV表单_最新.json"
    sync_report = out_dir / "单股证据核验CSV表单同步到台账_最新.json"
    checks: list[dict[str, Any]] = [
        check("生成脚本存在", generator.exists(), str(generator)),
        check("同步脚本存在", syncer.exists(), str(syncer)),
    ]
    run_gen = run_script(root, "生成单股证据核验人工填写CSV表单.py")
    checks.append(check("CSV生成脚本执行成功", run_gen.returncode == 0, run_gen.stdout.strip() or run_gen.stderr.strip()))
    checks.append(check("CSV表单存在", csv_path.exists() and csv_path.stat().st_size > 500, str(csv_path)))
    rows = read_csv(csv_path) if csv_path.exists() else []
    checks.append(check("CSV行数合理", len(rows) >= 30, len(rows)))
    required_columns = {"股票代码", "股票名称", "链路", "字段", "是否必填", "填写值", "填写说明"}
    checks.append(check("CSV列结构完整", bool(rows) and required_columns.issubset(rows[0].keys()), list(rows[0].keys()) if rows else []))
    chains = {row.get("链路") for row in rows}
    checks.append(check("三条证据链齐全", {"公司概况", "事件风险", "行业景气"}.issubset(chains), sorted(chains)))
    note = load_json(note_path, {}) or {}
    checks.append(check("CSV说明JSON存在", bool(note.get("CSV表单")), note))
    old_csv_protection = note.get("旧CSV保护", {}) if isinstance(note.get("旧CSV保护"), dict) else {}
    checks.append(check("旧CSV填写值保护已声明", old_csv_protection.get("重复刷新时保留已填写值") is True and "旧CSV读取行数" in old_csv_protection, old_csv_protection))
    open_bat = root / "05入口工具" / "单股证据核验人工填写CSV表单_打开.bat"
    checks.append(check("CSV打开入口存在", open_bat.exists(), str(open_bat)))
    run_sync = run_script(root, "同步单股证据核验CSV表单到台账.py", ["--dry-run"])
    checks.append(check("CSV同步dry-run成功", run_sync.returncode == 0, run_sync.stdout.strip() or run_sync.stderr.strip()))
    sync = load_json(sync_report, {}) or {}
    checks.append(check("同步预检报告存在且未写入", sync.get("只预检") is True, sync))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(csv_path),
    }
    log_dir = root / "04日志" / "单股证据核验人工填写CSV表单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-manual-csv-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-manual-csv-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
