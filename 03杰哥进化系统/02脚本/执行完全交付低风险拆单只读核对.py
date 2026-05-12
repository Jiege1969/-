# -*- coding: utf-8 -*-
"""执行完全交付低风险拆单只读核对。

仅读取低风险拆单包并生成核对报告，不触发任何真实外部动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "68完全交付使用版低风险可推进拆单包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险可推进拆单包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险可推进拆单包_最新.json"
CHECK_JSON = DATA_DIR / "完全交付低风险拆单只读核对_最新.json"
CHECK_MD = DATA_DIR / "完全交付低风险拆单只读核对_最新.md"
CHECK_LOG = LOG_DIR / "执行完全交付低风险拆单只读核对_最新.json"

REQUIRED_ITEMS = {
    "文档交接增强",
    "长周期样本",
    "异常样例扩展",
    "只读核对覆盖",
    "视频环境识别候选",
    "不触发真实渲染的依赖检测计划",
    "税收/股票/视频用户反馈样本模板",
}
REQUIRED_FIELDS = ["目标", "输入", "输出", "验收", "预计工时", "是否触红线"]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def evaluate(package: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    items = package.get("拆单项", [])
    item_names = {item.get("拆单项") for item in items}

    for name in sorted(REQUIRED_ITEMS):
        results.append({"核对项": f"必备拆单项：{name}", "结果": "pass" if name in item_names else "fail"})

    for item in items:
        name = item.get("拆单项", "未知拆单项")
        missing = [field for field in REQUIRED_FIELDS if field not in item or item.get(field) in ("", None, [])]
        results.append(
            {
                "核对项": f"字段完整：{name}",
                "结果": "pass" if not missing else "fail",
                "缺失字段": missing,
            }
        )
        results.append(
            {
                "核对项": f"红线关闭：{name}",
                "结果": "pass" if item.get("是否触红线") is False else "fail",
                "是否触红线": item.get("是否触红线"),
            }
        )
        output_ok = isinstance(item.get("输出"), list) and len(item["输出"]) >= 1
        acceptance_ok = isinstance(item.get("验收"), list) and len(item["验收"]) >= 2
        results.append(
            {
                "核对项": f"输出与验收可用：{name}",
                "结果": "pass" if output_ok and acceptance_ok else "fail",
                "输出项数量": len(item.get("输出", [])) if isinstance(item.get("输出"), list) else 0,
                "验收项数量": len(item.get("验收", [])) if isinstance(item.get("验收"), list) else 0,
            }
        )

    boundary = package.get("安全边界", {})
    boundary_ok = bool(boundary) and all(value is True for value in boundary.values())
    results.append({"核对项": "安全边界均为禁止或不修改声明", "结果": "pass" if boundary_ok else "fail", "安全边界": boundary})
    nature_ok = "低风险" in package.get("性质", "") and "红线外" in package.get("性质", "")
    results.append({"核对项": "包性质为红线外低风险", "结果": "pass" if nature_ok else "fail", "性质": package.get("性质")})
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付低风险拆单只读核对",
        "",
        f"- 核对时间：{report['核对时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        "",
        "| 核对项 | 结果 |",
        "| --- | --- |",
    ]
    for item in report["核对结果"]:
        lines.append(f"| {item['核对项']} | {item['结果']} |")
    lines.extend(["", "## 结论", "", report["结论"]])
    return "\n".join(lines)


def main() -> int:
    package = read_json(PACKAGE_JSON)
    results = evaluate(package)
    error_count = sum(1 for item in results if item["结果"] != "pass")
    report = {
        "名称": "完全交付低风险拆单只读核对",
        "核对时间": now(),
        "总体状态": "pass" if error_count == 0 else "fail",
        "错误数": error_count,
        "error_count": error_count,
        "包路径": str(PACKAGE_JSON),
        "核对结果": results,
        "结论": "所有拆单均为红线外低风险可推进项。" if error_count == 0 else "存在未通过项，不能作为低风险拆单验收输入。",
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_markdown(report))
    write_json(CHECK_LOG, report)
    print(json.dumps({"总体状态": report["总体状态"], "错误数": error_count, "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
