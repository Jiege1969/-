# -*- coding: utf-8 -*-
"""只读验收完全交付使用版低风险续建第二批复核包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "104完全交付使用版低风险续建第二批复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建第二批复核包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建第二批复核包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建第二批复核包_最新.md"
RECHECK_MD = DATA_DIR / "第二批低风险复核台账_最新.md"
STATIC_MD = DATA_DIR / "静态检查与禁用态确认_最新.md"
NEXT_MD = DATA_DIR / "第三批低风险续建建议_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建第二批复核包_最新.json"
VERIFY_LOG = LOG_DIR / "full-delivery-low-risk-batch2-recheck-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, RECHECK_MD, STATIC_MD, NEXT_MD, GEN_LOG]
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
        package.get("状态") == "full_delivery_low_risk_batch2_recheck_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    recheck = package.get("第二批低风险复核台账", [])
    recheck_text = json.dumps(recheck, ensure_ascii=False)
    recheck_ok = len(recheck) >= 6 and "未生效" in recheck_text and "未导入未触发" in recheck_text and "未渲染未发布" in recheck_text
    add_check(checks, "第二批复核保持低风险", recheck_ok, f"复核项={len(recheck)}")

    static_items = package.get("静态检查与禁用态确认", [])
    static_text = json.dumps(static_items, ensure_ascii=False)
    static_ok = len(static_items) >= 5 and "未写正式规则" in static_text and "未真实触发" in static_text and "未重载" in static_text
    add_check(checks, "静态检查与禁用态确认有效", static_ok, f"静态项={len(static_items)}")

    next_items = package.get("第三批低风险续建建议", [])
    next_text = json.dumps(next_items, ensure_ascii=False)
    next_ok = len(next_items) >= 4 and "不解锁" in next_text and "不启用自治" in next_text
    add_check(checks, "第三批建议仍不解锁", next_ok, f"建议项={len(next_items)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "完全交付使用版低风险续建第二批复核包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "第二批低风险复核台账": str(RECHECK_MD),
            "静态检查与禁用态确认": str(STATIC_MD),
            "第三批低风险续建建议": str(NEXT_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
