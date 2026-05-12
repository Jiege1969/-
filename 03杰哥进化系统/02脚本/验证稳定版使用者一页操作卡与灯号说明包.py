# -*- coding: utf-8 -*-
"""验证稳定版使用者一页操作卡与灯号说明包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版使用者一页操作卡与灯号说明包验收"

ASSET_JSON = DATA_DIR / "稳定版使用者一页操作卡与灯号说明包_最新.json"
OP_CARD_MD = DATA_DIR / "稳定版使用者一页操作卡_最新.md"
LIGHTS_MD = DATA_DIR / "稳定版运行灯号说明_最新.md"
LATEST_LOG = LOG_DIR / "stable-user-one-page-operation-card-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    op_text = OP_CARD_MD.read_text(encoding="utf-8-sig") if OP_CARD_MD.exists() else ""
    lights_text = LIGHTS_MD.read_text(encoding="utf-8-sig") if LIGHTS_MD.exists() else ""

    if asset.get("状态") != "stable_user_one_page_operation_card_ready":
        errors.append("总包状态必须为 stable_user_one_page_operation_card_ready")
    if asset.get("运行灯号") not in {"green", "yellow", "red"}:
        errors.append("运行灯号不合法")
    for path_text in asset.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")
    for path_text in [asset.get("每日入口"), asset.get("每日入口验收")]:
        if not path_text or not Path(path_text).exists():
            errors.append(f"每日入口不存在：{path_text}")
    if "每天先做" not in op_text or "跑完再验收" not in op_text:
        errors.append("操作卡必须包含每日执行和验收说明")
    if "green" not in lights_text or "yellow" not in lights_text or "red" not in lights_text:
        errors.append("灯号说明必须包含 green/yellow/red")
    if not all(value is False for value in asset.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")

    report = {
        "名称": "稳定版使用者一页操作卡与灯号说明包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "运行灯号": asset.get("运行灯号"),
            "三日达标": asset.get("三日达标"),
            "仍缺自然日样本": asset.get("仍缺自然日样本"),
        },
        "验证范围": {
            "总包": str(ASSET_JSON),
            "操作卡": str(OP_CARD_MD),
            "灯号说明": str(LIGHTS_MD),
            "日志": str(LATEST_LOG),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
