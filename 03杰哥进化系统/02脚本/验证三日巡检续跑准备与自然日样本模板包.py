# -*- coding: utf-8 -*-
"""验证三日巡检续跑准备与自然日样本模板包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
PACKAGE_DIR = ROOT / "03数据" / "65三日巡检续跑准备与自然日样本模板包"
PACKAGE_JSON = PACKAGE_DIR / "三日巡检续跑准备与自然日样本模板包_最新.json"
READONLY_CHECK_JSON = PACKAGE_DIR / "只读核对结果_最新.json"
LOG_DIR = ROOT / "04日志" / "三日巡检续跑准备与自然日样本模板包验收"
LATEST_LOG = LOG_DIR / "three-day-patrol-rerun-template-verify-最新.json"


REQUIRED_OUTPUTS = [
    "总包JSON",
    "总包Markdown",
    "第2自然日手动巡检执行模板",
    "第3自然日手动巡检执行模板",
    "自然日计数规则",
    "样本文件命名建议",
    "失败分级处理说明",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    readonly = read_json(READONLY_CHECK_JSON) if READONLY_CHECK_JSON.exists() else {}

    if not PACKAGE_JSON.exists():
        errors.append(f"总包 JSON 不存在：{PACKAGE_JSON}")
    if not READONLY_CHECK_JSON.exists():
        errors.append(f"只读核对结果不存在：{READONLY_CHECK_JSON}")

    if package.get("状态") != "three_day_patrol_rerun_template_ready":
        errors.append("状态必须为 three_day_patrol_rerun_template_ready")
    if package.get("允许作为三日达标") is not False:
        errors.append("模板包不得允许作为三日达标")

    source_confirm = package.get("59包首日样本确认", {})
    if source_confirm.get("已记录自然日数") != 1:
        errors.append("必须确认 59 包当前只有 1 个自然日")
    if source_confirm.get("三日达标") is not False:
        errors.append("必须确认 59 包当前三日达标=false")
    if source_confirm.get("确认结论") is not True:
        errors.append("59 包首日样本确认结论必须为 true")

    for key in REQUIRED_OUTPUTS:
        path_text = package.get("输出文件", {}).get(key)
        if not path_text:
            errors.append(f"缺少输出文件登记：{key}")
            continue
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{key} {path_text}")

    if len(package.get("自然日计数规则", [])) < 5:
        errors.append("自然日计数规则不得少于 5 条")
    if len(package.get("手动执行检查项", [])) < 5:
        errors.append("手动执行检查项不得少于 5 条")
    if len(package.get("失败分级处理", [])) < 3:
        errors.append("失败分级处理不得少于 3 级")

    no_fake = package.get("未生成样本声明", {})
    if "未生成" not in str(no_fake.get("第2自然日样本", "")):
        errors.append("必须声明未生成第2自然日样本")
    if "未生成" not in str(no_fake.get("第3自然日样本", "")):
        errors.append("必须声明未生成第3自然日样本")

    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    if readonly.get("通过") is not True:
        errors.append("只读核对结果必须通过")
    readonly_summary = readonly.get("59包台账摘要", {})
    if readonly_summary.get("自然日数") != 1:
        errors.append("只读核对必须确认当前只有 1 个自然日")
    if readonly_summary.get("三日达标") is not False:
        errors.append("只读核对必须确认三日达标=false")

    report = {
        "名称": "三日巡检续跑准备与自然日样本模板包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "输出文件数": len(package.get("输出文件", {})),
            "自然日计数规则数": len(package.get("自然日计数规则", [])),
            "手动执行检查项数": len(package.get("手动执行检查项", [])),
            "失败分级数": len(package.get("失败分级处理", [])),
            "当前已记录自然日数": source_confirm.get("已记录自然日数"),
            "当前三日达标": source_confirm.get("三日达标"),
            "只读核对通过": readonly.get("通过"),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
