# -*- coding: utf-8 -*-
"""验证稳定版次日自然日样本待办与防重复闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "99稳定版次日自然日样本待办与防重复闸口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版次日自然日样本待办与防重复闸口包验收"
PACKAGE_JSON = DATA_DIR / "稳定版次日自然日样本待办与防重复闸口包_最新.json"
TODO_MD = DATA_DIR / "次日自然日样本待办卡_最新.md"
GATE_JSON = DATA_DIR / "自然日样本防重复闸口_最新.json"
LOG_JSON = LOG_DIR / "stable-nextday-natural-sample-todo-duplicate-gate-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    gate = read_json(GATE_JSON)
    errors: list[str] = []

    if package.get("状态") != "stable_nextday_natural_sample_todo_duplicate_gate_ready":
        errors.append("总包状态不正确")
    if not gate.get("下一最早采集日期"):
        errors.append("下一最早采集日期不能为空")
    if gate.get("是否生成未来样本") is not False:
        errors.append("不得生成未来自然日样本")
    if gate.get("重复样本日期"):
        errors.append("样本台账存在重复自然日")
    if package.get("三日达标") is False and package.get("仍缺自然日样本数", 0) <= 0:
        errors.append("未达标时仍缺自然日样本数必须大于0")
    if not TODO_MD.exists() or "到点后只跑这个" not in TODO_MD.read_text(encoding="utf-8"):
        errors.append("次日待办卡缺失或内容不完整")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版次日自然日样本待办与防重复闸口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "已有通过自然日样本数": package.get("已有通过自然日样本数"),
            "仍缺自然日样本数": package.get("仍缺自然日样本数"),
            "三日达标": package.get("三日达标"),
            "今天是否允许新增自然日样本": gate.get("今天是否允许新增自然日样本"),
            "重复样本日期数": len(gate.get("重复样本日期", [])),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "待办卡": str(TODO_MD), "防重复闸口": str(GATE_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
