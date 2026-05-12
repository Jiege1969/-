# -*- coding: utf-8 -*-
"""只读验收红线材料缺口低风险补齐第一批模板包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "108红线材料缺口低风险补齐第一批模板包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "红线材料缺口低风险补齐第一批模板包验收"

PACKAGE_JSON = DATA_DIR / "红线材料缺口低风险补齐第一批模板包_最新.json"
PACKAGE_MD = DATA_DIR / "红线材料缺口低风险补齐第一批模板包_最新.md"
WECOM_MD = DATA_DIR / "企业微信发送对象确认模板_最新.md"
RELOAD_MD = DATA_DIR / "服务重载操作窗口登记模板_最新.md"
N8N_MD = DATA_DIR / "n8n禁用态静态扫描二轮摘要模板_最新.md"
VIDEO_MD = DATA_DIR / "视频白名单生效前拒收口径模板_最新.md"
RULE_MD = DATA_DIR / "正式规则申请人工签收补充页模板_最新.md"
GEN_LOG = LOG_DIR / "生成红线材料缺口低风险补齐第一批模板包_最新.json"
VERIFY_LOG = LOG_DIR / "redline-gap-low-risk-template-batch1-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, WECOM_MD, RELOAD_MD, N8N_MD, VIDEO_MD, RULE_MD, GEN_LOG]
REQUIRED_TEMPLATES = ["企业微信", "服务重载", "n8n", "视频", "正式规则"]
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
        package.get("状态") == "redline_gap_low_risk_template_batch1_ready",
        str(package.get("状态")),
    )

    sources = package.get("来源摘要", {})
    all_sources_exist = bool(sources) and all(item.get("存在") is True for item in sources.values() if isinstance(item, dict))
    add_check(checks, "来源摘要完整", len(sources) >= 5 and all_sources_exist, f"来源数={len(sources)}，全部存在={all_sources_exist}")

    templates = package.get("补齐模板清单", [])
    template_text = json.dumps(templates, ensure_ascii=False)
    template_ok = len(templates) >= 5 and all(marker in template_text for marker in REQUIRED_TEMPLATES) and "仅模板" in template_text
    add_check(checks, "补齐模板覆盖缺口", template_ok, f"模板数={len(templates)}")

    guards = package.get("模板守护口径", [])
    guard_text = json.dumps(guards, ensure_ascii=False)
    guard_ok = len(guards) >= 5 and "不发送消息" in guard_text and "不重载服务" in guard_text and "不导入不触发" in guard_text and "不写正式规则" in guard_text
    add_check(checks, "模板守护口径有效", guard_ok, f"守护项={len(guards)}")

    safety = package.get("安全边界", {})
    safety_ok = bool(safety) and all(value is False for value in safety.values())
    add_check(checks, "安全边界保持关闭", safety_ok, f"边界项={len(safety)}")

    text = combined_text(REQUIRED_FILES)
    forbidden_hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
    add_check(checks, "禁用放行语句未出现", not forbidden_hits, "命中: " + "；".join(forbidden_hits) if forbidden_hits else "未命中")

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "红线材料缺口低风险补齐第一批模板包验收",
        "验收时间": now_text(),
        "通过": not failed,
        "指标": {"检查项": len(checks), "通过项": passed, "错误数": len(failed)},
        "检查明细": checks,
        "输出文件": {
            "验收日志": str(VERIFY_LOG),
            "总包": str(PACKAGE_JSON),
            "企业微信发送对象确认模板": str(WECOM_MD),
            "服务重载操作窗口登记模板": str(RELOAD_MD),
            "n8n禁用态静态扫描二轮摘要模板": str(N8N_MD),
            "视频白名单生效前拒收口径模板": str(VIDEO_MD),
            "正式规则申请人工签收补充页模板": str(RULE_MD),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_LOG.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": result["通过"], "检查项": len(checks), "错误数": len(failed), "日志": str(VERIFY_LOG)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
