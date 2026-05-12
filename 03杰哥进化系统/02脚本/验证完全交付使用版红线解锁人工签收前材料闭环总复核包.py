# -*- coding: utf-8 -*-
"""验证完全交付使用版红线解锁人工签收前材料闭环总复核包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "110完全交付使用版红线解锁人工签收前材料闭环总复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁人工签收前材料闭环总复核包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版红线解锁人工签收前材料闭环总复核包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版红线解锁人工签收前材料闭环总复核包_最新.md"
CHECKLIST_JSON = DATA_DIR / "人工签收前材料闭环复核清单_最新.json"
CHECKLIST_MD = DATA_DIR / "人工签收前材料闭环复核清单_最新.md"
LATEST_LOG = LOG_DIR / "full-delivery-redline-unlock-presign-material-closure-review-verify-最新.json"

HARD_FALSE_KEYS = [
    "真实发送企业微信",
    "真实触发n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "真实渲染视频",
    "自动发布视频",
    "写正式规则",
    "自动转正式规则",
    "红线解锁生效",
    "真实执行回滚",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载19310",
    "重载19302",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    if not PACKAGE_JSON.exists():
        errors.append(f"总包不存在：{PACKAGE_JSON}")
        package: dict[str, Any] = {}
    else:
        package = read_json(PACKAGE_JSON)

    checklist = read_json(CHECKLIST_JSON) if CHECKLIST_JSON.exists() else []

    if package.get("状态") != "full_delivery_redline_unlock_presign_material_closure_review_ready":
        errors.append("总包状态不是人工签收前材料闭环总复核就绪")
    if not PACKAGE_MD.exists():
        errors.append(f"总包Markdown不存在：{PACKAGE_MD}")
    if not CHECKLIST_JSON.exists():
        errors.append(f"复核清单JSON不存在：{CHECKLIST_JSON}")
    if not CHECKLIST_MD.exists():
        errors.append(f"复核清单Markdown不存在：{CHECKLIST_MD}")

    sources = package.get("来源摘要", [])
    if len(sources) < 7:
        errors.append("来源摘要少于7项")
    missing_sources = [item for item in sources if item.get("存在") is not True]
    failed_sources = [item for item in sources if item.get("状态通过") is not True]
    failed_checks = [item for item in checklist if item.get("通过") is not True]

    if missing_sources:
        errors.append("存在缺失的上游来源")
    if failed_sources:
        errors.append("存在状态未通过的上游来源")
    if len(checklist) < 7:
        errors.append("复核清单少于7项")
    if failed_checks:
        errors.append("存在未通过的闭环复核项")

    conclusion = package.get("结论", {})
    if conclusion.get("pass") is not True:
        errors.append("结论pass不是True")
    if conclusion.get("总管已签收") is not False:
        errors.append("总管签收状态未保持False")
    if conclusion.get("允许生效") is not False:
        errors.append("允许生效未保持False")
    if conclusion.get("允许自动执行") is not False:
        errors.append("允许自动执行未保持False")
    if conclusion.get("红线解锁生效") is not False:
        errors.append("红线解锁生效未保持False")

    safety = package.get("安全边界", {})
    bad_safety = [key for key in HARD_FALSE_KEYS if safety.get(key) not in (False, None)]
    if bad_safety:
        errors.append("安全边界存在非False红线项：" + "，".join(bad_safety))

    result = {
        "名称": "完全交付使用版红线解锁人工签收前材料闭环总复核包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "来源数量": len(sources),
            "缺失来源数量": len(missing_sources),
            "状态未通过来源数量": len(failed_sources),
            "复核项数量": len(checklist),
            "未通过复核项数量": len(failed_checks),
            "安全边界异常数量": len(bad_safety),
        },
        "验证范围": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "复核清单JSON": str(CHECKLIST_JSON),
            "复核清单Markdown": str(CHECKLIST_MD),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
