"""
名称：企业微信只读回环预演.py
作用：模拟企业微信入站消息转为标准消息，并生成本地只读响应预演报告。
触发方式：python 企业微信只读回环预演.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只写入本模块03数据/02回环预演；不连接企业微信、不触发n8n、不写统一消息出口正式队列、不真实发送。
创建/修改记录：2026-04-27 创建企业微信只读回环预演脚本。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def message_id(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def run_loopback() -> dict[str, Any]:
    root = module_root()
    config = load_json(root / "01配置" / "企业微信助手配置.json")
    rules = load_json(root / "01配置" / "企业微信只读接入测试规则.json")
    output_dir = root / "03数据" / "02回环预演"
    output_dir.mkdir(parents=True, exist_ok=True)
    switches = config.get("接入开关", {})
    if switches.get("允许连接企业微信") or switches.get("允许发送企业微信") or switches.get("允许触发n8n真实工作流"):
        raise RuntimeError("只读回环预演要求真实连接、真实发送和n8n真实触发全部关闭")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample = dict(rules.get("输入样例", {}))
    sample["时间"] = now
    standard_message = {
        "消息ID": message_id(sample),
        "来源系统": "企业微信助手本地预演",
        "发送人": sample.get("发送人", "模拟用户"),
        "消息类型": sample.get("消息类型", "text"),
        "内容": sample.get("内容", ""),
        "接收时间": now,
        "路由目标": "n8n模拟入口",
        "是否真实发送": False,
    }
    simulated_response = {
        "消息ID": standard_message["消息ID"],
        "响应内容": "本地回环预演成功：消息已完成标准化，但未触发真实企业微信、n8n或统一消息出口正式队列。",
        "发送路径": "本地预演目录",
        "是否写入统一消息出口正式队列": False,
        "是否真实发送": False,
    }
    report = {
        "生成时间": now,
        "测试模式": rules.get("测试模式"),
        "输入样例": sample,
        "标准消息": standard_message,
        "模拟响应": simulated_response,
        "边界状态": {
            "连接企业微信": False,
            "触发n8n真实工作流": False,
            "写入统一消息出口正式队列": False,
            "真实发送企业微信": False,
        },
        "是否通过回环预演": True,
        "安全说明": "本报告只验证消息格式和本地回环，不代表真实企业微信接入已启用。",
    }
    latest = output_dir / "企业微信只读回环预演_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"passed": True, "message_id": standard_message["消息ID"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    run_loopback()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
