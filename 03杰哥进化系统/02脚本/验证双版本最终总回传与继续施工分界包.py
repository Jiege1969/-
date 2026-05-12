# -*- coding: utf-8 -*-
"""只读验收双版本最终总回传与继续施工分界包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101双版本最终总回传与继续施工分界包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "双版本最终总回传与继续施工分界包验收"

PACKAGE_JSON = DATA_DIR / "双版本最终总回传与继续施工分界包_最新.json"
PACKAGE_MD = DATA_DIR / "双版本最终总回传与继续施工分界包_最新.md"
FINAL_RETURN_MD = DATA_DIR / "双版本最终总回传_最新.md"
BOUNDARY_MD = DATA_DIR / "继续施工分界清单_最新.md"
NEXT_WORK_MD = DATA_DIR / "下一阶段施工路线_最新.md"
GEN_LOG = LOG_DIR / "生成双版本最终总回传与继续施工分界包_最新.json"
VERIFY_LOG = LOG_DIR / "dual-version-final-return-boundary-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, FINAL_RETURN_MD, BOUNDARY_MD, NEXT_WORK_MD, GEN_LOG]
REQUIRED_BOUNDARIES = ["已封存版本", "正式规则", "企业微信", "n8n", "股票", "税收", "视频", "服务"]
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
        package.get("状态") == "dual_version_final_return_boundary_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 7 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    final_return = package.get("双版本最终总回传", [])
    final_text = json.dumps(final_return, ensure_ascii=False)
    final_ok = (
        len(final_return) >= 4
        and "日常可用交付版" in final_text
        and "已完成并封存" in final_text
        and "稳定交付版" in final_text
        and "已完成本地试运行签收封存" in final_text
        and "继续施工" in final_text
    )
    add_check(checks, "双版本最终总回传有效", final_ok, f"回传项={len(final_return)}")

    boundaries = package.get("继续施工分界清单", [])
    boundary_text = json.dumps(boundaries, ensure_ascii=False)
    boundary_ok = len(boundaries) >= 8 and all(marker in boundary_text for marker in REQUIRED_BOUNDARIES)
    add_check(checks, "继续施工分界清楚", boundary_ok, f"分界项={len(boundaries)}")

    next_work = package.get("下一阶段施工路线", [])
    next_text = json.dumps(next_work, ensure_ascii=False)
    next_ok = len(next_work) >= 6 and "稳定版持续运行" in next_text and "真正自主运行准备" in next_text
    add_check(checks, "下一阶段施工路线有效", next_ok, f"路线项={len(next_work)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "双版本最终总回传与继续施工分界包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "双版本最终总回传": str(FINAL_RETURN_MD),
            "继续施工分界清单": str(BOUNDARY_MD),
            "下一阶段施工路线": str(NEXT_WORK_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
