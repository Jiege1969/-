# -*- coding: utf-8 -*-
"""
名称：验证个人智能母系统日常调度状态.py
作用：验证个人智能母系统日常调度规则、状态生成脚本和关键时间场景是否可用。
触发方式：python 验证个人智能母系统日常调度状态.py
依赖：Python标准库；生成个人智能母系统日常调度状态.py；个人智能母系统日常调度规则.json。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统日常调度/daily-scheduler-verify-*.json；daily-scheduler-verify-最新.json。
安全边界：只读验证并写总管日志；不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：personal-ai-daily-scheduler-verify；分时调度验收；只读验证。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def has_header(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig", errors="replace")[:1200]
    required = ["名称", "作用", "触发方式", "依赖", "所属系统", "安全边界", "标识"]
    return all(item in text for item in required)


def run_state(manager: Path, script: Path, sample_time: str) -> dict[str, Any]:
    result = subprocess.run(
        ["python", str(script), "--now", sample_time, "--ignore-resource-pressure"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest = manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json"
    parsed = load_json(latest) if latest.exists() else {}
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "parsed": parsed}


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"名称": name, "通过": bool(ok), "说明": detail})


def main() -> int:
    manager = manager_root()
    config = manager / "01配置" / "个人智能母系统日常调度规则.json"
    script = manager / "02脚本" / "生成个人智能母系统日常调度状态.py"
    checks: list[dict[str, Any]] = []

    add(checks, "日常调度规则存在", config.exists(), str(config))
    rules = load_json(config) if config.exists() else {}
    add(checks, "日常调度规则可解析", bool(rules.get("日常状态")), list(rules.keys()))
    add(checks, "日常调度规则包含硬件天花板原则", "硬件天花板是现实原则，不是约束借口。" in rules.get("核心原则", []), rules.get("核心原则", []))
    add(checks, "日常调度规则包含股票正式入口优先", any("股票系统白天正式可用优先" in item for item in rules.get("核心原则", [])), rules.get("核心原则", []))
    add(checks, "状态生成脚本存在", script.exists(), str(script))
    add(checks, "状态生成脚本含标准标头", script.exists() and has_header(script), str(script))

    samples = {
        "交易保护样本": ("2026-05-06 10:00:00", "开市轻量待命"),
        "收市分析样本": ("2026-05-06 16:00:00", "收市股票分析"),
        "夜间维护样本": ("2026-05-06 23:00:00", "夜间维护进化"),
        "节假日日常样本": ("2026-05-04 10:00:00", "日常轻量可用"),
    }
    sample_results = {}
    for name, (sample_time, expected_state) in samples.items():
        result = run_state(manager, script, sample_time)
        sample_results[name] = result
        actual = result.get("parsed", {}).get("当前状态")
        add(checks, f"{name}状态正确", result["returncode"] == 0 and actual == expected_state, {"期望": expected_state, "实际": actual, "样本时间": sample_time})

    latest_json = manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json"
    latest_md = manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.md"
    add(checks, "最新JSON状态文件存在", latest_json.exists(), str(latest_json))
    add(checks, "最新Markdown状态文件存在", latest_md.exists(), str(latest_md))
    if latest_json.exists():
        latest = load_json(latest_json)
        safety = latest.get("安全边界", {})
        add(checks, "安全边界全部为False", safety and not any(bool(value) for value in safety.values()), safety)
        add(checks, "输出包含调度优先级", bool(latest.get("调度优先级")), latest.get("调度优先级"))

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "个人智能母系统日常调度状态验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查项": checks,
        "样本结果": sample_results,
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    out_dir = manager / "04日志" / "个人智能母系统日常调度"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"daily-scheduler-verify-{stamp}.json"
    latest_output = out_dir / "daily-scheduler-verify-最新.json"
    write_json(output, report)
    write_json(latest_output, report)
    print(json.dumps({"通过": report["通过"], "失败": report["失败"], "输出": str(latest_output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
