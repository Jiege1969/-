# -*- coding: utf-8 -*-
"""生成日常可用交付版收口后进度校准。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
OUTPUT_DIR = ROOT / "03数据" / "47日常可用交付版收口后进度校准"
LATEST_JSON = OUTPUT_DIR / "日常可用交付版收口后进度校准_最新.json"
LATEST_MD = OUTPUT_DIR / "日常可用交付版收口后进度校准_最新.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    asset = {
        "名称": "日常可用交付版收口后进度校准",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "候选进度校准，不是正式承诺排期",
        "校准原因": [
            "日常可用交付版状态包已生成并验收通过。",
            "一键只读总回归已复跑通过。",
            "日常使用说明、故障处理清单、税收接续替代包、端口诊断与重载申请模板已生成并验收通过。",
        ],
        "整体进度判断": {
            "日常可用交付版": "93%-96%",
            "稳定交付版": "64%-74%",
            "完全交付使用版": "35%-47%",
            "真正自主运行版": "28%-38%",
        },
        "剩余有效工时判断": {
            "日常可用交付版剩余": {"乐观": 4, "常规": 8, "保守": 16},
            "稳定交付版剩余": {"乐观": 42, "常规": 70, "保守": 112},
            "完全交付使用版剩余": {"乐观": 165, "常规": 272, "保守": 420},
            "真正自主运行版剩余": {"乐观": 280, "常规": 520, "保守": 850},
        },
        "日常可用版剩余收口项": [
            "连续再跑2轮一键只读总回归并保持全通过。",
            "把收口包纳入后续日常使用入口说明。",
            "形成一次最终日常可用交付候选回传。",
        ],
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "重载19310": False,
            "重载19302": False,
            "真实发送企业微信": False,
            "接n8n": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式税务结论": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }
    write_json(LATEST_JSON, asset)
    lines = [
        "# 日常可用交付版收口后进度校准",
        "",
        f"- 生成时间：{asset['生成时间']}",
        f"- 性质：{asset['性质']}",
        "",
        "## 进度判断",
        "",
        "| 目标版本 | 当前完成度 | 乐观 | 常规 | 保守 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for version, key in [
        ("日常可用交付版", "日常可用交付版剩余"),
        ("稳定交付版", "稳定交付版剩余"),
        ("完全交付使用版", "完全交付使用版剩余"),
        ("真正自主运行版", "真正自主运行版剩余"),
    ]:
        h = asset["剩余有效工时判断"][key]
        lines.append(f"| {version} | {asset['整体进度判断'][version]} | {h['乐观']} | {h['常规']} | {h['保守']} |")
    lines.extend(["", "## 日常可用版剩余收口项", ""])
    lines.extend([f"- {item}" for item in asset["日常可用版剩余收口项"]])
    write_text(LATEST_MD, "\n".join(lines))
    print(json.dumps({"日常可用交付版": asset["整体进度判断"]["日常可用交付版"], "常规剩余": 8, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
