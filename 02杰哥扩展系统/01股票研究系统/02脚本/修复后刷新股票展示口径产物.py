# -*- coding: utf-8 -*-
"""修复后刷新股票展示口径相关前台产物。

只调用本地展示生成函数；不启动服务、不发送企业微信、不触发n8n、不接券商、不交易。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "02脚本" / "股票助手入口.py"


def load_entry():
    spec = importlib.util.spec_from_file_location("stock_assistant_entry_display_fix", ENTRY)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载股票助手入口：{ENTRY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    entry = load_entry()
    expert = entry.build_expert_overview_reply("专家总览")
    tianqi = entry.build_analysis("分析天齐锂业", refresh=False, remember_context=False, entrance_role="助手")
    result = {
        "状态": "完成",
        "动作": [
            "刷新专家市场总览最新产物",
            "刷新天齐锂业单股前台短答、标准报告v2和图形报告最新产物",
        ],
        "专家总览": expert.get("专家总览"),
        "天齐锂业": {
            "状态": tianqi.get("状态"),
            "标准报告v2路径": tianqi.get("标准报告v2路径"),
            "图形报告PNG": (tianqi.get("图形报告") or {}).get("PNG"),
            "企业微信真实发送": False,
            "触发n8n": False,
            "交易": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
