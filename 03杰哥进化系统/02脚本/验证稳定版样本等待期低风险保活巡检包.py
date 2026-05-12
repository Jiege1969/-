# -*- coding: utf-8 -*-
"""验证稳定版样本等待期低风险保活巡检包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "100稳定版样本等待期低风险保活巡检包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版样本等待期低风险保活巡检包验收"
PACKAGE_JSON = DATA_DIR / "稳定版样本等待期低风险保活巡检包_最新.json"
RUN_RESULT_JSON = DATA_DIR / "稳定版样本等待期低风险保活巡检执行结果_最新.json"
KEEPALIVE_CARD_MD = DATA_DIR / "样本等待期低风险保活巡检卡_最新.md"
LOG_JSON = LOG_DIR / "stable-sample-waiting-keepalive-patrol-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    result = read_json(RUN_RESULT_JSON)
    errors: list[str] = []

    if package.get("状态") != "stable_sample_waiting_keepalive_patrol_ready":
        errors.append("总包状态不正确")
    if len(package.get("巡检内容", [])) < 5:
        errors.append("巡检内容不足")
    if result.get("总体状态") != "pass":
        errors.append("执行结果未通过")
    if result.get("汇总", {}).get("失败") != 0:
        errors.append("执行结果存在失败任务")
    if result.get("汇总", {}).get("通过", 0) < 5:
        errors.append("执行任务通过数不足")
    if result.get("等待期摘要", {}).get("自主巡检状态") != "pass":
        errors.append("自主巡检快照未通过")
    if not KEEPALIVE_CARD_MD.exists() or "不新增三日自然日样本" not in KEEPALIVE_CARD_MD.read_text(encoding="utf-8"):
        errors.append("保活巡检卡缺失或内容不完整")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部为 false")
    if not all(value is False for value in result.get("安全边界", {}).values()):
        errors.append("执行结果安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版样本等待期低风险保活巡检包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "执行任务数": result.get("汇总", {}).get("总数"),
            "执行通过": result.get("汇总", {}).get("通过"),
            "执行失败": result.get("汇总", {}).get("失败"),
            "今天是否允许新增自然日样本": result.get("等待期摘要", {}).get("今天是否允许新增自然日样本"),
            "仍缺自然日样本数": result.get("等待期摘要", {}).get("仍缺自然日样本数"),
            "反馈需总管确认数": result.get("等待期摘要", {}).get("反馈需总管确认数"),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "执行结果": str(RUN_RESULT_JSON), "保活巡检卡": str(KEEPALIVE_CARD_MD), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
