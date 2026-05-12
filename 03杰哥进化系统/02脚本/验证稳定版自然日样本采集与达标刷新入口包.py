# -*- coding: utf-8 -*-
"""验证稳定版自然日样本采集与达标刷新入口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "97稳定版自然日样本采集与达标刷新入口包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版自然日样本采集与达标刷新入口包验收"
PACKAGE_JSON = DATA_DIR / "稳定版自然日样本采集与达标刷新入口包_最新.json"
RUN_RESULT_JSON = DATA_DIR / "稳定版自然日样本采集与达标刷新执行结果_最新.json"
LOG_JSON = LOG_DIR / "stable-natural-day-sample-refresh-entry-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    run_result = read_json(RUN_RESULT_JSON)
    errors: list[str] = []

    if package.get("状态") != "stable_natural_day_sample_refresh_entry_ready":
        errors.append("入口包状态不正确")
    if len(package.get("执行链路", [])) < 6:
        errors.append("执行链路不足")
    if run_result.get("总体状态") != "pass":
        errors.append("执行结果未通过")
    if run_result.get("汇总", {}).get("失败") != 0:
        errors.append("执行结果存在失败任务")
    if run_result.get("汇总", {}).get("通过", 0) < 7:
        errors.append("执行任务通过数不足")
    if run_result.get("运行摘要", {}).get("是否生成未来样本") is not False:
        errors.append("不得生成未来自然日样本")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("入口包安全边界必须全部为 false")
    if not all(value is False for value in run_result.get("安全边界", {}).values()):
        errors.append("执行结果安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版自然日样本采集与达标刷新入口包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "执行任务数": run_result.get("汇总", {}).get("总数"),
            "执行通过": run_result.get("汇总", {}).get("通过"),
            "执行失败": run_result.get("汇总", {}).get("失败"),
            "三日达标": run_result.get("运行摘要", {}).get("三日达标"),
            "仍缺自然日样本数": run_result.get("运行摘要", {}).get("仍缺自然日样本数"),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "执行结果": str(RUN_RESULT_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
