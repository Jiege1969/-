# -*- coding: utf-8 -*-
"""验证自主运行暂停闸口与人工接管演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION = Path(__file__).resolve().parents[1]
DATA = EVOLUTION / "03数据" / "77自主运行暂停闸口与人工接管演练包"
LOG = EVOLUTION / "04日志" / "自主运行暂停闸口与人工接管演练包验收"

PACKAGE_JSON = DATA / "自主运行暂停闸口与人工接管演练包_最新.json"
PACKAGE_MD = DATA / "自主运行暂停闸口与人工接管演练包_最新.md"
DRILL_JSON = DATA / "暂停闸口演练样例_最新.json"
DRILL_MD = DATA / "暂停闸口演练样例_最新.md"
HANDOFF_MD = DATA / "人工接管清单_最新.md"
VERIFY_JSON = LOG / "autonomous-pause-handoff-drill-verify-最新.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    for path in [PACKAGE_JSON, PACKAGE_MD, DRILL_JSON, DRILL_MD, HANDOFF_MD]:
        if not path.exists():
            errors.append(f"缺少文件：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    cases = package.get("演练样例", [])
    if package.get("状态") != "autonomous_pause_handoff_drill_ready":
        errors.append("状态不正确")
    if len(cases) < 9:
        errors.append("演练样例不足9条")
    if not any(item.get("需总管确认") is False and "低风险" in item.get("判断", "") for item in cases):
        errors.append("缺少低风险可自主推进样例")
    if sum(1 for item in cases if item.get("需总管确认") is True) < 8:
        errors.append("需总管确认样例不足8条")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    forbidden = ["允许真实发送", "允许真实触发", "允许交易", "允许登录电子税务局", "允许真实渲染", "允许自动发布", "允许自动转正式规则"]
    text = json.dumps(package, ensure_ascii=False)
    hits = [word for word in forbidden if word in text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")

    report = {
        "名称": "自主运行暂停闸口与人工接管演练包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "演练样例数": len(cases),
            "需总管确认样例数": sum(1 for item in cases if item.get("需总管确认") is True),
            "低风险可自主推进样例数": sum(1 for item in cases if item.get("需总管确认") is False),
            "错误数": len(errors),
        },
    }
    LOG.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
