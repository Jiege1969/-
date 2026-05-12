# -*- coding: utf-8 -*-
"""
名称：生成企业微信股票查询消息契约.py
作用：生成企业微信、OpenClaw、n8n、股票助手之间的股票查询消息契约文档和机器可读包。
触发方式：python 生成企业微信股票查询消息契约.py
依赖：Python标准库；企业微信股票查询消息契约.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地契约文件；不连接企业微信；不触发n8n；不调用OpenClaw；不发送消息；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询消息契约生成脚本。
标识：stock-wework-message-contract-generate
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_md(package: dict[str, Any]) -> str:
    contract = package["契约"]
    role_lines = "\n".join(f"- {key}：{value}" for key, value in contract["角色边界"].items())
    inbound = "\n".join(f"- {item}" for item in contract["入站消息字段"])
    outbound = "\n".join(f"- {item}" for item in contract["出站回复字段"])
    voice = "\n".join(f"- {item}" for item in contract["语音容错规则"])
    safety = "\n".join(f"- {item}" for item in contract["安全边界"])
    return f"""# 企业微信股票查询消息契约

生成时间：{package['生成时间']}

结论：{package['结论']}

## 一、角色边界

{role_lines}

## 二、入站消息字段

{inbound}

## 三、出站回复字段

{outbound}

## 四、语音容错规则

{voice}

## 五、安全边界

{safety}

## 六、样例

```json
{json.dumps(package['样例'], ensure_ascii=False, indent=2)}
```
"""


def main() -> int:
    root = module_root()
    contract_path = root / "01配置" / "企业微信股票查询消息契约.json"
    contract = load_json(contract_path)
    sample = {
        "入站": {
            "trace_id": "stock-demo-001",
            "source": "wework_openclaw",
            "user_id_hash": "local-user",
            "message_type": "voice_or_text",
            "text": "分析新易盛",
            "voice_text": "分析新易盛",
            "voice_confidence": 0.86,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "出站": {
            "trace_id": "stock-demo-001",
            "mode": "disabled_draft_only",
            "reply_text": "研究辅助回复草稿，不构成投资建议。",
            "data_health": "优秀",
            "need_clarification": False,
            "clarification_question": "",
            "real_send": False,
            "trade": False,
        },
    }
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "contract_only",
        "契约来源": str(contract_path),
        "契约": contract,
        "样例": sample,
        "实际动作": {
            "连接企业微信": False,
            "调用OpenClaw": False,
            "触发n8n": False,
            "发送消息": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "结论": "股票企业微信查询消息契约已生成，真实消息链路仍未启用。",
    }
    output_dir = root / "03数据" / "21企业微信消息契约"
    log_dir = root / "04日志" / "企业微信消息契约"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "企业微信股票查询消息契约_最新.json"
    latest_json = output_dir / "企业微信股票查询消息契约_最新.json"
    md_path = output_dir / "企业微信股票查询消息契约_最新.md"
    latest_md = output_dir / "企业微信股票查询消息契约_最新.md"
    log_path = log_dir / f"stock-wework-message-contract-generate-{timestamp}.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    markdown = build_md(package)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, package)
    print(json.dumps({"模式": package["模式"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
