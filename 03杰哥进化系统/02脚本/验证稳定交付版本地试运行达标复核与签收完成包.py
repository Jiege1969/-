# -*- coding: utf-8 -*-
"""只读验收稳定交付版本地试运行达标复核与签收完成包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99稳定交付版本地试运行达标复核与签收完成包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定交付版本地试运行达标复核与签收完成包验收"

PACKAGE_JSON = DATA_DIR / "稳定交付版本地试运行达标复核与签收完成包_最新.json"
PACKAGE_MD = DATA_DIR / "稳定交付版本地试运行达标复核与签收完成包_最新.md"
PASS_MD = DATA_DIR / "稳定交付版达标复核结论_最新.md"
SIGNOFF_MD = DATA_DIR / "稳定交付版签收完成说明_最新.md"
KEEP_MD = DATA_DIR / "签收后持续运行守护清单_最新.md"
GEN_LOG = LOG_DIR / "生成稳定交付版本地试运行达标复核与签收完成包_最新.json"
VERIFY_LOG = LOG_DIR / "stable-local-trial-acceptance-signoff-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, PASS_MD, SIGNOFF_MD, KEEP_MD, GEN_LOG]
REQUIRED_PASS = ["入口", "税收", "股票", "视频", "问题回收", "红线"]
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
        package.get("状态") == "stable_local_trial_acceptance_signoff_done",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    pass_items = package.get("稳定交付版达标复核结论", [])
    pass_text = json.dumps(pass_items, ensure_ascii=False)
    pass_ok = len(pass_items) >= 6 and all(marker in pass_text for marker in REQUIRED_PASS) and "达标" in pass_text
    add_check(checks, "达标复核覆盖关键链路", pass_ok, f"复核项={len(pass_items)}")

    signoff = package.get("稳定交付版签收完成说明", [])
    signoff_text = json.dumps(signoff, ensure_ascii=False)
    signoff_ok = len(signoff) >= 4 and "稳定交付版" in signoff_text and "已具备本地试运行签收完成条件" in signoff_text and "真正自主运行版" in signoff_text
    add_check(checks, "签收完成说明分层", signoff_ok, f"签收项={len(signoff)}")

    keep = package.get("签收后持续运行守护清单", [])
    keep_text = json.dumps(keep, ensure_ascii=False)
    keep_ok = len(keep) >= 6 and "一键只读总回归" in keep_text and "需确认事项" in keep_text and "回滚" in keep_text
    add_check(checks, "持续运行守护清单有效", keep_ok, f"守护项={len(keep)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "稳定交付版本地试运行达标复核与签收完成包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "稳定交付版达标复核结论": str(PASS_MD),
            "稳定交付版签收完成说明": str(SIGNOFF_MD),
            "签收后持续运行守护清单": str(KEEP_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
