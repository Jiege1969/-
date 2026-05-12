# -*- coding: utf-8 -*-
"""只读验收首周试用结果汇总与签收复核包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "91首周试用结果汇总与签收复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "首周试用结果汇总与签收复核包验收"

PACKAGE_JSON = DATA_DIR / "首周试用结果汇总与签收复核包_最新.json"
PACKAGE_MD = DATA_DIR / "首周试用结果汇总与签收复核包_最新.md"
SUMMARY_JSON = DATA_DIR / "首周试用结果汇总_最新.json"
SUMMARY_MD = DATA_DIR / "首周试用结果汇总_最新.md"
SIGNOFF_RECHECK_MD = DATA_DIR / "签收复核清单_最新.md"
NEXT_MD = DATA_DIR / "试用后下一步建议_最新.md"
GEN_LOG = LOG_DIR / "生成首周试用结果汇总与签收复核包_最新.json"
VERIFY_LOG = LOG_DIR / "week1-trial-signoff-recheck-verify-最新.json"

REQUIRED_FILES = [
    PACKAGE_JSON,
    PACKAGE_MD,
    SUMMARY_JSON,
    SUMMARY_MD,
    SIGNOFF_RECHECK_MD,
    NEXT_MD,
    GEN_LOG,
]

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

EXPECTED_RECHECK = [
    "日常可用版",
    "稳定交付版",
    "完全交付使用版",
    "真正自主运行版",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def text_blob(paths: list[Path]) -> str:
    parts: list[str] = []
    for path in paths:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8-sig", errors="ignore"))
    return "\n".join(parts)


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"名称": name, "通过": passed, "详情": detail})


def main() -> int:
    checks: list[dict[str, Any]] = []
    package = read_json(PACKAGE_JSON)

    missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
    add_check(checks, "必需文件存在", not missing, "缺失: " + "；".join(missing) if missing else "全部存在")

    add_check(
        checks,
        "包状态就绪",
        package.get("状态") == "week1_trial_signoff_recheck_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    source_exists = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 6 and source_exists, f"来源数={len(sources)}，全部存在={source_exists}")

    recheck = package.get("签收复核", [])
    recheck_text = json.dumps(recheck, ensure_ascii=False)
    recheck_passed = len(recheck) >= 4 and all(marker in recheck_text for marker in EXPECTED_RECHECK)
    add_check(checks, "签收复核覆盖四类版本", recheck_passed, f"复核项={len(recheck)}")

    next_steps = package.get("试用后下一步", [])
    has_confirm = any(item.get("需总管确认") is True for item in next_steps if isinstance(item, dict))
    has_no_confirm = any(item.get("需总管确认") is False for item in next_steps if isinstance(item, dict))
    add_check(checks, "试用后下一步分层", len(next_steps) >= 5 and has_confirm and has_no_confirm, f"事项={len(next_steps)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    all_text = text_blob(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed_count = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "首周试用结果汇总与签收复核包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {
            "检查项": len(checks),
            "通过项": passed_count,
            "错误数": len(failed),
        },
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "签收复核清单": str(SIGNOFF_RECHECK_MD),
            "试用后下一步建议": str(NEXT_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
