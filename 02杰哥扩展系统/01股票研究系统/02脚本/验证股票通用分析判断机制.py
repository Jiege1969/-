# -*- coding: utf-8 -*-
"""
验证股票通用分析判断机制是否已经形成可执行的系统级上位规则。

只做本地文件读取和验收产物输出，不触发企业微信、n8n、券商接口或交易链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "01配置"
DOC_DIR = ROOT / "07文档"
OUT_DIR = ROOT / "03数据" / "281股票通用分析判断机制验收"

MECHANISM_PATH = CONFIG_DIR / "股票通用分析判断机制_v1.0.json"
WORKFLOW_PATH = CONFIG_DIR / "股票分析报告工作流_v1.0.json"
JIEGE_RULE_PATH = CONFIG_DIR / "杰哥推荐分析方法v1规则.json"
JIEGE_WORKFLOW_PATH = CONFIG_DIR / "杰哥推荐方法工作流规则_v1.0.json"
MECHANISM_DOC_PATH = DOC_DIR / "股票通用分析判断机制_v1.0.md"


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_contains(name: str, content: str, keywords: list[str], errors: list[str], warnings: list[str]) -> None:
    missing = [word for word in keywords if word not in content]
    if missing:
        errors.append(f"{name} 缺少关键词: {', '.join(missing)}")
    elif len(content) < 200:
        warnings.append(f"{name} 内容过短，可能只是占位。")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    errors: list[str] = []
    warnings: list[str] = []

    required_files = [
        MECHANISM_PATH,
        WORKFLOW_PATH,
        JIEGE_RULE_PATH,
        JIEGE_WORKFLOW_PATH,
        MECHANISM_DOC_PATH,
    ]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少文件: {path}")

    mechanism = read_json(MECHANISM_PATH) if MECHANISM_PATH.exists() else {}
    workflow_text = read_text(WORKFLOW_PATH) if WORKFLOW_PATH.exists() else ""
    jiege_rule_text = read_text(JIEGE_RULE_PATH) if JIEGE_RULE_PATH.exists() else ""
    jiege_workflow_text = read_text(JIEGE_WORKFLOW_PATH) if JIEGE_WORKFLOW_PATH.exists() else ""
    mechanism_doc_text = read_text(MECHANISM_DOC_PATH) if MECHANISM_DOC_PATH.exists() else ""

    required_sections = [
        "总原则",
        "分析法阶",
        "通用分析顺序",
        "市场环境主次切换",
        "指标角色库",
        "输出字段要求",
        "前台投影规则",
        "长期学习机制",
        "安全边界",
    ]
    for section in required_sections:
        if section not in mechanism:
            errors.append(f"通用机制配置缺少章节: {section}")

    expected_law_levels = ["宪法层", "法律层", "规章层", "案例层"]
    actual_law_levels = [item.get("层级") for item in mechanism.get("分析法阶", [])]
    for level in expected_law_levels:
        if level not in actual_law_levels:
            errors.append(f"分析法阶缺少: {level}")

    environments = [item.get("市场环境") for item in mechanism.get("市场环境主次切换", [])]
    for expected in ["强势市/牛市", "震荡市/中性市", "弱势市/熊市", "事件驱动", "长期研究"]:
        if expected not in environments:
            errors.append(f"市场环境主次切换缺少: {expected}")

    roles = [item.get("指标组") for item in mechanism.get("指标角色库", [])]
    for expected in ["趋势与均线", "量能与换手", "行业与市场宽度", "失败对照", "基本面与财务", "估值", "事件与政策"]:
        if expected not in roles:
            errors.append(f"指标角色库缺少: {expected}")

    safety = mechanism.get("安全边界", {})
    for key in ["真实发送企业微信", "触发n8n", "调用券商接口", "自动交易", "输出交易指令"]:
        if safety.get(key) is not False:
            errors.append(f"安全边界异常: {key} 必须为 false")

    check_contains(
        "股票分析报告工作流",
        workflow_text,
        ["股票通用分析判断机制_v1.0.json", "主指标", "辅助指标", "证据法阶"],
        errors,
        warnings,
    )
    check_contains(
        "杰哥推荐分析方法v1规则",
        jiege_rule_text,
        ["上位规则", "股票通用分析判断机制_v1.0.json"],
        errors,
        warnings,
    )
    check_contains(
        "杰哥推荐方法工作流规则",
        jiege_workflow_text,
        ["股票通用分析判断机制_v1.0.json", "通用分析判断机制"],
        errors,
        warnings,
    )
    check_contains(
        "通用机制文档",
        mechanism_doc_text,
        ["证据法阶", "市场环境改变指标主次", "指标角色", "学习机制"],
        errors,
        warnings,
    )

    report = {
        "名称": "股票通用分析判断机制验收",
        "生成时间": now,
        "结论": "通过" if not errors else "不通过",
        "检查文件": [str(path) for path in required_files],
        "错误": errors,
        "警告": warnings,
        "机制摘要": {
            "分析法阶": actual_law_levels,
            "市场环境数量": len(environments),
            "指标角色数量": len(roles),
            "输出字段数量": len(mechanism.get("输出字段要求", [])),
            "适用范围": mechanism.get("适用范围", []),
        },
        "安全边界": safety,
    }

    latest_json = OUT_DIR / "股票通用分析判断机制验收_最新.json"
    stamped_json = OUT_DIR / f"股票通用分析判断机制验收_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    latest_md = OUT_DIR / "股票通用分析判断机制验收_最新.md"

    latest_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    stamped_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# 股票通用分析判断机制验收",
        "",
        f"生成时间：{now}",
        f"结论：{report['结论']}",
        "",
        "## 机制摘要",
        "",
        f"- 分析法阶：{', '.join(actual_law_levels)}",
        f"- 市场环境数量：{len(environments)}",
        f"- 指标角色数量：{len(roles)}",
        f"- 输出字段数量：{len(mechanism.get('输出字段要求', []))}",
        "",
        "## 错误",
        "",
    ]
    md_lines.extend([f"- {item}" for item in errors] or ["- 无"])
    md_lines.extend(["", "## 警告", ""])
    md_lines.extend([f"- {item}" for item in warnings] or ["- 无"])
    md_lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        md_lines.append(f"- {key}: {value}")

    latest_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(json.dumps({"结论": report["结论"], "错误数": len(errors), "警告数": len(warnings), "输出": str(latest_json)}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
