# -*- coding: utf-8 -*-
"""验证使用者验收签收与后续迭代队列包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "89使用者验收签收与后续迭代队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者验收签收与后续迭代队列包验收"

PACKAGE_JSON = DATA_DIR / "使用者验收签收与后续迭代队列包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者验收签收与后续迭代队列包_最新.md"
SIGNOFF_MD = DATA_DIR / "使用者签收检查清单_最新.md"
ITERATION_JSON = DATA_DIR / "后续迭代队列_最新.json"
ITERATION_MD = DATA_DIR / "后续迭代队列_最新.md"
HANDOFF_MD = DATA_DIR / "签收后使用说明_最新.md"
GEN_LOG = LOG_DIR / "生成使用者验收签收与后续迭代队列包_最新.json"
VERIFY_JSON = LOG_DIR / "user-signoff-iteration-queue-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, SIGNOFF_MD, ITERATION_JSON, ITERATION_MD, HANDOFF_MD, GEN_LOG]
REQUIRED_SIGNOFF = {"日常可用版", "稳定交付版", "完全交付使用版", "真正自主运行版"}
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


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8-sig")) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "user_signoff_iteration_queue_ready":
        errors.append("状态不正确")
    sources = package.get("来源摘要", {})
    if len(sources) < 6:
        errors.append("来源摘要不足6项")
    for name, item in sources.items():
        if item.get("存在") is not True:
            errors.append(f"来源不存在：{name}")
    signoff = package.get("签收检查清单", [])
    signoff_names = {item.get("项目") for item in signoff}
    if not REQUIRED_SIGNOFF.issubset(signoff_names):
        errors.append(f"签收项目不完整：{sorted(signoff_names)}")
    if not any(item.get("签收状态") == "可签收使用" for item in signoff):
        errors.append("缺少可签收使用项")
    if not any(item.get("签收状态") == "不在本次签收范围" for item in signoff):
        errors.append("缺少不在本次签收范围项")
    queue = package.get("后续迭代队列", [])
    if len(queue) < 6:
        errors.append("后续迭代队列不足6项")
    if not any(item.get("需总管确认") is True for item in queue):
        errors.append("后续队列缺少需总管确认项")
    if not any(item.get("需总管确认") is False for item in queue):
        errors.append("后续队列缺少低风险项")
    if "日常可用版与稳定交付版可签收使用" not in package.get("签收结论", ""):
        errors.append("签收结论不明确")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    all_text = json.dumps(package, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")
    report = {
        "名称": "使用者验收签收与后续迭代队列包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "来源数": len(sources),
            "签收项": len(signoff),
            "迭代项": len(queue),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
