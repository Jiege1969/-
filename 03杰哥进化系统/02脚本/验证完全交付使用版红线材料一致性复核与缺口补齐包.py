# -*- coding: utf-8 -*-
"""只读验收完全交付使用版红线材料一致性复核与缺口补齐包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线材料一致性复核与缺口补齐包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线材料一致性复核与缺口补齐包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.md"
CHECK_MD = DATA_DIR / "红线材料一致性复核表_最新.md"
GAP_MD = DATA_DIR / "材料缺口补齐队列_最新.md"
GUARD_MD = DATA_DIR / "未确认前守护口径_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版红线材料一致性复核与缺口补齐包_最新.json"
VERIFY_LOG = LOG_DIR / "full-delivery-redline-material-consistency-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, CHECK_MD, GAP_MD, GUARD_MD, GEN_LOG]
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
        package.get("状态") == "full_delivery_redline_material_consistency_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    checks_table = package.get("红线材料一致性复核表", [])
    checks_text = json.dumps(checks_table, ensure_ascii=False)
    consistency_ok = len(checks_table) >= 6 and "未写正式规则" in checks_text and "未导入未触发" in checks_text and "未渲染未发布" in checks_text and "未自行重载" in checks_text
    add_check(checks, "红线材料一致性有效", consistency_ok, f"复核对象={len(checks_table)}")

    gaps = package.get("材料缺口补齐队列", [])
    gaps_text = json.dumps(gaps, ensure_ascii=False)
    gaps_ok = len(gaps) >= 5 and "不发送" in gaps_text and "不重载" in gaps_text and "不导入" in gaps_text and "不渲染" in gaps_text and "不生效" in gaps_text
    add_check(checks, "缺口补齐队列仍低风险", gaps_ok, f"缺口项={len(gaps)}")

    guards = package.get("未确认前守护口径", [])
    guards_text = json.dumps(guards, ensure_ascii=False)
    guards_ok = len(guards) >= 5 and "申请材料不等于授权" in guards_text and "已封存双版本不被改写" in guards_text
    add_check(checks, "未确认前守护口径有效", guards_ok, f"守护项={len(guards)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "完全交付使用版红线材料一致性复核与缺口补齐包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "红线材料一致性复核表": str(CHECK_MD),
            "材料缺口补齐队列": str(GAP_MD),
            "未确认前守护口径": str(GUARD_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
