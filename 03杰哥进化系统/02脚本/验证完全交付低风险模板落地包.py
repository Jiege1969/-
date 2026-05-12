# -*- coding: utf-8 -*-
"""验证完全交付低风险模板落地包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付低风险模板落地包验收"

PACKAGE_JSON = DATA_DIR / "完全交付低风险模板落地包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付低风险模板落地包_最新.md"
CHECK_JSON = DATA_DIR / "完全交付低风险模板只读核对_最新.json"
CHECK_MD = DATA_DIR / "完全交付低风险模板只读核对_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付低风险模板落地包_最新.json"
CHECK_LOG = LOG_DIR / "执行完全交付低风险模板只读核对_最新.json"
VERIFY_JSON = LOG_DIR / "full-delivery-low-risk-template-landing-verify-最新.json"
VERIFY_MD = LOG_DIR / "full-delivery-low-risk-template-landing-verify-最新.md"

REQUIRED_TEMPLATE_NAMES = [
    "用户反馈样本模板",
    "视频环境识别候选模板",
    "只读核对扩展模板",
    "异常样例扩展模板",
    "文档交接增强模板",
    "长周期样本记录模板",
]
REQUIRED_FIELDS = ["模板名称", "输入", "输出", "验收", "红线"]
TEMPLATE_JSON_FILES = {name: DATA_DIR / f"{name}_最新.json" for name in REQUIRED_TEMPLATE_NAMES}
TEMPLATE_MD_FILES = {name: DATA_DIR / f"{name}_最新.md" for name in REQUIRED_TEMPLATE_NAMES}
FORBIDDEN_OPEN_MARKERS = [
    "红线=true",
    '"红线": true',
    '"red_line": true',
    "允许真实发送企业微信",
    "执行真实发送企业微信",
    "允许触发n8n",
    "执行触发n8n",
    "允许连接券商",
    "允许交易",
    "执行交易",
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


def pass_fail(ok: bool) -> str:
    return "pass" if ok else "fail"


def check_file(path: Path) -> dict[str, Any]:
    return {"检查项": f"文件存在：{path.name}", "结果": pass_fail(path.exists()), "路径": str(path)}


def validate_template(name: str, path: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if not path.exists():
        results.append(check_file(path))
        return results

    template = read_json(path)
    missing = [field for field in REQUIRED_FIELDS if field not in template or template.get(field) in ("", None, [])]
    results.append({"检查项": f"字段完整：{name}", "结果": pass_fail(not missing), "缺失字段": missing})
    results.append(
        {
            "检查项": f"红线=false：{name}",
            "结果": pass_fail(template.get("红线") is False and template.get("red_line") is False),
            "红线": template.get("红线"),
            "red_line": template.get("red_line"),
        }
    )
    for field in ["输入", "输出", "验收"]:
        value = template.get(field)
        results.append(
            {
                "检查项": f"{field}说明存在：{name}",
                "结果": pass_fail(isinstance(value, list) and len(value) > 0),
                "数量": len(value) if isinstance(value, list) else 0,
            }
        )
    text = json.dumps(template, ensure_ascii=False)
    markers = [marker for marker in FORBIDDEN_OPEN_MARKERS if marker in text]
    results.append({"检查项": f"红线未开放措辞：{name}", "结果": pass_fail(not markers), "命中": markers})
    return results


def validate_package() -> list[dict[str, Any]]:
    results = [check_file(PACKAGE_JSON), check_file(PACKAGE_MD), check_file(CHECK_JSON), check_file(CHECK_MD), check_file(GEN_LOG), check_file(CHECK_LOG)]
    for path in TEMPLATE_JSON_FILES.values():
        results.append(check_file(path))
    for path in TEMPLATE_MD_FILES.values():
        results.append(check_file(path))

    if PACKAGE_JSON.exists():
        package = read_json(PACKAGE_JSON)
        names = [item.get("模板名称") for item in package.get("模板清单", [])]
        results.append({"检查项": "包内模板数量为6", "结果": pass_fail(package.get("模板数量") == 6 and len(names) == 6), "模板数量": package.get("模板数量")})
        for name in REQUIRED_TEMPLATE_NAMES:
            results.append({"检查项": f"包内包含模板：{name}", "结果": pass_fail(name in names)})
        results.append({"检查项": "包验收口径红线=false", "结果": pass_fail(package.get("验收口径", {}).get("红线") is False)})

    for name, path in TEMPLATE_JSON_FILES.items():
        results.extend(validate_template(name, path))

    if CHECK_JSON.exists():
        check = read_json(CHECK_JSON)
        results.append(
            {
                "检查项": "只读核对通过且错误数0",
                "结果": pass_fail(check.get("总体状态") == "pass" and check.get("错误数") == 0 and check.get("error_count") == 0),
                "只读核对状态": check.get("总体状态"),
                "只读核对错误数": check.get("错误数"),
            }
        )
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付低风险模板落地包验证",
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
    lines.extend(["", "## 结论", "", report["验证结论"]])
    return "\n".join(lines)


def main() -> int:
    results = validate_package()
    error_count = sum(1 for item in results if item["结果"] != "pass")
    report = {
        "名称": "完全交付低风险模板落地包验证",
        "验证时间": now(),
        "总体状态": "pass" if error_count == 0 else "fail",
        "错误数": error_count,
        "error_count": error_count,
        "检查结果": results,
        "验证结论": "错误数0，完全交付低风险模板落地包验收通过。" if error_count == 0 else "存在错误项，需修正后重新验证。",
    }
    write_json(VERIFY_JSON, report)
    write_text(VERIFY_MD, build_markdown(report))
    print(json.dumps({"总体状态": report["总体状态"], "错误数": error_count, "输出": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
