# -*- coding: utf-8 -*-
"""只读验收日常签收完成与稳定试运行启动回传包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常签收完成与稳定试运行启动回传包验收"

PACKAGE_JSON = DATA_DIR / "日常签收完成与稳定试运行启动回传包_最新.json"
PACKAGE_MD = DATA_DIR / "日常签收完成与稳定试运行启动回传包_最新.md"
SIGNOFF_DONE_MD = DATA_DIR / "日常可用版签收完成说明_最新.md"
STABLE_START_MD = DATA_DIR / "稳定版试运行启动说明_最新.md"
REMAINING_GAPS_MD = DATA_DIR / "剩余缺口与红线说明_最新.md"
GEN_LOG = LOG_DIR / "生成日常签收完成与稳定试运行启动回传包_最新.json"
VERIFY_LOG = LOG_DIR / "daily-signoff-done-stable-trial-start-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, SIGNOFF_DONE_MD, STABLE_START_MD, REMAINING_GAPS_MD, GEN_LOG]
REQUIRED_GAPS = ["完全交付使用版", "真正自主运行版", "n8n", "视频", "正式规则"]
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
        package.get("状态") == "daily_signoff_done_stable_trial_start_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 6 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    signoff = package.get("日常可用版签收完成说明", [])
    signoff_text = json.dumps(signoff, ensure_ascii=False)
    add_check(checks, "日常签收完成说明有效", len(signoff) >= 3 and "完成签收条件" in signoff_text and "可进入日常使用" in signoff_text, f"签收说明={len(signoff)}")

    stable = package.get("稳定版试运行启动说明", [])
    stable_text = json.dumps(stable, ensure_ascii=False)
    add_check(checks, "稳定试运行启动观察点有效", len(stable) >= 5 and "每日一键只读回归" in stable_text and "反馈本地入账" in stable_text, f"观察点={len(stable)}")

    gaps = package.get("剩余缺口与红线说明", [])
    gap_text = json.dumps(gaps, ensure_ascii=False)
    add_check(checks, "剩余缺口覆盖关键红线", len(gaps) >= 5 and all(marker in gap_text for marker in REQUIRED_GAPS), f"缺口={len(gaps)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "日常签收完成与稳定试运行启动回传包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "日常可用版签收完成说明": str(SIGNOFF_DONE_MD),
            "稳定版试运行启动说明": str(STABLE_START_MD),
            "剩余缺口与红线说明": str(REMAINING_GAPS_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
