# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁误触发拦截与禁止执行预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_JSON = EVOLUTION_ROOT / "03数据" / "111完全交付使用版红线解锁误触发拦截与禁止执行预演包" / "完全交付使用版红线解锁误触发拦截与禁止执行预演包_最新.json"
BLOCK_JSON = EVOLUTION_ROOT / "03数据" / "111完全交付使用版红线解锁误触发拦截与禁止执行预演包" / "红线解锁误触发拦截结果_最新.json"
RULE_MD = EVOLUTION_ROOT / "03数据" / "111完全交付使用版红线解锁误触发拦截与禁止执行预演包" / "红线解锁禁止执行拦截规则_最新.md"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁误触发拦截与禁止执行预演包验收"
LATEST_LOG = LOG_DIR / "full-delivery-redline-unlock-misfire-blocker-verify-最新.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    if not PACKAGE_JSON.exists():
        errors.append(f"总包不存在：{PACKAGE_JSON}")
        package: dict[str, Any] = {}
    else:
        package = read_json(PACKAGE_JSON)
    blocks = read_json(BLOCK_JSON) if BLOCK_JSON.exists() else []
    rules = RULE_MD.read_text(encoding="utf-8-sig") if RULE_MD.exists() else ""

    if package.get("状态") != "full_delivery_redline_unlock_misfire_blocker_preview_ready":
        errors.append("总包状态不是误触发拦截预演就绪")
    if len(blocks) < 10:
        errors.append("误触发请求样本少于10项")

    allowed = [item for item in blocks if item.get("判定") != "blocked"]
    real_exec = [item for item in blocks if item.get("真实执行") is not False]
    activation = [item for item in blocks if item.get("允许生效") is not False]
    auto_exec = [item for item in blocks if item.get("允许自动执行") is not False]
    missing_reason = [item for item in blocks if not item.get("拦截原因")]

    if allowed:
        errors.append("存在未被拦截的误触发样本")
    if real_exec:
        errors.append("存在真实执行项")
    if activation:
        errors.append("存在允许生效项")
    if auto_exec:
        errors.append("存在允许自动执行项")
    if missing_reason:
        errors.append("存在缺少拦截原因的样本")
    if "打包解锁多条红线：blocked" not in rules:
        errors.append("拦截规则缺少打包解锁阻断说明")
    if package.get("安全边界", {}).get("红线解锁生效") is not False:
        errors.append("安全边界未保持红线解锁不生效")

    result = {
        "名称": "完全交付使用版红线解锁误触发拦截与禁止执行预演包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "请求样本数量": len(blocks),
            "拦截数量": len([item for item in blocks if item.get("判定") == "blocked"]),
            "放行数量": len(allowed),
            "真实执行数量": len(real_exec),
            "允许生效数量": len(activation),
            "允许自动执行数量": len(auto_exec),
        },
        "验证范围": {
            "总包": str(PACKAGE_JSON),
            "拦截结果": str(BLOCK_JSON),
            "拦截规则": str(RULE_MD),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
