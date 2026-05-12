# -*- coding: utf-8 -*-
"""验证运行期故障恢复与回滚总索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期故障恢复与回滚总索引包验收"

PACKAGE_JSON = DATA_DIR / "运行期故障恢复与回滚总索引包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期故障恢复与回滚总索引包_最新.md"
RECOVERY_JSON = DATA_DIR / "故障恢复路线图_最新.json"
RECOVERY_MD = DATA_DIR / "故障恢复路线图_最新.md"
ROLLBACK_MD = DATA_DIR / "回滚与停机闸口索引_最新.md"
HANDOFF_MD = DATA_DIR / "人工接管恢复清单_最新.md"
GEN_LOG = LOG_DIR / "生成运行期故障恢复与回滚总索引包_最新.json"
VERIFY_JSON = LOG_DIR / "runtime-recovery-rollback-index-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, RECOVERY_JSON, RECOVERY_MD, ROLLBACK_MD, HANDOFF_MD, GEN_LOG]
REQUIRED_SCENARIOS = {"总巡检失败", "一键总回归失败", "触碰红线", "n8n启用/导入风险", "正式规则申请", "视频真实渲染风险"}
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
    "允许执行真实回滚",
    "允许重载19310",
    "允许重载19302",
]


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8-sig")) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "runtime_recovery_rollback_index_ready":
        errors.append("状态不正确")
    sources = package.get("来源摘要", {})
    if len(sources) < 7:
        errors.append("来源摘要不足7项")
    for name, item in sources.items():
        if item.get("存在") is not True:
            errors.append(f"来源不存在：{name}")
    routes = package.get("故障恢复路线", [])
    scenarios = {item.get("场景") for item in routes}
    if not REQUIRED_SCENARIOS.issubset(scenarios):
        errors.append(f"恢复场景不完整：{sorted(scenarios)}")
    if not any(item.get("需总管确认") is True for item in routes):
        errors.append("缺少需总管确认路线")
    if not any(item.get("需总管确认") is False for item in routes):
        errors.append("缺少低风险自主路线")
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
        "名称": "运行期故障恢复与回滚总索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "来源数": len(sources),
            "恢复路线": len(routes),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
