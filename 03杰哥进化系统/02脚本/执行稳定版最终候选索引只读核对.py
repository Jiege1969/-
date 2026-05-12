# -*- coding: utf-8 -*-
"""执行稳定版最终候选索引只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "57稳定版最终候选索引与接续包" / "稳定版最终候选索引与接续包_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "57稳定版最终候选索引与接续包"
LATEST_JSON = OUTPUT_DIR / "稳定版最终候选索引只读核对_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版最终候选索引只读核对_最新.md"


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
        f"| {item['编号']} | {item['名称']} | {'pass' if item['存在'] else 'missing'} | {item['路径']} |"
        for item in report["索引核对结果"]
    ]
    return "\n".join(
        [
            "# 稳定版最终候选索引只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 结果 | 路径 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    checks = []
    for item in asset.get("候选资料索引", []):
        path = Path(item["路径"])
        checks.append({**item, "存在": path.exists()})
    passed = sum(1 for item in checks if item["存在"])
    output_files = asset.get("输出文件", {})
    file_outputs_ok = all(Path(path).exists() for path in output_files.values())
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    structure_ok = len(asset.get("后续接续步骤", [])) >= 5 and len(asset.get("交接阅读顺序", [])) >= 7
    extra_checks = [
        {"名称": "输出文件全部存在", "通过": file_outputs_ok},
        {"名称": "安全边界全部 false", "通过": safety_ok},
        {"名称": "接续步骤和阅读顺序完整", "通过": structure_ok},
    ]
    all_passed = passed == len(checks) and all(item["通过"] for item in extra_checks)
    report = {
        "名称": "稳定版最终候选索引只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all_passed else "blocked",
        "汇总": {"总数": len(checks), "通过": passed, "失败": len(checks) - passed},
        "索引核对结果": checks,
        "附加核对": extra_checks,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(checks) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
