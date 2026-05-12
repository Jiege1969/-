# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁分项确认单草案与授权边界包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
PACKAGE_JSON = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "完全交付使用版红线解锁分项确认单草案与授权边界包_最新.json"
CARDS_JSON = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "红线解锁分项确认单草案_最新.json"
BOUNDARY_MD = EVOLUTION_ROOT / "03数据" / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "红线解锁分项授权边界说明_最新.md"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁分项确认单草案与授权边界包验收"
LATEST_LOG = LOG_DIR / "full-delivery-redline-unlock-confirmation-boundary-verify-最新.json"


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
    cards = read_json(CARDS_JSON) if CARDS_JSON.exists() else []
    boundary_text = BOUNDARY_MD.read_text(encoding="utf-8-sig") if BOUNDARY_MD.exists() else ""

    if package.get("状态") != "full_delivery_redline_unlock_confirmation_draft_ready":
        errors.append("总包状态不是确认单草案就绪")
    if len(cards) < 7:
        errors.append("分项确认单少于7项")
    if len(cards) != len(package.get("分项确认单草案", [])):
        errors.append("分项确认单独立文件与总包数量不一致")

    allowed_activation = [card for card in cards if card.get("允许生效") is not False]
    allowed_auto = [card for card in cards if card.get("允许自动执行") is not False]
    confirmed = [card for card in cards if card.get("总管确认状态") != "未确认"]
    missing_required = [
        card
        for card in cards
        if not {"解锁对象", "回滚路径", "成功样本", "失败样本", "拒收样本"}.issubset(set(card.get("生效前必填项", [])))
    ]

    if allowed_activation:
        errors.append("存在允许生效的确认单")
    if allowed_auto:
        errors.append("存在允许自动执行的确认单")
    if confirmed:
        errors.append("存在已确认确认单")
    if missing_required:
        errors.append("存在缺少生效前必填项的确认单")
    if package.get("安全边界", {}).get("红线解锁生效") is not False:
        errors.append("安全边界未保持红线解锁不生效")
    if "不构成生效授权" not in boundary_text:
        errors.append("授权边界说明缺少不构成生效授权声明")

    result = {
        "名称": "完全交付使用版红线解锁分项确认单草案与授权边界包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "确认单数量": len(cards),
            "允许生效数量": len(allowed_activation),
            "允许自动执行数量": len(allowed_auto),
            "已确认数量": len(confirmed),
        },
        "验证范围": {
            "总包": str(PACKAGE_JSON),
            "分项确认单草案": str(CARDS_JSON),
            "授权边界说明": str(BOUNDARY_MD),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
