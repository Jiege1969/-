# -*- coding: utf-8 -*-
"""
名称：验证300只候选事件核验结果回填包.py
作用：验证事件核验结果回填包是否可生成、派生账本是否存在、安全边界是否保持。
触发方式：python 验证300只候选事件核验结果回填包.py
依赖：Python标准库；生成300只候选事件核验结果回填包.py；300只候选事件核验结果回填规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不覆盖原始99人工闸口；不覆盖原始97复盘账本；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选事件核验结果回填包验收脚本。
标识：stock-trial-pool-300-event-verification-backfill-verify
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成300只候选事件核验结果回填包.py"
    rule_path = root / "01配置" / "300只候选事件核验结果回填规则.json"
    checks: list[dict[str, Any]] = [
        check("脚本存在", script.exists(), str(script)),
        check("规则存在", rule_path.exists(), str(rule_path)),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))

    rule = load_json(rule_path)
    latest = root / rule["输出"]["数据目录"] / rule["输出"]["最新文件"]
    markdown = root / rule["输出"]["数据目录"] / rule["输出"]["报告文件"]
    gate_derivative = root / rule["输出"]["数据目录"] / rule["输出"]["人工闸口派生文件"]
    review_derivative = root / rule["输出"]["数据目录"] / rule["输出"]["复盘闭环派生文件"]
    checks.append(check("最新JSON存在", latest.exists(), str(latest)))
    checks.append(check("Markdown报告存在", markdown.exists(), str(markdown)))
    checks.append(check("人工闸口派生账本存在", gate_derivative.exists(), str(gate_derivative)))
    checks.append(check("复盘闭环派生账本存在", review_derivative.exists(), str(review_derivative)))

    report = load_json(latest) if latest.exists() else {}
    results = report.get("逐只回填结果", [])
    checks.append(check("逐只回填结果存在", len(results) == report.get("候选数量") and len(results) > 0, {"results": len(results), "count": report.get("候选数量")}))
    checks.append(check("核验任务数量覆盖", int(report.get("核验任务数量", 0)) >= int(report.get("候选数量", 0)) * 3, {"tasks": report.get("核验任务数量"), "candidates": report.get("候选数量")}))
    all_pending_blocked = all(item.get("是否可进入精选推送草案") is False for item in results)
    checks.append(check("未人工核验时不进入精选草案", all_pending_blocked, [item.get("系统回填结论") for item in results]))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))
    gate_data = load_json(gate_derivative) if gate_derivative.exists() else {}
    review_data = load_json(review_derivative) if review_derivative.exists() else {}
    checks.append(check("原始人工闸口未覆盖标记", gate_data.get("是否覆盖原始人工闸口") is False, gate_data.get("是否覆盖原始人工闸口")))
    checks.append(check("原始复盘账本未覆盖标记", review_data.get("是否覆盖原始复盘账本") is False, review_data.get("是否覆盖原始复盘账本")))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含回填结论", "逐只回填结果" in text and "安全边界" in text, "回填报告"))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest)
    }
    output_dir = root / "04日志" / "事件核验结果回填"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-event-verification-backfill-verify-{stamp}.json"
    latest_log = output_dir / "trial-pool-300-event-verification-backfill-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
