# -*- coding: utf-8 -*-
"""
名称：验证股票证据链人工核验入口.py
作用：验证证据链人工核验入口可生成，且引导到190/191/198/197受控单股链路，不导入、不改评分、不触发外部动作。
触发方式：python 验证股票证据链人工核验入口.py
依赖：生成股票证据链人工核验入口.py、180证据核验总览面板、181导入执行闸口。
所属系统：02杰哥扩展系统/01股票研究系统
输出：04日志/证据链人工核验入口/stock-evidence-manual-verification-entry-verify-最新.json。
安全边界：只运行本地入口生成脚本并检查产物；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-evidence-manual-verification-entry-verify
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


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成股票证据链人工核验入口.py"
    latest_json = root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    latest_md = root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.md"
    checks: list[dict[str, Any]] = [check("脚本存在", script.exists(), str(script))]
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
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("Markdown报告存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json, {}) or {}
    checks.append(check("三条链路齐全", len(report.get("链路入口", [])) == 3, report.get("链路入口", [])))
    checks.append(check("逐股任务非空", len(report.get("逐股任务", [])) >= 10, len(report.get("逐股任务", []))))
    pending_tasks = [item for item in report.get("逐股任务", []) if int(item.get("合计待填") or 0) > 0]
    first_pending = pending_tasks[0] if pending_tasks else {}
    checks.append(check("已导入股票不再排为待填", all(int(item.get("合计待填") or 0) == 0 for item in report.get("逐股任务", [])[:4]), report.get("逐股任务", [])[:4]))
    checks.append(check("下一只待填为天齐锂业", first_pending.get("代码") == "sz002466", first_pending))
    checks.append(check("闸口仍禁止自动导入", report.get("导入闸口", {}).get("是否允许任何正式导入") is False, report.get("导入闸口", {})))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含人工操作顺序", "建议人工操作顺序" in text and "安全边界" in text, str(latest_md)))
    run_order = report.get("填完后运行脚本", [])
    checks.append(check(
        "189入口引导到190/191/198/197受控链路",
        all(any(required in str(item) for item in run_order) for required in ["单股证据核验工作包", "人工填写台账", "191填写质量闸口", "191完成后预演检查"]),
        run_order,
    ))
    checks.append(check(
        "189入口不再提示直接三链路预览旧路径",
        not any(old in str(item) for item in run_order for old in ["生成公司概况核验导入预览.py", "生成事件风险证据核验预览.py", "生成行业景气核验预览.py"]),
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
    log_dir = root / "04日志" / "证据链人工核验入口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"stock-evidence-manual-verification-entry-verify-{stamp}.json"
    latest_log = log_dir / "stock-evidence-manual-verification-entry-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
