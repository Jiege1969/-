# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信真实发送准备清单.py
作用：生成企业微信真实发送前的人工放行和上线准备清单。
安全边界：只生成本地待填写清单；不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
MESSAGE_VALIDATION = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口消息预演验收_最新.json"
SEND_GATE = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口发送门禁_最新.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信真实发送准备清单_最新.json"
OUT_MD = OUT_DIR / "税收企业微信真实发送准备清单_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    validation = load_json(MESSAGE_VALIDATION)
    send_gate = load_json(SEND_GATE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checklist = {
        "名称": "税收企业微信真实发送准备清单",
        "生成时间": now,
        "放行状态": config.get("人工放行", {}).get("默认状态", "pending"),
        "配置来源": str(CONFIG),
        "消息预演验收来源": str(MESSAGE_VALIDATION),
        "发送门禁来源": str(SEND_GATE),
        "当前入口状态": config.get("入口状态"),
        "当前真实发送放行": config.get("真实发送放行"),
        "当前消息预演验收结论": validation.get("结论", "缺失"),
        "当前发送门禁结论": send_gate.get("结论", "缺失"),
        "上线前必填": {
            "人工复核人": "",
            "复核时间": "",
            "接收范围": "",
            "允许发送场景": "",
            "回滚负责人": "",
            "异常联系人": "",
            "备注": ""
        },
        "上线前必须确认": [
            "确认企业微信接收群或接收人只用于内部待复核沟通。",
            "确认消息不包含正式税务意见、确定性适用结论或金额测算结论。",
            "确认消息不包含未脱敏纳税人识别号、银行账号、身份证号、手机号或企业微信凭据。",
            "确认入口状态、真实发送放行、人工放行状态、企业微信凭据和消息预演验收均通过后才允许真实发送。",
            "确认发送后保留审计台账和可追溯报告路径。"
        ],
        "不得填写内容": [
            "企业微信Webhook完整URL",
            "企业微信应用Secret",
            "电子税务局账号密码",
            "财税软件账号密码",
            "未脱敏纳税人敏感身份信息"
        ],
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False
        }
    }
    OUT_JSON.write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信真实发送准备清单",
        "",
        f"- 生成时间：{now}",
        f"- 放行状态：{checklist['放行状态']}",
        f"- 当前入口状态：{checklist['当前入口状态']}",
        f"- 当前真实发送放行：{checklist['当前真实发送放行']}",
        f"- 当前消息预演验收结论：{checklist['当前消息预演验收结论']}",
        f"- 当前发送门禁结论：{checklist['当前发送门禁结论']}",
        "",
        "## 上线前必填",
        "",
    ]
    for key, value in checklist["上线前必填"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 上线前必须确认", ""])
    for item in checklist["上线前必须确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 不得填写内容", ""])
    for item in checklist["不得填写内容"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in checklist["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "放行状态": checklist["放行状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
