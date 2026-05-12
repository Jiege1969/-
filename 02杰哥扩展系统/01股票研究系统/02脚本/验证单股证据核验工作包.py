# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验工作包.py
作用：验证190单股证据核验工作包可以生成，且目标必须跟随189入口中的第一只待核验股票。
触发方式：python 验证单股证据核验工作包.py
依赖：189证据链人工核验入口、190单股证据核验工作包、生成单股证据核验工作包.py。
所属系统：02杰哥扩展系统/01股票研究系统
输出：04日志/单股证据核验工作包/single-stock-evidence-package-verify-最新.json
安全边界：只读核验并刷新190准备包；不导入、不写正式档案、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：stock-evidence-single-package-verify
"""

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


def first_pending_target(entry: dict[str, Any]) -> dict[str, Any]:
    tasks = entry.get("逐股任务", []) if isinstance(entry.get("逐股任务"), list) else []
    for item in tasks:
        if int(item.get("合计待填") or 0) > 0:
            return item
    return {}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成单股证据核验工作包.py"
    entry_path = root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    latest_json = root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json"
    latest_md = root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.md"
    checks: list[dict[str, Any]] = [
        check("生成脚本存在", script.exists(), str(script)),
        check("189入口存在", entry_path.exists(), str(entry_path)),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json, {}) or {}
    entry = load_json(entry_path, {}) or {}
    target = report.get("目标股票", {})
    checks.append(check("目标股票明确", bool(target.get("代码") and target.get("名称")), target))
    expected_target = first_pending_target(entry)
    checks.append(check(
        "190目标跟随189第一只待核验股票",
        bool(expected_target) and target.get("代码") == expected_target.get("代码"),
        {
            "189第一只待核验": f"{expected_target.get('名称')}({expected_target.get('代码')})" if expected_target else "无",
            "190当前目标": f"{target.get('名称')}({target.get('代码')})",
        },
    ))
    checks.append(check("三条核验链齐全", all(report.get(name, {}).get("模板存在") for name in ["公司概况", "事件风险", "行业景气"]), report.get("待填汇总", {})))
    checks.append(check("待填任务非空", int(report.get("待填汇总", {}).get("合计待填") or 0) > 0, report.get("待填汇总", {})))
    target_total = int(target.get("合计待填") or 0)
    report_total = int(report.get("待填汇总", {}).get("合计待填") or 0)
    checks.append(check("待填合计与189入口一致", target_total > 0 and report_total == target_total, {"189合计待填": target_total, "190合计待填": report_total}))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含填完后运行和安全边界", "填完后运行" in md_text and "安全边界" in md_text, str(latest_md)))
    run_order = report.get("填完后运行脚本", [])
    checks.append(check(
        "190运行顺序包含198质量闸口和197预演",
        any("191填写质量闸口" in str(item) for item in run_order) and any("191完成后预演检查" in str(item) for item in run_order),
        run_order,
    ))
    checks.append(check(
        "190不再提示直接CSV同步旧链路",
        not any("同步单股证据核验CSV表单到台账.py" in str(item) for item in run_order),
        run_order,
    ))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验工作包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-package-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
