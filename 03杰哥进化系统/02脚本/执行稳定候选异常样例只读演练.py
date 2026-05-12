# -*- coding: utf-8 -*-
"""执行稳定候选异常样例只读演练。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例库与演练包_最新.json"
LATEST_JSON = ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例只读演练_最新.json"
LATEST_MD = ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例只读演练_最新.md"


STOP_LEVELS = {"L3", "L4", "L5"}
AUTO_LEVELS = {"L1", "L2"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['预期分级']} | {item['演练动作']} | {'pass' if item['通过'] else 'blocked'} |"
        for item in report["演练结果"]
    ]
    return "\n".join(
        [
            "# 稳定候选异常样例只读演练",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 分级 | 演练动作 | 结果 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    results = []
    for sample in asset.get("异常样例", []):
        level = sample.get("预期分级")
        if level in AUTO_LEVELS:
            action = "允许只读复跑或低风险候选修复"
            passed = "不得" in sample.get("停止条件", "") or "升级" in sample.get("停止条件", "")
        elif level in STOP_LEVELS:
            action = "必须停止并汇报/等待确认"
            passed = "不得" in sample.get("停止条件", "") or "停止" in sample.get("自动动作", "")
        else:
            action = "未知分级"
            passed = False
        results.append({**sample, "演练动作": action, "通过": passed})

    passed_count = sum(1 for item in results if item["通过"])
    report = {
        "名称": "稳定候选异常样例只读演练",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed_count == len(results) else "blocked",
        "汇总": {"总数": len(results), "通过": passed_count, "失败": len(results) - passed_count},
        "演练结果": results,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed_count, "失败": len(results) - passed_count, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
