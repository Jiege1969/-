# -*- coding: utf-8 -*-
"""
名称：清理全A历史日线_剔除盘中未完结日.py
作用：清理正式历史日线库中误写入的当天盘中未完结日线。
边界：只处理股票系统 03数据/012全A历史日线；不联网；不触发外部系统；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_date(value: Any) -> str:
    return str(value or "").replace("-", "")[:8]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A历史日线盘中未完结日清理报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 清理阈值日期：{report['清理阈值日期']}",
        f"- 扫描文件数：{report['扫描文件数']}",
        f"- 修改文件数：{report['修改文件数']}",
        f"- 删除日线行数：{report['删除日线行数']}",
        "",
        "## 修改样本",
        "",
    ]
    if report["修改样本"]:
        for item in report["修改样本"][:50]:
            lines.append(
                f"- {item['代码']} {item.get('名称', '')}：删除{item['删除行数']}行，"
                f"原末日{item['原末日']} -> 新末日{item['新末日']}"
            )
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    data_dir = root / "03数据" / "012全A历史日线"
    stock_dir = data_dir / "按股票"
    today = datetime.now().strftime("%Y%m%d")
    files = list(stock_dir.glob("*/*.json"))
    modified = 0
    removed_rows = 0
    samples: list[dict[str, Any]] = []

    for path in files:
        data = load_json(path)
        rows = list(data.get("日线", []))
        if not rows:
            continue
        original_last = rows[-1].get("日期")
        kept = [row for row in rows if compact_date(row.get("日期")) < today]
        removed = len(rows) - len(kept)
        if removed <= 0:
            continue
        data["日线"] = kept
        data["记录数"] = len(kept)
        data["末日"] = kept[-1].get("日期") if kept else ""
        data["盘中未完结日清理"] = {
            "清理时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "清理阈值日期": today,
            "删除行数": removed,
            "说明": "剔除当天盘中未完结日线，历史底座只保留完整交易日。",
        }
        write_json(path, data)
        modified += 1
        removed_rows += removed
        samples.append({
            "代码": data.get("代码", path.stem),
            "名称": data.get("名称", ""),
            "删除行数": removed,
            "原末日": original_last,
            "新末日": data["末日"],
            "文件": str(path),
        })

    report = {
        "名称": "全A历史日线盘中未完结日清理报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过",
        "清理阈值日期": today,
        "扫描文件数": len(files),
        "修改文件数": modified,
        "删除日线行数": removed_rows,
        "修改样本": samples,
        "安全边界": {
            "是否联网": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否交易": False,
        },
    }
    json_path = data_dir / "全A历史日线盘中未完结日清理_最新.json"
    md_path = data_dir / "全A历史日线盘中未完结日清理_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "扫描文件数": len(files),
        "修改文件数": modified,
        "删除日线行数": removed_rows,
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
