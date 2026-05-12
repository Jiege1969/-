# -*- coding: utf-8 -*-
"""验证交付后首日运行观察与问题登记包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "81交付后首日运行观察与问题登记包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "交付后首日运行观察与问题登记包验收"

PACKAGE_JSON = DATA_DIR / "交付后首日运行观察与问题登记包_最新.json"
PACKAGE_MD = DATA_DIR / "交付后首日运行观察与问题登记包_最新.md"
OBSERVE_MD = DATA_DIR / "首日运行观察清单_最新.md"
ISSUE_LEDGER_JSON = DATA_DIR / "首日问题登记台账模板_最新.json"
ISSUE_LEDGER_MD = DATA_DIR / "首日问题登记台账模板_最新.md"
RECHECK_MD = DATA_DIR / "首日复验建议_最新.md"
GEN_LOG = LOG_DIR / "生成交付后首日运行观察与问题登记包_最新.json"
VERIFY_JSON = LOG_DIR / "day1-operation-observation-issue-ledger-verify-最新.json"
VERIFY_MD = LOG_DIR / "day1-operation-observation-issue-ledger-verify-最新.md"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, OBSERVE_MD, ISSUE_LEDGER_JSON, ISSUE_LEDGER_MD, RECHECK_MD, GEN_LOG]
REQUIRED_DOMAINS = ["企业微信", "税收", "股票", "视频", "n8n", "进化", "19310/19302", "总巡检"]
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
    "允许重载19310",
    "允许重载19302",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "day1_observation_ready":
        errors.append("状态不正确")
    items = package.get("观察项", [])
    if len(items) < 8:
        errors.append("观察项不足8条")
    joined_items = json.dumps(items, ensure_ascii=False)
    for domain in REQUIRED_DOMAINS:
        if domain not in joined_items:
            errors.append(f"缺少观察域：{domain}")
    if package.get("当前总巡检", {}).get("总体状态") != "pass":
        errors.append("当前总巡检不是pass")
    regression_metrics = package.get("当前一键只读总回归", {}).get("指标", {})
    if regression_metrics.get("错误数", 0) != 0:
        errors.append("当前一键只读总回归错误数不为0")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    ledger = read_json(ISSUE_LEDGER_JSON) if ISSUE_LEDGER_JSON.exists() else {}
    template = ledger.get("模板", [])
    if not template:
        errors.append("问题台账模板为空")
    elif template[0].get("处理状态") != "待确认":
        errors.append("问题台账默认状态不是待确认")

    all_text = json.dumps(package, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")

    report = {
        "名称": "交付后首日运行观察与问题登记包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "观察项": len(items),
            "覆盖域": len(REQUIRED_DOMAINS),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    VERIFY_MD.write_text(
        "\n".join([
            "# 交付后首日运行观察与问题登记包验收",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 通过：{report['通过']}",
            f"- 错误数：{len(errors)}",
            "",
            "## 错误",
            "",
            "\n".join(f"- {item}" for item in errors) if errors else "- 无",
        ]),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
