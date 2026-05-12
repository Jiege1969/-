# -*- coding: utf-8 -*-
"""
名称：验证并发写最新文件竞态经验卡片.py
作用：验证并发写最新文件竞态经验卡片已沉淀到03进化系统，并包含现象、原因、修复办法和复用规则。
触发方式：python 验证并发写最新文件竞态经验卡片.py
依赖：Python标准库；03数据/历史经验/并发写最新文件竞态经验卡片.md。
所属系统：03杰哥进化系统
安全边界：只读取经验卡片并写入04日志/历史经验验收；不删除文件；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建并发写最新文件竞态经验卡片验收脚本。
标识：evolution-concurrent-latest-write-experience-verify
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def evolution_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return evolution_root().parents[0]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = evolution_root()
    card = root / "03数据" / "历史经验" / "并发写最新文件竞态经验卡片.md"
    text = card.read_text(encoding="utf-8") if card.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "经验卡片存在", card.exists(), str(card))
    add_check(checks, "包含问题现象", "问题现象" in text and "JSONDecodeError" in text, "问题现象")
    add_check(checks, "包含原因判断", "原因判断" in text and "同时写" in text, "原因判断")
    add_check(checks, "包含修复办法", "修复办法" in text and "原子替换" in text, "修复办法")
    add_check(checks, "包含可复用规则", "可复用规则" in text and "不应和本地验收脚本并行运行" in text, "可复用规则")
    add_check(checks, "包含安全边界", "安全边界" in text and "不触发 n8n" in text, "安全边界")
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "并发写最新文件竞态经验已沉淀。" if failed == 0 else "并发写最新文件竞态经验卡片存在缺口。",
    }
    output_dir = root / "04日志" / "历史经验验收"
    output = output_dir / f"evolution-concurrent-latest-write-experience-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "evolution-concurrent-latest-write-experience-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
