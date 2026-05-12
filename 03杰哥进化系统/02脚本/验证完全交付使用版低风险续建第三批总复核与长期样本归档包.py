# -*- coding: utf-8 -*-
"""只读验收完全交付使用版低风险续建第三批总复核与长期样本归档包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "105完全交付使用版低风险续建第三批总复核与长期样本归档包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建第三批总复核与长期样本归档包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.md"
RECHECK_MD = DATA_DIR / "第三批低风险总复核台账_最新.md"
SAMPLE_MD = DATA_DIR / "长期样本归档入口_最新.md"
GAP_MD = DATA_DIR / "后续缺口与确认事项_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json"
VERIFY_LOG = LOG_DIR / "full-delivery-low-risk-batch3-sample-archive-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, RECHECK_MD, SAMPLE_MD, GAP_MD, GEN_LOG]
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
        package.get("状态") == "full_delivery_low_risk_batch3_sample_archive_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    recheck = package.get("第三批低风险总复核台账", [])
    recheck_text = json.dumps(recheck, ensure_ascii=False)
    recheck_ok = len(recheck) >= 5 and "真实能力" in recheck_text and "未启用" in recheck_text and "不修改日常版和稳定版封存结论" in recheck_text
    add_check(checks, "第三批总复核保持低风险", recheck_ok, f"复核项={len(recheck)}")

    samples = package.get("长期样本归档入口", [])
    sample_text = json.dumps(samples, ensure_ascii=False)
    sample_ok = len(samples) >= 5 and "周报" in sample_text and "日报" in sample_text and "只读归档" in sample_text
    add_check(checks, "长期样本归档入口有效", sample_ok, f"样本入口={len(samples)}")

    gaps = package.get("后续缺口与确认事项", [])
    gap_text = json.dumps(gaps, ensure_ascii=False)
    gap_ok = len(gaps) >= 5 and "总管确认" in gap_text and "真正自主运行" in gap_text and "n8n" in gap_text
    add_check(checks, "后续缺口仍需确认", gap_ok, f"缺口={len(gaps)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "完全交付使用版低风险续建第三批总复核与长期样本归档包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "第三批低风险总复核台账": str(RECHECK_MD),
            "长期样本归档入口": str(SAMPLE_MD),
            "后续缺口与确认事项": str(GAP_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
