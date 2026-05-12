# -*- coding: utf-8 -*-
"""
验证股票前台展示口径一致性。

只读取股票研究系统内前台展示产物并写入验收报告；不接券商、不交易、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA = ROOT / "03数据"
OUT_DIR = DATA / "246展示口径修复"
RESULT_JSON = OUT_DIR / "股票展示口径一致性验收_最新.json"
RESULT_MD = OUT_DIR / "股票展示口径一致性验收_最新.md"

DISPLAY_PRODUCTS = [
    DATA / "185专家市场总览" / "股票专家市场总览_最新.md",
    DATA / "185专家市场总览" / "股票专家市场总览_最新.json",
    DATA / "86图形报告" / "股票图形报告_最新.json",
    DATA / "86图形报告" / "股票图形报告_最新.svg",
    DATA / "86图形报告" / "sz002466_最新_png参数.json",
    DATA / "86图形报告" / "sz002466_最新.svg",
    DATA / "135分层日报" / "单股标准报告v2_天齐锂业_sz002466_最新.md",
    DATA / "135分层日报" / "单股标准报告v2_最新.md",
    DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md",
    DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json",
]

FORBIDDEN_DISPLAY_TERMS = [
    "重点关注",
    "常规推荐",
    "重点推荐",
    "买入研究信号",
    "卖出研究信号",
    "卖出/退出研究信号",
]

RECOMMENDATION_TERMS = [
    "重点关注",
    "常规推荐",
    "重点推荐",
    "买入研究信号",
    "常规研究，但现价不追",
    "当前进入重点研究",
]

RISK_TERMS = [
    "风险复核",
    "继续回避",
    "回避",
    "暂不建议关注",
    "卖出研究信号",
    "卖出/退出研究信号",
]

REQUIRED_REPLACEMENT_TERMS = [
    "研究价值评分",
    "当前操作建议",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.suffix.lower() == ".json":
        try:
            data: Any = json.loads(path.read_text(encoding="utf-8-sig"))
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            return path.read_text(encoding="utf-8-sig", errors="replace")
    return path.read_text(encoding="utf-8-sig", errors="replace")


def check_path(path: Path) -> dict[str, Any]:
    text = read_text(path)
    forbidden_hits = [term for term in FORBIDDEN_DISPLAY_TERMS if term in text]
    recommendation_hits = [term for term in RECOMMENDATION_TERMS if term in text]
    risk_hits = [term for term in RISK_TERMS if term in text]
    replacement_hits = [term for term in REQUIRED_REPLACEMENT_TERMS if term in text]
    is_expert = "185专家市场总览" in str(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "forbidden_hits": forbidden_hits,
        "recommendation_hits": recommendation_hits,
        "risk_hits": risk_hits,
        "has_conflict": bool(recommendation_hits and risk_hits),
        "replacement_hits": replacement_hits,
        "expert_replacement_ready": (not is_expert) or all(term in text for term in REQUIRED_REPLACEMENT_TERMS),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checked = [check_path(path) for path in DISPLAY_PRODUCTS]
    errors: list[str] = []
    for item in checked:
        if not item["exists"]:
            errors.append(f"展示产物不存在：{item['path']}")
        if item["forbidden_hits"]:
            errors.append(f"存在旧展示词 {item['forbidden_hits']}：{item['path']}")
        if item["has_conflict"]:
            errors.append(f"同一展示产物同时出现推荐类词和风险/回避类词：{item['path']}")
        if not item["expert_replacement_ready"]:
            errors.append(f"专家总览未同时包含研究价值评分和当前操作建议：{item['path']}")
    result = {
        "名称": "股票展示口径一致性验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "检查文件数": len(checked),
        "检查结果": checked,
        "安全边界": {
            "不接券商": True,
            "不交易": True,
            "不生成买卖指令": True,
            "不修改核心评分引擎": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不真实发送企业微信": True,
        },
    }
    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票展示口径一致性验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 是否通过：{'是' if result['通过'] else '否'}",
        f"- 检查文件数：{result['检查文件数']}",
        "",
        "## 错误",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- 无"])
    lines.extend(["", "## 检查结果", ""])
    for item in checked:
        lines.append(
            f"- {item['path']} | forbidden={item['forbidden_hits']} | conflict={item['has_conflict']} | replacement={item['replacement_hits']}"
        )
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
