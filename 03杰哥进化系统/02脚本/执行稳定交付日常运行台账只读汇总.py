# -*- coding: utf-8 -*-
"""执行稳定交付日常运行台账只读汇总。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包" / "稳定交付日常运行台账与交接验收包_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "52稳定交付日常运行台账与交接验收包"
LATEST_JSON = OUTPUT_DIR / "日常运行台账只读汇总_最新.json"
LATEST_MD = OUTPUT_DIR / "日常运行台账只读汇总_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evaluate_check(item: dict[str, Any]) -> dict[str, Any]:
    path = Path(item["验收产物"])
    if not path.exists():
        return {**item, "存在": False, "当前结果": "missing", "摘要": "验收产物不存在"}
    data = read_json(path)
    result = "unknown"
    summary: Any = {}
    if data.get("总体状态") == "pass":
        result = "pass"
        summary = data.get("汇总", {})
    elif data.get("通过") is True:
        result = "pass"
        summary = data.get("指标", data.get("汇总", {}))
    elif data.get("passed") is True:
        result = "pass"
        summary = data.get("metrics", {})
    elif data.get("汇总", {}).get("失败") == 0 and data.get("汇总", {}).get("通过", 0) > 0:
        result = "pass"
        summary = data.get("汇总", {})
    else:
        result = "blocked"
        summary = data.get("指标", data.get("汇总", data))
    return {**item, "存在": True, "当前结果": result, "摘要": summary}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['检查项']} | {item['当前结果']} | {item['验收产物']} |"
        for item in report["检查结果"]
    ]
    return "\n".join(
        [
            "# 日常运行台账只读汇总",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 检查项 | 当前结果 | 验收产物 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 只读取验收产物，不请求业务接口，不重载服务。",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    checks = [evaluate_check(item) for item in asset.get("日常检查项", [])]
    passed = sum(1 for item in checks if item["当前结果"] == "pass")
    report = {
        "名称": "日常运行台账只读汇总",
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
