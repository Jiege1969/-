# -*- coding: utf-8 -*-
"""执行稳定交付跨业务回归证据链只读汇总。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "53稳定交付跨业务回归证据链与版本冻结候选包" / "稳定交付跨业务回归证据链与版本冻结候选包_最新.json"
OUTPUT_DIR = ROOT / "03数据" / "53稳定交付跨业务回归证据链与版本冻结候选包"
LATEST_JSON = OUTPUT_DIR / "跨业务回归证据链只读汇总_最新.json"
LATEST_MD = OUTPUT_DIR / "跨业务回归证据链只读汇总_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def evaluate_json(path: Path) -> tuple[str, Any]:
    if not path.exists():
        return "missing", "证据不存在"
    data = read_json(path)
    if data.get("总体状态") == "pass":
        return "pass", data.get("汇总", {})
    if data.get("通过") is True:
        return "pass", data.get("指标", data.get("汇总", {}))
    if data.get("passed") is True:
        return "pass", data.get("metrics", {})
    if data.get("汇总", {}).get("失败") == 0 and data.get("汇总", {}).get("通过", 0) > 0:
        return "pass", data.get("汇总", {})
    if (
        data.get("执行器状态") == "禁用态"
        and data.get("是否调用剪辑软件") is False
        and data.get("是否生成真实媒体") is False
        and data.get("是否自动发布") is False
    ):
        return "pass", {
            "执行器状态": data.get("执行器状态"),
            "是否调用剪辑软件": data.get("是否调用剪辑软件"),
            "是否生成真实媒体": data.get("是否生成真实媒体"),
            "是否自动发布": data.get("是否自动发布"),
        }
    return "blocked", data.get("指标", data.get("汇总", {}))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['业务线']} | {item['证据名称']} | {item['当前结果']} | {item['证据路径']} |"
        for item in report["证据检查结果"]
    ]
    return "\n".join(
        [
            "# 跨业务回归证据链只读汇总",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            f"- 冻结候选成立：{report['冻结候选成立']}",
            "",
            "| 编号 | 业务线 | 证据名称 | 当前结果 | 证据路径 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 只读取证据链产物，不触发业务接口，不写正式规则。",
        ]
    )


def main() -> int:
    asset = read_json(ASSET_JSON)
    results = []
    for item in asset.get("跨业务回归证据链", []):
        status, summary = evaluate_json(Path(item["证据路径"]))
        results.append({**item, "当前结果": status, "摘要": summary})
    passed = sum(1 for item in results if item["当前结果"] == "pass")
    freeze_ok = passed == len(results) and all(value is False for value in asset.get("安全边界", {}).values())
    report = {
        "名称": "跨业务回归证据链只读汇总",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if freeze_ok else "blocked",
        "冻结候选成立": freeze_ok,
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "证据检查结果": results,
        "安全边界": asset.get("安全边界", {}),
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "冻结候选成立": freeze_ok, "通过": passed, "失败": len(results) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
