# -*- coding: utf-8 -*-
"""验证三业务正式规则申请草案冲突扫描与签收台账包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包"
LOG_DIR = ROOT / "04日志" / "三业务正式规则申请草案冲突扫描与签收台账包验收"

PACKAGE_JSON = DATA_DIR / "三业务正式规则申请草案冲突扫描与签收台账包_最新.json"
SCAN_RULE_JSON = DATA_DIR / "冲突扫描规则_最新.json"
SCAN_RULE_MD = DATA_DIR / "冲突扫描规则_最新.md"
SIGNOFF_FIELD_JSON = DATA_DIR / "签收台账字段_最新.json"
SIGNOFF_FIELD_MD = DATA_DIR / "签收台账字段_最新.md"
DRAFT_EXAMPLE_JSON = DATA_DIR / "三业务正式规则申请草案扫描示例_最新.json"
SCAN_RESULT_JSON = DATA_DIR / "三业务草案冲突扫描结果_最新.json"
SCAN_RESULT_MD = DATA_DIR / "三业务草案冲突扫描结果_最新.md"
SIGNOFF_LEDGER_JSON = DATA_DIR / "签收台账_最新.json"
SIGNOFF_LEDGER_MD = DATA_DIR / "签收台账_最新.md"
LOG_JSON = LOG_DIR / "three-business-rule-draft-conflict-signoff-verify-最新.json"

REQUIRED_OUTPUTS = [
    PACKAGE_JSON,
    SCAN_RULE_JSON,
    SCAN_RULE_MD,
    SIGNOFF_FIELD_JSON,
    SIGNOFF_FIELD_MD,
    DRAFT_EXAMPLE_JSON,
    SCAN_RESULT_JSON,
    SCAN_RESULT_MD,
    SIGNOFF_LEDGER_JSON,
    SIGNOFF_LEDGER_MD,
]
REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_CONFLICT_TYPES = {
    "红线冲突",
    "跨业务职责冲突",
    "旧口径回潮",
    "正式规则自动生效",
    "缺少回滚办法",
    "缺少总管确认",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_flags(data: dict[str, Any], name: str, errors: list[str]) -> None:
    if data.get("正式生效") is not False:
        errors.append(f"{name} 必须为正式生效=false")
    if data.get("写正式规则") is not False:
        errors.append(f"{name} 必须为写正式规则=false")
    if data.get("需总管确认") is not True:
        errors.append(f"{name} 必须为需总管确认=true")
    if data.get("自动转正式规则") is True:
        errors.append(f"{name} 不得自动转正式规则")
    if data.get("触发外部系统") is True:
        errors.append(f"{name} 不得触发外部系统")


def validate_rows(rows: list[dict[str, Any]], row_name: str, errors: list[str]) -> None:
    if len(rows) < 3:
        errors.append(f"{row_name} 不得少于3条")
    if {row.get("业务") for row in rows} != REQUIRED_BUSINESSES:
        errors.append(f"{row_name} 必须覆盖税收/股票/视频")
    for row in rows:
        if row.get("签收状态") != "待签收":
            errors.append(f"{row_name} {row.get('草案ID', 'UNKNOWN')} 默认签收状态必须为待签收")
        if row.get("正式生效") is not False:
            errors.append(f"{row_name} {row.get('草案ID', 'UNKNOWN')} 正式生效必须为false")
        if row.get("写正式规则") is not False:
            errors.append(f"{row_name} {row.get('草案ID', 'UNKNOWN')} 写正式规则必须为false")
        if row.get("需总管确认") is not True:
            errors.append(f"{row_name} {row.get('草案ID', 'UNKNOWN')} 需总管确认必须为true")


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    scan_rule = read_json(SCAN_RULE_JSON) if SCAN_RULE_JSON.exists() else {}
    signoff_fields = read_json(SIGNOFF_FIELD_JSON) if SIGNOFF_FIELD_JSON.exists() else {}
    examples = read_json(DRAFT_EXAMPLE_JSON) if DRAFT_EXAMPLE_JSON.exists() else {}
    scan_result = read_json(SCAN_RESULT_JSON) if SCAN_RESULT_JSON.exists() else {}
    ledger = read_json(SIGNOFF_LEDGER_JSON) if SIGNOFF_LEDGER_JSON.exists() else {}

    for name, data in [
        ("生成包", package),
        ("冲突扫描规则", scan_rule),
        ("签收台账字段", signoff_fields),
        ("草案示例", examples),
        ("扫描结果", scan_result),
        ("签收台账", ledger),
    ]:
        require_flags(data, name, errors)

    if package.get("状态") != "three_business_rule_draft_conflict_signoff_ready":
        errors.append("生成包状态不正确")
    if set(scan_rule.get("冲突类型", [])) != REQUIRED_CONFLICT_TYPES:
        errors.append("冲突类型必须完整包含红线冲突、跨业务职责冲突、旧口径回潮、正式规则自动生效、缺少回滚办法、缺少总管确认")
    if set(scan_result.get("冲突类型", [])) != REQUIRED_CONFLICT_TYPES:
        errors.append("扫描结果冲突类型必须齐全")
    if scan_result.get("错误数") != 0:
        errors.append("扫描结果错误数必须为0")
    if ledger.get("错误数") != 0:
        errors.append("签收台账错误数必须为0")

    validate_rows(examples.get("草案", []), "草案示例", errors)
    validate_rows(scan_result.get("扫描明细", []), "扫描明细", errors)
    validate_rows(ledger.get("台账", []), "签收台账", errors)

    report = {
        "名称": "三业务正式规则申请草案冲突扫描与签收台账包验收",
        "验收时间": now_text(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "覆盖税收股票视频": {row.get("业务") for row in scan_result.get("扫描明细", [])} == REQUIRED_BUSINESSES,
            "冲突类型齐全": set(scan_rule.get("冲突类型", [])) == REQUIRED_CONFLICT_TYPES,
            "正式生效=false": scan_result.get("正式生效") is False and ledger.get("正式生效") is False,
            "写正式规则=false": scan_result.get("写正式规则") is False and ledger.get("写正式规则") is False,
            "需总管确认=true": scan_result.get("需总管确认") is True and ledger.get("需总管确认") is True,
            "扫描错误数=0": scan_result.get("错误数") == 0,
        },
        "文件": {
            "生成包": str(PACKAGE_JSON),
            "冲突扫描规则": str(SCAN_RULE_JSON),
            "签收台账字段": str(SIGNOFF_FIELD_JSON),
            "扫描结果": str(SCAN_RESULT_JSON),
            "签收台账": str(SIGNOFF_LEDGER_JSON),
            "验收日志": str(LOG_JSON),
        },
    }

    write_json(LOG_JSON, report)
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
