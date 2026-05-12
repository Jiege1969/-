# -*- coding: utf-8 -*-
"""
名称：验证股票报告质检与宪法级原则落实.py
作用：验证股票报告质检旁路方案和系统宪法级原则是否已纳入当前施工体系。
安全边界：只读验证；不触发n8n、不调用模型、不发送企业微信、不改正式业务库。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
INTELLIGENCE = ROOT / "01杰哥智能系统"
EVOLUTION = ROOT / "03杰哥进化系统"

CONSTITUTION_DOC = MANAGER / "07文档" / "设计纲领" / "系统宪法级原则与落地检查清单_20260503.md"
CONSTITUTION_RULE = MANAGER / "01配置" / "系统宪法级原则落地规则.json"
REPORT_REVIEW_DOC = INTELLIGENCE / "07文档" / "股票报告文稿质检融入方案_20260503.md"
REPORT_REVIEW_RULE = INTELLIGENCE / "01配置" / "股票报告质检融入规则.json"
TEXT_REVIEWER = INTELLIGENCE / "02脚本" / "文稿质检" / "text_reviewer.py"
REVIEW_RECORDS_DIR = INTELLIGENCE / "03数据" / "文稿质检"
GENERAL_METHOD = EVOLUTION / "03数据" / "04通用方法" / "报告质检_内容结构语言排版把关方法_20260503.md"
FUSION_PANEL = MANAGER / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def has_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def main() -> int:
    constitution_text = read_text(CONSTITUTION_DOC)
    review_text = read_text(REPORT_REVIEW_DOC)
    method_text = read_text(GENERAL_METHOD)
    constitution_rule = load_json(CONSTITUTION_RULE)
    review_rule = load_json(REPORT_REVIEW_RULE)
    fusion = load_json(FUSION_PANEL)
    review_boundary = review_rule.get("安全边界", {})

    checks: list[dict[str, object]] = [
        {"名称": "宪法级原则总纲存在", "通过": CONSTITUTION_DOC.exists()},
        {"名称": "宪法级原则规则存在", "通过": CONSTITUTION_RULE.exists()},
        {"名称": "股票报告质检融入方案存在", "通过": REPORT_REVIEW_DOC.exists()},
        {"名称": "股票报告质检融入规则存在", "通过": REPORT_REVIEW_RULE.exists()},
        {"名称": "通用报告质检方法存在", "通过": GENERAL_METHOD.exists()},
        {"名称": "text_reviewer脚本存在", "通过": TEXT_REVIEWER.exists()},
        {"名称": "审稿记录目录存在", "通过": REVIEW_RECORDS_DIR.exists()},
        {"名称": "宪法原则不少于12条", "通过": len(constitution_rule.get("宪法级原则", [])) >= 12},
        {"名称": "硬件天花板已纳入宪法", "通过": has_all(constitution_text, ["硬件天花板", "现实上限", "资源不足"])},
        {"名称": "平稳运行已纳入宪法", "通过": has_all(constitution_text, ["平稳运行", "企业微信入口", "股票助手"])},
        {"名称": "系统能力边界已纳入宪法", "通过": has_all(constitution_text, ["能力边界", "扩展能力", "进化能力"])},
        {"名称": "影子试验失败隔离已纳入宪法", "通过": has_all(constitution_text, ["影子试验", "失败隔离", "正式链路"])},
        {"名称": "克制施工已纳入宪法", "通过": has_all(constitution_text, ["克制施工", "避免新增无必要复杂度"])},
        {"名称": "报告质检覆盖完整性结构语言排版", "通过": has_all(review_text, ["内容完整性", "文章结构", "语言描述", "排版显示"])},
        {"名称": "报告质检明确旁路不接管正式推送", "通过": has_all(review_text, ["旁路实验", "不接管正式推送", "不自动替换原文"])},
        {"名称": "报告质检明确不改事实判断", "通过": has_all(review_text, ["不改事实", "不改判断", "不改推荐名单"])},
        {"名称": "报告质检纳入手机端排版", "通过": has_all(review_text, ["手机企业微信", "窄屏", "宽表格"])},
        {"名称": "报告质检规则安全边界全部禁止", "通过": bool(review_boundary) and all(value is False for value in review_boundary.values())},
        {"名称": "通用方法可复制到其他子系统", "通过": has_all(method_text, ["适用于所有", "税收", "工作总结"])},
        {"名称": "融合面板仍标记不影响股票日常使用", "通过": "不影响" in fusion.get("是否影响股票日常使用", "")},
    ]

    ok = all(item["通过"] for item in checks)
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：股票报告质检与宪法级原则已纳入施工体系" if ok else "未通过：股票报告质检或宪法级原则存在缺口",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "安全边界": {
            "触发n8n": False,
            "调用模型": False,
            "发送企业微信": False,
            "写正式业务库": False,
            "自动交易": False
        }
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
