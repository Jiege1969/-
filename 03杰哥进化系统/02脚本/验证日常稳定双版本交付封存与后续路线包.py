# -*- coding: utf-8 -*-
"""只读验收日常稳定双版本交付封存与后续路线包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "100日常稳定双版本交付封存与后续路线包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定双版本交付封存与后续路线包验收"

PACKAGE_JSON = DATA_DIR / "日常稳定双版本交付封存与后续路线包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定双版本交付封存与后续路线包_最新.md"
FREEZE_MD = DATA_DIR / "双版本交付封存说明_最新.md"
ROUTE_MD = DATA_DIR / "后续路线分层清单_最新.md"
KEEP_MD = DATA_DIR / "封存后守护与复验清单_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定双版本交付封存与后续路线包_最新.json"
VERIFY_LOG = LOG_DIR / "daily-stable-dual-delivery-freeze-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, FREEZE_MD, ROUTE_MD, KEEP_MD, GEN_LOG]
REQUIRED_ROUTES = ["日常可用版", "稳定交付版", "正式规则", "n8n", "视频", "真实业务连接"]
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
        package.get("状态") == "daily_stable_dual_delivery_freeze_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 8 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    freeze = package.get("双版本交付封存说明", [])
    freeze_text = json.dumps(freeze, ensure_ascii=False)
    freeze_ok = (
        len(freeze) >= 4
        and "日常可用交付版" in freeze_text
        and "已封存为可签收使用" in freeze_text
        and "稳定交付版" in freeze_text
        and "已封存为本地试运行签收完成" in freeze_text
        and "真正自主运行版" in freeze_text
    )
    add_check(checks, "双版本封存说明有效", freeze_ok, f"封存项={len(freeze)}")

    routes = package.get("后续路线分层清单", [])
    route_text = json.dumps(routes, ensure_ascii=False)
    route_ok = len(routes) >= 6 and all(marker in route_text for marker in REQUIRED_ROUTES) and "是" in route_text and "否" in route_text
    add_check(checks, "后续路线分层有效", route_ok, f"路线项={len(routes)}")

    keep = package.get("封存后守护与复验清单", [])
    keep_text = json.dumps(keep, ensure_ascii=False)
    keep_ok = len(keep) >= 6 and "只读总回归" in keep_text and "自主巡检快照" in keep_text and "红线闸口" in keep_text
    add_check(checks, "封存后守护清单有效", keep_ok, f"守护项={len(keep)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "日常稳定双版本交付封存与后续路线包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "双版本交付封存说明": str(FREEZE_MD),
            "后续路线分层清单": str(ROUTE_MD),
            "封存后守护与复验清单": str(KEEP_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
