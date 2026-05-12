# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信凭据接入预检.py
作用：检查企业微信凭据环境变量是否具备接入条件，并生成脱敏预检报告。
安全边界：只检查环境变量存在性和基本形态；不输出凭据原文、不联网、不真实发送。
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信凭据接入预检_最新.json"
OUT_MD = OUT_DIR / "税收企业微信凭据接入预检_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def env_status(name: str) -> dict[str, Any]:
    value = os.environ.get(name, "")
    return {
        "环境变量名": name,
        "是否存在": bool(value),
        "字符长度": len(value) if value else 0,
        "是否已脱敏": True,
        "值预览": "[已设置-不显示]" if value else "[未设置]",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    webhook_var = config.get("凭据配置", {}).get("机器人Webhook环境变量", "TAX_WECOM_WEBHOOK_URL")
    app_vars = config.get("凭据配置", {}).get("应用凭据环境变量", [])
    webhook_value = os.environ.get(webhook_var, "")
    webhook_status = env_status(webhook_var)
    webhook_status["格式是否疑似企业微信机器人Webhook"] = bool(
        webhook_value and re.match(r"^https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+$", webhook_value)
    )
    app_status = [env_status(name) for name in app_vars]
    app_complete = bool(app_status) and all(item["是否存在"] for item in app_status)
    credential_ready = webhook_status["格式是否疑似企业微信机器人Webhook"] or app_complete

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信凭据接入预检",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "凭据预检结论": "具备凭据形态" if credential_ready else "未具备凭据形态",
        "机器人Webhook预检": webhook_status,
        "应用凭据预检": app_status,
        "是否具备真实发送凭据条件": credential_ready,
        "说明": [
            "本预检只确认环境变量是否存在和基本形态，不验证企业微信服务端可用性。",
            "报告不得输出Webhook、Secret或任何凭据原文。",
            "即使凭据预检通过，仍需入口状态、真实发送放行、人工放行、消息验收和发送门禁全部通过。"
        ],
        "安全边界": {
            "是否联网": False,
            "是否输出凭据原文": False,
            "是否保存凭据": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False
        }
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信凭据接入预检",
        "",
        f"- 生成时间：{now}",
        f"- 凭据预检结论：{report['凭据预检结论']}",
        f"- 是否具备真实发送凭据条件：{credential_ready}",
        "",
        "## 机器人Webhook预检",
        "",
    ]
    for key, value in webhook_status.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 应用凭据预检", ""])
    for item in app_status:
        lines.append(f"- {item['环境变量名']}：存在={item['是否存在']}，字符长度={item['字符长度']}，值预览={item['值预览']}")
    lines.extend(["", "## 说明", ""])
    for item in report["说明"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "凭据预检结论": report["凭据预检结论"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
