# -*- coding: utf-8 -*-
"""执行完全交付低风险模板只读核对。

只读取 72 包模板文件，确认文件存在、字段完整、红线未开放。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付低风险模板落地包验收"

PACKAGE_JSON = DATA_DIR / "完全交付低风险模板落地包_最新.json"
CHECK_JSON = DATA_DIR / "完全交付低风险模板只读核对_最新.json"
CHECK_MD = DATA_DIR / "完全交付低风险模板只读核对_最新.md"
CHECK_LOG = LOG_DIR / "执行完全交付低风险模板只读核对_最新.json"

REQUIRED_TEMPLATE_NAMES = [
    "用户反馈样本模板",
    "视频环境识别候选模板",
    "只读核对扩展模板",
    "异常样例扩展模板",
    "文档交接增强模板",
    "长周期样本记录模板",
]
REQUIRED_FIELDS = ["模板名称", "输入", "输出", "验收", "红线"]
TEMPLATE_FILES = {name: DATA_DIR / f"{name}_最新.json" for name in REQUIRED_TEMPLATE_NAMES}


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


def pass_fail(ok: bool) -> str:
    return "pass" if ok else "fail"


def check_template(name: str, path: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = [
        {"核对项": f"模板文件存在：{name}", "结果": pass_fail(path.exists()), "路径": str(path)}
    ]
    if not path.exists():
        return results

    try:
        template = read_json(path)
    except Exception as exc:  # noqa: BLE001
        results.append({"核对项": f"模板JSON可解析：{name}", "结果": "fail", "错误": repr(exc)})
        return results

    results.append({"核对项": f"模板JSON可解析：{name}", "结果": "pass"})
    missing = [field for field in REQUIRED_FIELDS if field not in template or template.get(field) in ("", None, [])]
    results.append({"核对项": f"字段完整：{name}", "结果": pass_fail(not missing), "缺失字段": missing})
    results.append(
        {
            "核对项": f"模板名称一致：{name}",
            "结果": pass_fail(template.get("模板名称") == name),
            "实际名称": template.get("模板名称"),
        }
    )
    results.append(
        {
            "核对项": f"红线未开放：{name}",
            "结果": pass_fail(template.get("红线") is False and template.get("red_line") is False),
            "红线": template.get("红线"),
            "red_line": template.get("red_line"),
        }
    )
    for field in ["输入", "输出", "验收"]:
        value = template.get(field)
        results.append(
            {
                "核对项": f"{field}非空列表：{name}",
                "结果": pass_fail(isinstance(value, list) and len(value) > 0),
                "数量": len(value) if isinstance(value, list) else 0,
            }
        )
    return results


def check_package() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = [
        {"核对项": "索引包存在", "结果": pass_fail(PACKAGE_JSON.exists()), "路径": str(PACKAGE_JSON)}
    ]
    if not PACKAGE_JSON.exists():
        return results

    package = read_json(PACKAGE_JSON)
    names = [item.get("模板名称") for item in package.get("模板清单", [])]
    results.append(
        {
            "核对项": "索引包模板数量为6",
            "结果": pass_fail(package.get("模板数量") == 6 and len(names) == 6),
            "模板数量": package.get("模板数量"),
            "清单数量": len(names),
        }
    )
    for name in REQUIRED_TEMPLATE_NAMES:
        results.append({"核对项": f"索引包含模板：{name}", "结果": pass_fail(name in names)})
    results.append(
        {
            "核对项": "索引包验收口径红线=false",
            "结果": pass_fail(package.get("验收口径", {}).get("红线") is False),
            "红线": package.get("验收口径", {}).get("红线"),
        }
    )
    boundary = package.get("安全边界", {})
    results.append(
        {
            "核对项": "安全边界均保持禁止或不修改",
            "结果": pass_fail(bool(boundary) and all(value is True for value in boundary.values())),
            "安全边界数量": len(boundary) if isinstance(boundary, dict) else 0,
        }
    )
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付低风险模板只读核对",
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
    results = check_package()
    for name, path in TEMPLATE_FILES.items():
        results.extend(check_template(name, path))

    error_count = sum(1 for item in results if item["结果"] != "pass")
    report = {
        "名称": "完全交付低风险模板只读核对",
        "核对时间": now(),
        "总体状态": "pass" if error_count == 0 else "fail",
        "错误数": error_count,
        "error_count": error_count,
        "核对结果": results,
        "结论": "模板文件存在、字段完整、红线未开放。" if error_count == 0 else "存在未通过项，不能进入验收通过状态。",
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_markdown(report))
    write_json(CHECK_LOG, report)
    print(json.dumps({"总体状态": report["总体状态"], "错误数": error_count, "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
