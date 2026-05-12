# -*- coding: utf-8 -*-
"""
名称：生成行业景气结论.py
作用：复用L6行业强度排行，把后台分数转换为标准报告v2前台可读的行业景气结论。
触发方式：python 生成行业景气结论.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读03数据/133行业主题观察池；只写03数据/167行业景气结论；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-industry-prosperity-conclusion-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def classify(row: dict[str, Any]) -> tuple[str, str]:
    score = float(row.get("行业强度分") or 0)
    d5 = float(row.get("近5日平均涨跌幅") or 0)
    d20 = float(row.get("近20日平均涨跌幅") or 0)
    relative20 = float(row.get("近20日相对强弱") or 0)

    if score >= 4.2 and d5 > 0 and relative20 > 0:
        state = "上行"
    elif score <= 2.2 and d20 < 0 and relative20 < 0:
        state = "下行"
    elif abs(d20) <= 5:
        state = "震荡"
    else:
        state = "中性"

    sentence = (
        f"行业近5日平均涨跌幅{d5:.2f}%，近20日平均涨跌幅{d20:.2f}%，"
        f"相对沪深300强弱{relative20:.2f}%，行业强度分{score:.2f}/5，当前判断为{state}。"
    )
    return state, sentence


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    source = root / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json"
    l6 = load_json(source)

    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(l6.get("行业强度排行", []), start=1):
        state, sentence = classify(row)
        rows.append({
            "行业": row.get("行业"),
            "排名": idx,
            "成分数": row.get("成分数"),
            "景气状态": state,
            "前台结论": sentence,
            "行业强度分": row.get("行业强度分"),
            "当日平均涨跌幅": row.get("当日平均涨跌幅"),
            "近5日平均涨跌幅": row.get("近5日平均涨跌幅"),
            "近20日平均涨跌幅": row.get("近20日平均涨跌幅"),
            "近20日相对强弱": row.get("近20日相对强弱"),
            "数据状态": "部分接入",
            "说明": "基于L6成分股等权估算，尚未接入正式申万行业指数和行业价格数据。",
        })

    report = {
        "名称": "行业景气结论",
        "版本": "2026-05-02",
        "定位": "股票标准报告v2的P0数据源，把L6行业强度转换为前台景气结论。",
        "数据日期": l6.get("数据日期"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成行业景气结论.py",
        "上游文件": str(source),
        "数据健康度": {
            "输入行业数": len(l6.get("行业强度排行", [])),
            "输出行业数": len(rows),
            "是否完整": len(rows) > 0,
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "行业景气结论": rows,
    }

    output_dir = root / "03数据" / "167行业景气结论"
    latest = output_dir / "行业景气结论_最新.json"
    stamped = output_dir / f"行业景气结论_{stamp}.json"
    write_json(latest, report)
    write_json(stamped, report)

    print(json.dumps({
        "状态": "完成",
        "输出行业数": len(rows),
        "最新": str(latest),
        "时间戳": str(stamped),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
