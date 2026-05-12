# -*- coding: utf-8 -*-
"""执行稳定交付使用者视角只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "56稳定交付使用者交付摘要与非技术操作手册包" / "稳定交付使用者交付摘要与非技术操作手册包_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "56稳定交付使用者交付摘要与非技术操作手册包"
LATEST_JSON = OUTPUT_DIR / "使用者视角只读核对_最新.json"
LATEST_MD = OUTPUT_DIR / "使用者视角只读核对_最新.md"


REQUIRED_PHRASES = [
    "不会真实发给企业微信",
    "不登录税局",
    "不接券商",
    "不真实渲染成片",
    "不会自动转正式规则",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['检查项']} | {'pass' if item['通过'] else 'blocked'} | {item['说明']} |" for item in report["检查结果"]]
    return "\n".join(
        [
            "# 使用者视角只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 检查项 | 结果 | 说明 |",
            "| --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    text_blob = json.dumps(asset, ensure_ascii=False)
    output_files = asset.get("输出文件", {})
    checks = [
        {"检查项": "能力摘要不少于 5 项", "通过": len(asset.get("能力摘要", [])) >= 5, "说明": str(len(asset.get("能力摘要", [])))},
        {"检查项": "使用场景不少于 5 项", "通过": len(asset.get("使用场景", [])) >= 5, "说明": str(len(asset.get("使用场景", [])))},
        {"检查项": "可做清单不少于 4 项", "通过": len(asset.get("可以做", [])) >= 4, "说明": str(len(asset.get("可以做", [])))},
        {"检查项": "不可做清单不少于 5 项", "通过": len(asset.get("不可以做", [])) >= 5, "说明": str(len(asset.get("不可以做", [])))},
        {"检查项": "状态卡覆盖 4 个版本", "通过": len(asset.get("状态卡", {})) >= 4, "说明": str(len(asset.get("状态卡", {})))},
        {"检查项": "红线表达齐全", "通过": all(phrase in text_blob for phrase in REQUIRED_PHRASES), "说明": "关键限制短语检查"},
        {"检查项": "输出文件全部存在", "通过": all(Path(path).exists() for path in output_files.values()), "说明": str(len(output_files))},
        {"检查项": "安全边界全部 false", "通过": all(value is False for value in asset.get("安全边界", {}).values()), "说明": str(len(asset.get("安全边界", {})))},
    ]
    passed = sum(1 for item in checks if item["通过"])
    report = {
        "名称": "使用者视角只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed == len(checks) else "blocked",
        "汇总": {"总数": len(checks), "通过": passed, "失败": len(checks) - passed},
        "检查结果": checks,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
