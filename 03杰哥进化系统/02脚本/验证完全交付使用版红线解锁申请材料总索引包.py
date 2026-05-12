# -*- coding: utf-8 -*-
"""只读验收完全交付使用版红线解锁申请材料总索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁申请材料总索引包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版红线解锁申请材料总索引包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版红线解锁申请材料总索引包_最新.md"
INDEX_MD = DATA_DIR / "红线解锁申请材料总索引_最新.md"
CONFIRM_MD = DATA_DIR / "总管确认条件清单_最新.md"
REJECT_MD = DATA_DIR / "未确认前禁止动作清单_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版红线解锁申请材料总索引包_最新.json"
VERIFY_LOG = LOG_DIR / "full-delivery-redline-unlock-material-index-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, INDEX_MD, CONFIRM_MD, REJECT_MD, GEN_LOG]
REQUIRED_REDLINES = ["正式规则", "n8n", "视频", "企业微信", "19310", "券商", "税局"]
FORBIDDEN_MARKERS = [
    "允许真实发送",
    "允许真实触发",
    "允许接券商",
    "允许交易",
    "允许登录电子税务局",
    "允许接财税软件",
    "允许真实渲染",
    "允许自动发布",
    "允许写正式规则",
    "允许自动转正式规则",
    "允许重载19310",
    "允许重载19302",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"名称": name, "通过": passed, "详情": detail})


def combined_text(paths: list[Path]) -> str:
    parts: list[str] = []
    for path in paths:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8-sig", errors="ignore"))
    return "\n".join(parts)


def main() -> int:
    checks: list[dict[str, Any]] = []
    package = read_json(PACKAGE_JSON)

    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    add_check(checks, "必需文件存在", not missing, "缺失: " + "；".join(missing) if missing else "全部存在")

    add_check(
        checks,
        "总包状态就绪",
        package.get("状态") == "full_delivery_redline_unlock_material_index_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 9 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    index_items = package.get("红线解锁申请材料总索引", [])
    index_text = json.dumps(index_items, ensure_ascii=False)
    index_ok = len(index_items) >= 7 and all(marker in index_text for marker in REQUIRED_REDLINES) and "仅" in index_text
    add_check(checks, "红线材料索引覆盖", index_ok, f"红线项={len(index_items)}")

    confirm_items = package.get("总管确认条件清单", [])
    confirm_text = json.dumps(confirm_items, ensure_ascii=False)
    confirm_ok = len(confirm_items) >= 6 and "回滚" in confirm_text and "单次授权边界" in confirm_text
    add_check(checks, "总管确认条件有效", confirm_ok, f"确认项={len(confirm_items)}")

    reject_items = package.get("未确认前禁止动作清单", [])
    reject_text = json.dumps(reject_items, ensure_ascii=False)
    reject_ok = len(reject_items) >= 7 and "真实发送企业微信" in reject_text and "真实触发n8n" in reject_text and "自行重载19310/19302" in reject_text
    add_check(checks, "未确认前禁止动作明确", reject_ok, f"禁止项={len(reject_items)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "完全交付使用版红线解锁申请材料总索引包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "红线解锁申请材料总索引": str(INDEX_MD),
            "总管确认条件清单": str(CONFIRM_MD),
            "未确认前禁止动作清单": str(REJECT_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
