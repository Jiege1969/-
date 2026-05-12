# -*- coding: utf-8 -*-
"""
名称：验证智能化施工落地检查清单.py
作用：验证智能化施工落地检查规则和清单可生成、关键原则覆盖完整。
触发方式：手动验收；规则或清单生成脚本更新后执行。
依赖：生成智能化施工落地检查清单.py、01配置/智能化施工落地检查规则.json。
所属系统：00杰哥系统总管。
输出：04日志/智能化施工落地检查/智能化施工落地检查验证_最新.json。
安全边界：只读规则和生成的清单；只写04日志/智能化施工落地检查；不触发n8n、不发送企业微信、不启动模型。
标识：智能化施工落地检查；清单验收；只读验证。
"""

from __future__ import annotations

import json
import os
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
    manager = manager_root()
    rule_path = manager / "01配置" / "智能化施工落地检查规则.json"
    generator = manager / "02脚本" / "生成智能化施工落地检查清单.py"
    latest_json = manager / "03数据" / "智能化施工落地检查" / "智能化施工落地检查清单_最新.json"
    latest_md = manager / "03数据" / "智能化施工落地检查" / "智能化施工落地检查清单_最新.md"
    checks: list[dict[str, Any]] = [
        check("规则文件存在", rule_path.exists(), str(rule_path)),
        check("生成脚本存在", generator.exists(), str(generator)),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(generator)],
        cwd=str(manager / "02脚本"),
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
    rule = load_json(rule_path, {}) or {}
    report = load_json(latest_json, {}) or {}
    checks.append(check("检查项不少于8项", len(rule.get("落地检查项", [])) >= 8, len(rule.get("落地检查项", []))))
    text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    for keyword in ["硬件", "分时调度", "规则优先", "检索增强", "人工闸口", "资源闸口", "进化", "企业微信"]:
        checks.append(check(f"覆盖关键词：{keyword}", keyword in text, keyword))
    checks.append(check("安全边界全部为false", bool(report.get("安全边界")) and all(value is False for value in report["安全边界"].values()), report.get("安全边界", {})))
    open_bat = manager / "06工具" / "智能化施工落地检查清单_打开.bat"
    checks.append(check("入口工具存在", open_bat.exists(), str(open_bat)))
    missing_refs = []
    for item in report.get("落地检查项", []):
        missing_refs.extend(item.get("参考文件缺失", []))
    checks.append(check("参考文件全部存在", not missing_refs, missing_refs))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = manager / "04日志" / "智能化施工落地检查"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"intelligent-construction-check-verify-{stamp}.json"
    latest = log_dir / "intelligent-construction-check-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
