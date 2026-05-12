# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信机器人终端绑定报告.py
作用：登记企业微信机器人“杰哥工作秘书”作为税收业务系统输入输出终端。
安全边界：只生成本地终端绑定报告；不读取凭据、不联网、不真实发送、不接收真实消息。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信机器人终端绑定报告_最新.json"
OUT_MD = OUT_DIR / "税收企业微信机器人终端绑定报告_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    terminal = config.get("机器人终端", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信机器人终端绑定报告",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "机器人名称": terminal.get("机器人名称", ""),
        "绑定状态": terminal.get("绑定状态", "missing"),
        "终端定位": terminal.get("终端定位", ""),
        "输入职责": terminal.get("输入职责", []),
        "输出职责": terminal.get("输出职责", []),
        "输入技术边界": terminal.get("输入技术边界", ""),
        "输出技术边界": terminal.get("输出技术边界", ""),
        "禁止职责": terminal.get("禁止职责", []),
        "当前收发状态": {
            "是否登记为输入终端": terminal.get("机器人名称") == "杰哥工作秘书",
            "是否登记为输出终端": terminal.get("机器人名称") == "杰哥工作秘书",
            "是否已接入真实输入回调": False,
            "是否已接入真实输出发送": False,
            "真实收发放行状态": "not_released"
        },
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否接收真实消息": False,
            "是否企业微信真实发送": False,
            "是否修改入口状态": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False
        }
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信机器人终端绑定报告",
        "",
        f"- 生成时间：{now}",
        f"- 机器人名称：{report['机器人名称']}",
        f"- 绑定状态：{report['绑定状态']}",
        f"- 终端定位：{report['终端定位']}",
        f"- 真实收发放行状态：{report['当前收发状态']['真实收发放行状态']}",
        "",
        "## 输入职责",
        "",
    ]
    for item in report["输入职责"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 输出职责", ""])
    for item in report["输出职责"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 技术边界", ""])
    lines.append(f"- 输入：{report['输入技术边界']}")
    lines.append(f"- 输出：{report['输出技术边界']}")
    lines.extend(["", "## 禁止职责", ""])
    for item in report["禁止职责"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "机器人名称": report["机器人名称"], "绑定状态": report["绑定状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
