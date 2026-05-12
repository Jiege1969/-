# -*- coding: utf-8 -*-
"""执行稳定版候选最终总索引只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包" / "稳定版候选最终总索引与收口验收包_最新.json"
LATEST_JSON = ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包" / "稳定版候选最终总索引只读核对_最新.json"
LATEST_MD = ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包" / "稳定版候选最终总索引只读核对_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_verify_passed(path: Path) -> bool:
    if not path.exists():
        return False
    data = read_json(path)
    if data.get("通过") is True and data.get("指标", {}).get("错误数", 0) == 0:
        return True
    if data.get("总体状态") == "pass" and data.get("汇总", {}).get("失败", 0) == 0:
        return True
    return False


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {'pass' if item['资料存在'] else 'missing'} | {'pass' if item['验收通过'] else 'blocked'} |"
        for item in report["核对结果"]
    ]
    return "\n".join(
        [
            "# 稳定版候选最终总索引只读核对",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 资料 | 验收 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    results = []
    for item in asset.get("最终总索引", []):
        material = Path(item["路径"])
        verify = Path(item["验收"])
        results.append(
            {
                **item,
                "资料存在": material.exists(),
                "验收存在": verify.exists(),
                "验收通过": is_verify_passed(verify),
            }
        )
    passed = sum(1 for item in results if item["资料存在"] and item["验收通过"])
    output_ok = all(Path(path).exists() for path in asset.get("输出文件", {}).values())
    safety_ok = all(value is False for value in asset.get("安全边界", {}).values())
    closeout_ok = len(asset.get("收口验收项", [])) >= 7 and len(asset.get("阅读入口", [])) >= 5
    all_passed = passed == len(results) and output_ok and safety_ok and closeout_ok
    report = {
        "名称": "稳定版候选最终总索引只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all_passed else "blocked",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "核对结果": results,
        "附加核对": {
            "输出文件全部存在": output_ok,
            "安全边界全部false": safety_ok,
            "收口验收与阅读入口完整": closeout_ok,
        },
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
