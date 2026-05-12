# -*- coding: utf-8 -*-
"""
名称：验证个人智能母系统任务队列调度.py
作用：验证无人值守任务队列种子能通过个人智能母系统任务准入闸口生成队列调度面板，且不触发执行器或n8n。
触发方式：python 验证个人智能母系统任务队列调度.py
依赖：Python标准库；生成个人智能母系统任务队列调度面板.py。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统任务队列/task-queue-scheduler-verify-*.json。
安全边界：只读验证并写总管日志；不执行任务、不触发执行器、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：personal-ai-task-queue-scheduler-verify；队列调度验收；只读验证。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def has_header(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig", errors="replace")[:1200]
    return all(key in text for key in ["名称", "作用", "触发方式", "依赖", "所属系统", "输出", "安全边界", "标识"])


def run_panel(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"名称": name, "通过": bool(ok), "说明": detail})


def main() -> int:
    manager = manager_root()
    config = manager / "01配置" / "个人智能母系统任务队列调度规则.json"
    script = manager / "02脚本" / "生成个人智能母系统任务队列调度面板.py"
    latest = manager / "03数据" / "运行状态" / "个人智能母系统任务队列调度_最新.json"
    checks: list[dict[str, Any]] = []
    add(checks, "任务队列调度规则存在", config.exists(), str(config))
    rules = load_json(config, {})
    add(checks, "任务队列调度规则可解析", bool(rules.get("队列动作")), list(rules.keys()))
    add(checks, "任务队列调度脚本存在", script.exists(), str(script))
    add(checks, "任务队列调度脚本含标准标头", script.exists() and has_header(script), str(script))

    run = run_panel(script, "--now", "2026-05-06 10:00:00", "--ignore-resource-pressure")
    report = load_json(latest, {})
    summary = report.get("汇总", {})
    queue = report.get("任务队列", [])
    add(checks, "任务队列调度面板生成成功", run.returncode == 0 and latest.exists(), run.stdout.strip() or run.stderr.strip())
    add(checks, "队列包含样例任务", summary.get("任务数量", 0) >= 4, summary)
    add(checks, "最新Markdown队列面板存在", (manager / "03数据" / "运行状态" / "个人智能母系统任务队列调度_最新.md").exists(), str(manager / "03数据" / "运行状态" / "个人智能母系统任务队列调度_最新.md"))
    add(checks, "队列不触发执行器", summary.get("触发执行器数量") == 0, summary)
    add(checks, "队列不触发n8n", summary.get("触发n8n数量") == 0, summary)
    add(checks, "至少一个任务允许执行", summary.get("允许执行", 0) >= 1, summary)
    add(checks, "至少一个任务禁止执行", summary.get("禁止执行", 0) >= 1, summary)
    wecom_disabled = [item for item in queue if item.get("任务编号") == "UQ003"]
    add(checks, "企业微信真实发送禁用态巡检不被误判为真实发送", bool(wecom_disabled) and wecom_disabled[0].get("准入结论") != "禁止执行", wecom_disabled)
    add(checks, "所有任务有准入结论", all(item.get("准入结论") for item in queue), queue)
    safety = report.get("安全边界", {})
    add(checks, "安全边界全部为False", safety and not any(bool(value) for value in safety.values()), safety)

    failed = [item for item in checks if not item["通过"]]
    verify = {
        "名称": "个人智能母系统任务队列调度验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查项": checks,
        "安全边界": {
            "是否执行任务": False,
            "是否触发执行器": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    out_dir = manager / "04日志" / "个人智能母系统任务队列"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"task-queue-scheduler-verify-{stamp}.json"
    latest_output = out_dir / "task-queue-scheduler-verify-最新.json"
    write_json(output, verify)
    write_json(latest_output, verify)
    print(json.dumps({"通过": verify["通过"], "失败": verify["失败"], "输出": str(latest_output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
