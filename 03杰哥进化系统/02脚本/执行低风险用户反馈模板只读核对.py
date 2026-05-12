# -*- coding: utf-8 -*-
"""执行低风险用户反馈模板只读核对。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "71低风险用户反馈样本模板包" / "低风险用户反馈样本模板包_最新.json"
LATEST_JSON = ROOT / "03数据" / "71低风险用户反馈样本模板包" / "低风险用户反馈模板只读核对_最新.json"
LATEST_MD = ROOT / "03数据" / "71低风险用户反馈样本模板包" / "低风险用户反馈模板只读核对_最新.md"


REQUIRED_LINES = {"企业微信公共接入层", "税收业务", "股票研究", "视频制作", "智能进化候选"}


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
    return "\n".join(["# 低风险用户反馈模板只读核对", "", f"- 总体状态：{report['总体状态']}", "", "| 检查项 | 结果 | 说明 |", "| --- | --- | --- |", *rows])


def main() -> int:
    asset = read_json(ASSET_JSON)
    lines = {item.get("业务线") for item in asset.get("反馈模板", [])}
    output_files = asset.get("输出文件", {})
    checks = [
        {"检查项": "反馈模板覆盖五条业务线", "通过": REQUIRED_LINES.issubset(lines), "说明": ",".join(sorted(lines))},
        {"检查项": "反馈模板不少于5项", "通过": len(asset.get("反馈模板", [])) >= 5, "说明": str(len(asset.get("反馈模板", [])))},
        {"检查项": "反馈分级覆盖F1-F5", "通过": {item.get("级别") for item in asset.get("反馈分级规则", [])} == {"F1", "F2", "F3", "F4", "F5"}, "说明": "F1-F5"},
        {"检查项": "输出文件全部存在", "通过": all(Path(path).exists() for path in output_files.values()), "说明": str(len(output_files))},
        {"检查项": "安全边界全部false", "通过": all(value is False for value in asset.get("安全边界", {}).values()), "说明": str(len(asset.get("安全边界", {})))},
    ]
    passed = sum(1 for item in checks if item["通过"])
    report = {
        "名称": "低风险用户反馈模板只读核对",
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
