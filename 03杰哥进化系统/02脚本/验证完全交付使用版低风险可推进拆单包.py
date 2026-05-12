# -*- coding: utf-8 -*-
"""验证完全交付使用版低风险可推进拆单包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "68完全交付使用版低风险可推进拆单包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险可推进拆单包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险可推进拆单包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险可推进拆单包_最新.md"
PACKAGE_CSV = DATA_DIR / "完全交付使用版低风险可推进拆单清单_最新.csv"
CHECK_JSON = DATA_DIR / "完全交付低风险拆单只读核对_最新.json"
CHECK_MD = DATA_DIR / "完全交付低风险拆单只读核对_最新.md"
VERIFY_JSON = LOG_DIR / "full-delivery-low-risk-breakdown-verify-最新.json"
VERIFY_MD = LOG_DIR / "full-delivery-low-risk-breakdown-verify-最新.md"

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
FORBIDDEN_INTENT_MARKERS = [
    "允许真实发送",
    "执行真实发送",
    "允许触发n8n",
    "执行触发n8n",
    "允许连接券商",
    "执行连接券商",
    "允许登录税局",
    "执行登录税局",
    "允许真实渲染",
    "执行真实渲染",
    "允许发布视频",
    "执行发布视频",
    "允许转正式规则",
    "执行转正式规则",
]


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


def check_file(path: Path) -> dict[str, Any]:
    return {"检查项": f"文件存在：{path.name}", "结果": "pass" if path.exists() else "fail", "路径": str(path)}


def validate_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    items = package.get("拆单项", [])
    item_names = {item.get("拆单项") for item in items}

    results.append({"检查项": "拆单项数量为7", "结果": "pass" if len(items) == 7 else "fail", "实际数量": len(items)})
    for name in sorted(REQUIRED_ITEMS):
        results.append({"检查项": f"包含拆单项：{name}", "结果": "pass" if name in item_names else "fail"})

    for item in items:
        name = item.get("拆单项", "未知拆单项")
        missing = [field for field in REQUIRED_FIELDS if field not in item or item.get(field) in ("", None, [])]
        results.append({"检查项": f"字段完整：{name}", "结果": "pass" if not missing else "fail", "缺失字段": missing})
        results.append(
            {
                "检查项": f"是否触红线=false：{name}",
                "结果": "pass" if item.get("是否触红线") is False else "fail",
                "是否触红线": item.get("是否触红线"),
            }
        )
        text = json.dumps(item, ensure_ascii=False)
        unsafe_intent = any(marker in text for marker in FORBIDDEN_INTENT_MARKERS)
        results.append({"检查项": f"无真实动作推进意图：{name}", "结果": "pass" if not unsafe_intent else "fail"})

    boundary = package.get("安全边界", {})
    boundary_ok = bool(boundary) and all(value is True for value in boundary.values())
    results.append({"检查项": "安全边界声明完整关闭", "结果": "pass" if boundary_ok else "fail", "安全边界": boundary})
    acceptance = package.get("验收口径", {})
    results.append(
        {
            "检查项": "验收口径要求是否触红线=false",
            "结果": "pass" if acceptance.get("是否触红线") is False else "fail",
            "验收口径": acceptance,
        }
    )
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付使用版低风险可推进拆单包验证",
        "",
        f"- 验证时间：{report['验证时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        "",
        "| 检查项 | 结果 |",
        "| --- | --- |",
    ]
    for item in report["检查结果"]:
        lines.append(f"| {item['检查项']} | {item['结果']} |")
    lines.extend(["", "## 验证结论", "", report["验证结论"]])
    return "\n".join(lines)


def main() -> int:
    results = [check_file(path) for path in [PACKAGE_JSON, PACKAGE_MD, PACKAGE_CSV, CHECK_JSON, CHECK_MD]]
    if PACKAGE_JSON.exists():
        results.extend(validate_package(read_json(PACKAGE_JSON)))
    if CHECK_JSON.exists():
        check = read_json(CHECK_JSON)
        results.append(
            {
                "检查项": "只读核对通过且错误数0",
                "结果": "pass" if check.get("总体状态") == "pass" and check.get("错误数") == 0 else "fail",
                "只读核对状态": check.get("总体状态"),
                "只读核对错误数": check.get("错误数"),
            }
        )

    error_count = sum(1 for item in results if item["结果"] != "pass")
    report = {
        "名称": "完全交付使用版低风险可推进拆单包验证",
        "验证时间": now(),
        "总体状态": "pass" if error_count == 0 else "fail",
        "错误数": error_count,
        "error_count": error_count,
        "检查结果": results,
        "验证结论": "错误数 0，低风险可推进拆单包验收通过。" if error_count == 0 else "存在错误项，需修正后重新验证。",
    }
    write_json(VERIFY_JSON, report)
    write_text(VERIFY_MD, build_markdown(report))
    print(json.dumps({"总体状态": report["总体状态"], "错误数": error_count, "输出": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
