# -*- coding: utf-8 -*-
"""
名称：验证中信借鉴指标扩展.py
作用：轻量验证从成熟软件借鉴后新增的指标字段能否在样本日线上正常计算。
边界：只读样本日线；只写验证报告；不联网；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from 技术指标计算库 import calc_all_indicators


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict) -> str:
    lines = [
        "# 中信借鉴指标扩展验证报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 样本文件：{report['样本文件']}",
        f"- 样本行数：{report['样本行数']}",
        "",
        "## 新增字段",
        "",
    ]
    for field, value in report["末行字段值"].items():
        lines.append(f"- {field}：{value}")
    lines.extend(["", "## 缺失字段", ""])
    if report["缺失字段"]:
        for field in report["缺失字段"]:
            lines.append(f"- {field}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    sample = root / "03数据" / "013券商本机历史日线" / "中信证券" / "按股票" / "sz" / "sz000001.json"
    out_dir = root / "03数据" / "015外部成熟软件指标借鉴" / "中信证券"
    data = json.loads(sample.read_text(encoding="utf-8-sig"))
    df = pd.DataFrame(data["日线"])
    for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "换手率"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    result = calc_all_indicators(df)
    expected = [
        "近似涨停",
        "近似跌停",
        "连涨天数",
        "连跌天数",
        "连板近似天数",
        "60日箱体突破",
        "VCP收缩形态",
        "MA250向上",
        "第二阶段模板得分",
        "第二阶段趋势模板",
        "成交额5_20比",
        "成交额20_60比",
        "成交量60日波动率",
    ]
    missing = [field for field in expected if field not in result.columns]
    last = result.iloc[-1]
    values = {field: (None if field in missing else str(last[field])) for field in expected}
    report = {
        "名称": "中信借鉴指标扩展验证报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not missing else "需复核",
        "样本文件": str(sample),
        "样本行数": len(result),
        "新增字段数量": len(expected) - len(missing),
        "缺失字段": missing,
        "末行字段值": values,
        "安全边界": {
            "是否联网": False,
            "是否调用券商接口": False,
            "是否交易": False,
        },
    }
    json_path = out_dir / "中信借鉴指标扩展验证_最新.json"
    md_path = out_dir / "中信借鉴指标扩展验证_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "样本行数": len(result),
        "新增字段数量": report["新增字段数量"],
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
