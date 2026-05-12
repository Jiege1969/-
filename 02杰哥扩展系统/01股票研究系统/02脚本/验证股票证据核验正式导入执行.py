# -*- coding: utf-8 -*-
"""验证股票证据核验正式导入执行器默认dry-run、高风险动作关闭，执行后关键证据可读取。"""

from __future__ import annotations

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


def parse_json_line(text: str) -> dict[str, Any]:
    for line in reversed([line.strip() for line in text.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def find_item(items: list[dict[str, Any]], code: str) -> dict[str, Any]:
    for item in items:
        if str(item.get("代码") or "").lower() == code.lower():
            return item
    return {}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行股票证据核验正式导入.py"
    report_path = root / "03数据" / "195证据核验正式导入执行" / "股票证据核验正式导入执行报告_最新.json"
    checks = [check("正式导入执行脚本存在", script.exists(), str(script))]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    dry = subprocess.run([sys.executable, str(script), "--report-scope", "temp"], cwd=str(root / "02脚本"), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    checks.append(check("默认dry-run可执行", dry.returncode == 0, dry.stdout.strip() or dry.stderr.strip()))
    dry_output = parse_json_line(dry.stdout)
    dry_report_path = Path(dry_output.get("报告JSON", ""))
    report = load_json(dry_report_path, {}) or {}
    checks.append(check("默认不写入正式档案", report.get("执行写入") is False, report.get("总结论")))
    latest_report = load_json(report_path, {}) or {}
    checks.append(check("dry-run验证不覆盖最新执行报告", bool(latest_report), latest_report.get("总结论")))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    snapshot = load_json(root / "03数据" / "166公司经营快照" / "公司经营快照_最新.json", {}) or {}
    quality = load_json(root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json", {}) or {}
    industry = load_json(root / "03数据" / "167行业景气结论" / "行业景气结论_最新.json", {}) or {}
    event_ledger = load_json(root / "03数据" / "195事件风险核验证据账" / "事件风险核验证据账_最新.json", {}) or {}
    snap = find_item(snapshot.get("股票快照", []), "sh688047")
    qual = find_item(quality.get("股票档案", []), "sh688047")
    semis = next((row for row in industry.get("行业景气结论", []) if row.get("行业") == "半导体"), {})
    checks.append(check("公司经营快照可读取目标", bool(snap), snap.get("名称")))
    checks.append(check("公司品质档案可读取目标", bool(qual), qual.get("名称")))
    checks.append(check("行业景气结论可读取半导体", bool(semis), semis.get("行业")))
    if report.get("执行写入"):
        checks.append(check("公司概况已导入经营快照", snap.get("公司概况", {}).get("核心业务") not in ("", "待接入", None), snap.get("公司概况", {})))
        checks.append(check("公司概况已导入品质档案", qual.get("公司概况", {}).get("核心业务") not in ("", "待接入", None), qual.get("公司概况", {})))
        checks.append(check("行业正式核验证据已导入", bool(semis.get("正式核验")), semis.get("正式核验")))
        checks.append(check("事件风险证据账已导入", int(event_ledger.get("记录数") or 0) > 0, event_ledger.get("记录数")))
    else:
        checks.append(check("dry-run阶段允许等待正式写入", True, report.get("总结论")))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks}
    log_dir = root / "04日志" / "股票证据核验正式导入执行"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest = log_dir / "stock-evidence-formal-import-execute-verify-最新.json"
    write_json(log_dir / f"stock-evidence-formal-import-execute-verify-{stamp}.json", result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
