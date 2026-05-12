# -*- coding: utf-8 -*-
"""
名称：执行孵化区内生能力只读检查.py
作用：只读确认孵化区影子资产、成熟度、人工复核、进化候选等能力证据是否存在。
安全边界：只读扫描文件名，不触发n8n，不写正式库，不接入正式业务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "03数据" / "孵化区内生能力只读检查_最新.json"
KEYWORDS = ["影子", "成熟度", "人工复核", "进化候选", "验收", "失败", "待补", "只读"]


def main() -> int:
    names = [p.name for p in ROOT.rglob("*") if p.is_file()]
    hits = {key: [name for name in names if key in name][:5] for key in KEYWORDS}
    report = {
        "名称": "孵化区内生能力只读检查",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if all(hits.values()) else "needs_attention",
        "能力证据": hits,
        "安全边界": {
            "触发n8n": False,
            "写正式库": False,
            "正式业务执行": False
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"总体状态": report["总体状态"], "输出": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
