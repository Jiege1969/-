# -*- coding: utf-8 -*-
"""只读验收完全交付使用版低风险续建启动队列包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "102完全交付使用版低风险续建启动队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建启动队列包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建启动队列包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建启动队列包_最新.md"
QUEUE_MD = DATA_DIR / "低风险续建启动队列_最新.md"
GATE_MD = DATA_DIR / "红线解锁申请队列_最新.md"
VERIFY_MD = DATA_DIR / "续建验收与回滚要求_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建启动队列包_最新.json"
VERIFY_LOG = LOG_DIR / "full-delivery-low-risk-continue-queue-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, QUEUE_MD, GATE_MD, VERIFY_MD, GEN_LOG]
REQUIRED_GATES = ["企业微信", "n8n", "正式规则", "视频", "券商", "税局", "19310"]
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
        package.get("状态") == "full_delivery_low_risk_continue_queue_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 10 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    queue = package.get("低风险续建启动队列", [])
    queue_text = json.dumps(queue, ensure_ascii=False)
    queue_ok = len(queue) >= 6 and "模板" in queue_text and "n8n" in queue_text and "视频" in queue_text and "长期运行样本" in queue_text
    add_check(checks, "低风险续建队列有效", queue_ok, f"低风险项={len(queue)}")

    gates = package.get("红线解锁申请队列", [])
    gate_text = json.dumps(gates, ensure_ascii=False)
    gate_ok = len(gates) >= 7 and all(marker in gate_text for marker in REQUIRED_GATES) and "关闭" in gate_text
    add_check(checks, "红线解锁申请队列有效", gate_ok, f"红线项={len(gates)}")

    verify_items = package.get("续建验收与回滚要求", [])
    verify_text = json.dumps(verify_items, ensure_ascii=False)
    verify_ok = len(verify_items) >= 6 and "只读验收" in verify_text and "回滚" in verify_text and "正式规则" in verify_text
    add_check(checks, "续建验收回滚要求有效", verify_ok, f"要求项={len(verify_items)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "完全交付使用版低风险续建启动队列包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "低风险续建启动队列": str(QUEUE_MD),
            "红线解锁申请队列": str(GATE_MD),
            "续建验收与回滚要求": str(VERIFY_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
