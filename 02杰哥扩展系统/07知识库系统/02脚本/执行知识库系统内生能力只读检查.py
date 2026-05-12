# -*- coding: utf-8 -*-
"""
名称：执行知识库系统内生能力只读检查.py
作用：只读检查知识库系统层级、输入输出契约、调度协同、问题修复和证据边界是否具备文件证据。
安全边界：只读扫描文件名，仅写入本系统03数据检查结果；不写正式向量库，不触发n8n。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03数据" / "知识库系统内生能力只读检查_最新.json"
KEYWORDS = ["层级", "输入输出", "调度", "问题修复", "证据", "追溯", "待复核", "免疫"]


def main() -> int:
    names = [p.name for p in ROOT.rglob("*") if p.is_file()]
    hits = {key: [name for name in names if key in name][:5] for key in KEYWORDS}
    report = {
        "名称": "知识库系统内生能力只读检查",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all(hits.values()) else "needs_attention",
        "能力证据": hits,
        "安全边界": {
            "正式向量写库": False,
            "触发n8n": False,
            "外发回答": False,
            "覆盖原资料": False
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"总体状态": report["总体状态"], "输出": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
