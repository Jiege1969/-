# -*- coding: utf-8 -*-
"""
名称：验证施工接续卡片.py
作用：验证施工接续卡片生成链路可运行且不越权。
触发方式：python 验证施工接续卡片.py
依赖：Python标准库；生成施工接续卡片.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证本地接续卡片；只写04日志/施工接续的最新验收结果；不写时间戳流水；不删除文件；不写旧系统；不重启服务；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
标识：construction-handoff-card-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = system_root()
    manager = root / "00杰哥系统总管"
    generator = manager / "02脚本" / "生成施工接续卡片.py"
    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    json_latest = manager / "03数据" / "施工接续" / "施工接续卡片_最新.json"
    md_latest = manager / "03数据" / "施工接续" / "施工接续卡片_最新.md"
    card = load_json(json_latest) if json_latest.exists() else {}
    text = md_latest.read_text(encoding="utf-8") if md_latest.exists() else ""
    safety = card.get("安全边界", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "JSON接续卡片存在", json_latest.exists() and card.get("当前所在步骤"), str(json_latest))
    add_check(checks, "Markdown接续卡片存在", md_latest.exists() and "施工接续卡片" in text, str(md_latest))
    add_check(checks, "接续口径已更新", "摸清家底找差距" in json.dumps(card, ensure_ascii=False), card.get("当前所在步骤"))
    add_check(checks, "不再保留旧股票灰度阶段口径", "继续完善股票研究系统企业微信真实灰度接入前的安全门禁" not in text, "")
    add_check(checks, "安全边界关闭", bool(safety) and all(item is False for item in safety.values()), safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "施工接续卡片可用于下一轮继续施工。" if failed == 0 else "施工接续卡片存在失败项。",
    }
    latest = manager / "04日志" / "施工接续" / "construction-handoff-card-verify-最新.json"
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
