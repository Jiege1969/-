# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信n8n路由契约.py
作用：生成股票企业微信统一路由对接n8n时的输入输出契约和样例包。
触发方式：python 生成股票企业微信n8n路由契约.py
依赖：Python标准库；股票企业微信n8n路由契约.json；企业微信股票消息统一路由禁用态_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地契约文件；不导入n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信n8n路由契约生成脚本。
标识：stock-wework-n8n-router-contract-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(package: dict[str, Any]) -> str:
    contract = package["契约"]
    inputs = "\n".join(f"- {item}" for item in contract["n8n输入字段"])
    outputs = "\n".join(f"- {item}" for item in contract["股票路由输出字段"])
    roles = "\n".join(f"- {key}：{value}" for key, value in contract["职责边界"].items())
    safety = "\n".join(f"- {item}" for item in contract["安全要求"])
    return f"""# 股票企业微信n8n路由契约

生成时间：{package['生成时间']}

## 一、n8n输入字段

{inputs}

## 二、股票路由输出字段

{outputs}

## 三、职责边界

{roles}

## 四、安全要求

{safety}

## 五、样例

```json
{json.dumps(package['样例'], ensure_ascii=False, indent=2)}
```
"""


def main() -> int:
    root = module_root()
    contract = load_json(root / "01配置" / "股票企业微信n8n路由契约.json", {})
    latest_router = load_json(root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json", {})
    sample = {
        "n8n输入": {
            "trace_id": "stock-route-demo-001",
            "message_type": "text",
            "text": "分析新易盛",
            "voice_text": "",
            "sender_hash": "local-user",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dry_run": True,
        },
        "股票路由输出": {
            "trace_id": "stock-route-demo-001",
            "reply_text": latest_router.get("reply_text", "研究回复草稿"),
            "need_clarification": latest_router.get("need_clarification", False),
            "data_health": latest_router.get("data_health", {}),
            "real_send": False,
            "trade": False,
            "source_output": latest_router.get("路由结果", {}).get("源输出", ""),
            "error": "",
        },
    }
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "contract_only",
        "契约": contract,
        "样例": sample,
        "实际动作": {
            "导入n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "26n8n路由契约"
    log_dir = root / "04日志" / "n8n路由契约"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "股票企业微信n8n路由契约_最新.json"
    latest_json = output_dir / "股票企业微信n8n路由契约_最新.json"
    md_path = output_dir / "股票企业微信n8n路由契约_最新.md"
    latest_md = output_dir / "股票企业微信n8n路由契约_最新.md"
    log_path = log_dir / "stock-wework-n8n-router-contract-generate-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    markdown = build_markdown(package)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, package)
    print(json.dumps({"模式": package["模式"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
