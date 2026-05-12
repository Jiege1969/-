# -*- coding: utf-8 -*-
"""验证稳定版运行期问题候选队列分流预演包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "102稳定版运行期问题候选队列分流预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定版运行期问题候选队列分流预演包验收"
PACKAGE_JSON = DATA_DIR / "稳定版运行期问题候选队列分流预演包_最新.json"
SAMPLES_JSON = DATA_DIR / "运行期问题分流样例_最新.json"
QUEUE_PREVIEW_JSON = DATA_DIR / "运行期问题候选队列预演_最新.json"
QUEUE_PREVIEW_MD = DATA_DIR / "运行期问题候选队列预演_最新.md"
LOG_JSON = LOG_DIR / "stable-runtime-issue-candidate-queue-preview-verify-最新.json"


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    package = read_json(PACKAGE_JSON)
    samples = read_json(SAMPLES_JSON)
    preview = read_json(QUEUE_PREVIEW_JSON)
    errors: list[str] = []

    if package.get("状态") != "stable_runtime_issue_candidate_queue_preview_ready":
        errors.append("总包状态不正确")
    if not isinstance(samples, list) or len(samples) < 5:
        errors.append("分流样例不足")
    if preview.get("总体状态") != "pass":
        errors.append("候选队列预演未通过")
    if preview.get("汇总", {}).get("失败") != 0:
        errors.append("候选队列预演存在失败样例")
    queue = preview.get("候选队列", [])
    p0 = [item for item in queue if item.get("级别") == "P0"]
    p1 = [item for item in queue if item.get("级别") == "P1"]
    low = [item for item in queue if item.get("级别") in {"P2", "P3"}]
    if not p0 or not all(item.get("需总管确认") is True and item.get("允许自动执行") is False for item in p0):
        errors.append("P0 样例必须需总管确认且禁止自动执行")
    if not p1 or not all(item.get("需总管确认") is True and item.get("允许自动执行") is False for item in p1):
        errors.append("P1 样例必须需总管确认且禁止自动执行")
    if len(low) < 3 or not all(item.get("需总管确认") is False and item.get("允许自动执行") is True for item in low):
        errors.append("P2/P3 样例必须允许低风险候选执行")
    if not QUEUE_PREVIEW_MD.exists() or "运行期问题候选队列预演" not in QUEUE_PREVIEW_MD.read_text(encoding="utf-8"):
        errors.append("预演 Markdown 缺失或内容不完整")
    if not all(value is False for value in package.get("安全边界", {}).values()):
        errors.append("总包安全边界必须全部为 false")
    if not all(value is False for value in preview.get("安全边界", {}).values()):
        errors.append("预演安全边界必须全部为 false")
    for path_text in package.get("输出文件", {}).values():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{path_text}")

    report = {
        "名称": "稳定版运行期问题候选队列分流预演包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "样例数": len(samples) if isinstance(samples, list) else 0,
            "预演通过": preview.get("汇总", {}).get("通过"),
            "预演失败": preview.get("汇总", {}).get("失败"),
            "P0样例数": len(p0),
            "P1样例数": len(p1),
            "低风险样例数": len(low),
        },
        "验证范围": {"总包": str(PACKAGE_JSON), "样例": str(SAMPLES_JSON), "预演": str(QUEUE_PREVIEW_JSON), "日志": str(LOG_JSON)},
    }
    write_json(LOG_JSON, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
