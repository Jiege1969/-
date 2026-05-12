# -*- coding: utf-8 -*-
"""验证运行期问题闭环总台账索引包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期问题闭环总台账索引包验收"

PACKAGE_JSON = DATA_DIR / "运行期问题闭环总台账索引包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期问题闭环总台账索引包_最新.md"
LEDGER_JSON = DATA_DIR / "运行期问题总台账模板_最新.json"
LEDGER_MD = DATA_DIR / "运行期问题总台账模板_最新.md"
STATE_MD = DATA_DIR / "问题状态流转说明_最新.md"
EVIDENCE_MD = DATA_DIR / "运行期证据入口索引_最新.md"
GEN_LOG = LOG_DIR / "生成运行期问题闭环总台账索引包_最新.json"
VERIFY_JSON = LOG_DIR / "runtime-issue-loop-ledger-index-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, LEDGER_JSON, LEDGER_MD, STATE_MD, EVIDENCE_MD, GEN_LOG]
REQUIRED_STATES = {"发现", "候选", "复验", "升级", "暂停", "关闭"}
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
    if package.get("状态") != "runtime_issue_loop_ledger_index_ready":
        errors.append("状态不正确")
    sources = package.get("来源摘要", {})
    if len(sources) < 7:
        errors.append("来源摘要不足7项")
    for name, item in sources.items():
        if item.get("存在") is not True:
            errors.append(f"来源不存在：{name}")
    states = {item.get("状态") for item in package.get("状态流转", [])}
    if not REQUIRED_STATES.issubset(states):
        errors.append(f"状态流转不完整：{sorted(states)}")
    template = package.get("台账模板", [])
    if not template:
        errors.append("台账模板为空")
    elif template[0].get("当前状态") != "发现":
        errors.append("台账模板默认状态不是发现")
    if not any(item.get("需总管确认") is True for item in package.get("状态流转", [])):
        errors.append("状态流转缺少需总管确认项")
    if not any(item.get("需总管确认") is False for item in package.get("状态流转", [])):
        errors.append("状态流转缺少低风险项")
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
        "名称": "运行期问题闭环总台账索引包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "来源数": len(sources),
            "状态数": len(states),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
