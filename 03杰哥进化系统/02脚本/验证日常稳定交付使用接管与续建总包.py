# -*- coding: utf-8 -*-
"""只读验收日常稳定交付使用接管与续建总包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定交付使用接管与续建总包验收"

PACKAGE_JSON = DATA_DIR / "日常稳定交付使用接管与续建总包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定交付使用接管与续建总包_最新.md"
HANDOFF_MD = DATA_DIR / "使用接管清单_最新.md"
CONTINUE_MD = DATA_DIR / "后续低风险续建清单_最新.md"
GATE_MD = DATA_DIR / "必须总管确认事项清单_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定交付使用接管与续建总包_最新.json"
VERIFY_LOG = LOG_DIR / "daily-stable-handoff-continue-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, HANDOFF_MD, CONTINUE_MD, GATE_MD, GEN_LOG]
REQUIRED_GATES = ["19310", "19302", "正式规则", "n8n", "企业微信", "券商", "税局", "视频"]
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
        package.get("状态") == "daily_stable_handoff_continue_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    handoff = package.get("使用接管清单", [])
    add_check(checks, "使用接管清单足量", len(handoff) >= 8, f"接管事项={len(handoff)}")

    continue_items = package.get("后续低风险续建清单", [])
    has_confirm = any(item.get("需总管确认") is True for item in continue_items if isinstance(item, dict))
    has_no_confirm = any(item.get("需总管确认") is False for item in continue_items if isinstance(item, dict))
    add_check(checks, "续建清单区分低风险与需确认", len(continue_items) >= 7 and has_confirm and has_no_confirm, f"续建事项={len(continue_items)}")

    gates = package.get("必须总管确认事项", [])
    gate_text = json.dumps(gates, ensure_ascii=False)
    add_check(checks, "必须确认事项覆盖红线", len(gates) >= 7 and all(marker in gate_text for marker in REQUIRED_GATES), f"闸口事项={len(gates)}")

    delivery = package.get("交付判断", {})
    add_check(
        checks,
        "交付判断分层",
        delivery.get("日常可用交付版") == "可签收使用"
        and delivery.get("稳定交付版") == "可签收试运行"
        and delivery.get("真正自主运行版") == "继续排队",
        json.dumps(delivery, ensure_ascii=False),
    )

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "日常稳定交付使用接管与续建总包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "使用接管清单": str(HANDOFF_MD),
            "后续低风险续建清单": str(CONTINUE_MD),
            "必须总管确认事项清单": str(GATE_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
