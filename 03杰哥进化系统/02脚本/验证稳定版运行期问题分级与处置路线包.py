# -*- coding: utf-8 -*-
"""验证稳定版运行期问题分级与处置路线包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101稳定版运行期问题分级与处置路线包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版运行期问题分级与处置路线包验收"
PACKAGE_JSON = DATA_DIR / "稳定版运行期问题分级与处置路线包_最新.json"
ROUTE_MD = DATA_DIR / "运行期问题分级与处置路线_最新.md"
GATE_MATRIX_JSON = DATA_DIR / "总管确认闸口矩阵_最新.json"
QUEUE_TEMPLATE_JSON = DATA_DIR / "候选任务队列模板_最新.json"
LOG_JSON = LOG_DIR / "stable-runtime-issue-triage-route-verify-最新.json"


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    gate = read_json(GATE_MATRIX_JSON)
    queue = read_json(QUEUE_TEMPLATE_JSON)
    errors: list[str] = []

    if package.get("状态") != "stable_runtime_issue_triage_route_ready":
        errors.append("总包状态不正确")
    levels = package.get("问题分级", [])
    level_ids = {item.get("级别") for item in levels}
    if level_ids != {"P0", "P1", "P2", "P3"}:
        errors.append("问题分级必须覆盖 P0-P3")
    if gate.get("P0", {}).get("需总管确认") is not True or gate.get("P0", {}).get("允许自动执行") is not False:
        errors.append("P0 必须需总管确认且禁止自动执行")
    if gate.get("P1", {}).get("需总管确认") is not True or gate.get("P1", {}).get("允许自动执行") is not False:
        errors.append("P1 必须需总管确认且禁止自动执行")
    if len(package.get("问题域路线", [])) < 5:
        errors.append("问题域路线不足")
    if not isinstance(queue, list) or not queue:
        errors.append("候选任务队列模板缺失")
    if not ROUTE_MD.exists() or "问题分级" not in ROUTE_MD.read_text(encoding="utf-8"):
        errors.append("处置路线文档缺失或内容不完整")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版运行期问题分级与处置路线包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "问题分级数": len(levels),
            "问题域路线数": len(package.get("问题域路线", [])),
            "P0需总管确认": gate.get("P0", {}).get("需总管确认"),
            "P0允许自动执行": gate.get("P0", {}).get("允许自动执行"),
            "当前反馈需总管确认数": package.get("当前反馈摘要", {}).get("需总管确认数"),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "路线": str(ROUTE_MD), "闸口矩阵": str(GATE_MATRIX_JSON), "队列模板": str(QUEUE_TEMPLATE_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
