# -*- coding: utf-8 -*-
"""验证运行期证据归档与版本冻结候选包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "86运行期证据归档与版本冻结候选包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期证据归档与版本冻结候选包验收"

PACKAGE_JSON = DATA_DIR / "运行期证据归档与版本冻结候选包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期证据归档与版本冻结候选包_最新.md"
EVIDENCE_JSON = DATA_DIR / "运行期证据归档索引_最新.json"
EVIDENCE_MD = DATA_DIR / "运行期证据归档索引_最新.md"
FREEZE_MD = DATA_DIR / "版本冻结候选说明_最新.md"
HANDOFF_MD = DATA_DIR / "冻结候选交接清单_最新.md"
GEN_LOG = LOG_DIR / "生成运行期证据归档与版本冻结候选包_最新.json"
VERIFY_JSON = LOG_DIR / "runtime-evidence-freeze-candidate-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, EVIDENCE_JSON, EVIDENCE_MD, FREEZE_MD, HANDOFF_MD, GEN_LOG]
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
    if package.get("状态") != "runtime_evidence_freeze_candidate_ready":
        errors.append("状态不正确")
    evidence = package.get("证据归档索引", {})
    if len(evidence) < 9:
        errors.append("证据索引不足9项")
    for name, item in evidence.items():
        if item.get("存在") is not True:
            errors.append(f"证据来源不存在：{name}")
    prereq = package.get("冻结前提", {})
    for key in ["总巡检通过", "一键总回归通过", "来源全部存在", "红线全部关闭"]:
        if prereq.get(key) is not True:
            errors.append(f"冻结前提不满足：{key}")
    if "正式规则封版仍需总管确认" not in package.get("冻结候选结论", ""):
        errors.append("冻结候选结论缺少总管确认口径")
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
        "名称": "运行期证据归档与版本冻结候选包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "证据数": len(evidence),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
