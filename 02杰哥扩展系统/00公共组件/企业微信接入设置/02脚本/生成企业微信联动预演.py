"""
名称：生成企业微信联动预演.py
作用：串联企业微信本地消息、OpenClaw标准化、n8n草案、智能体模拟响应和统一消息出口预演。
触发方式：python 生成企业微信联动预演.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只生成本地联动预演报告；不导入n8n、不连接企业微信、不写统一消息出口正式队列、不真实发送。
创建/修改记录：2026-04-27 创建企业微信联动预演脚本。
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_workflow_draft(root: Path) -> Path:
    latest = root / "03数据" / "03工作流草案" / "企业微信n8n工作流草案_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "生成企业微信n8n工作流草案.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def stable_id(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_link_preview() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "企业微信n8n联动规则.json")
    readonly_rules = load_json(root / "01配置" / "企业微信只读接入测试规则.json")
    workflow_path = ensure_workflow_draft(root)
    workflow = load_json(workflow_path)
    output_dir = root / "03数据" / "04联动预演"
    output_dir.mkdir(parents=True, exist_ok=True)
    switches = rules.get("开关", {})
    if switches.get("允许导入n8n") or switches.get("允许连接企业微信") or switches.get("允许真实发送"):
        raise RuntimeError("联动预演阶段禁止导入n8n、连接企业微信或真实发送")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inbound = dict(readonly_rules.get("输入样例", {}))
    inbound["时间"] = now
    standard_request = {
        "请求ID": stable_id(inbound),
        "来源渠道": "企业微信模拟",
        "来源系统": "OpenClaw本地预演",
        "用户标识": inbound.get("发送人", "模拟用户"),
        "会话ID": "local-loopback",
        "用户输入": inbound.get("内容", ""),
        "原始消息": inbound,
        "风险等级": "低",
        "是否人工确认": True,
    }
    simulated_agent_response = {
        "请求ID": standard_request["请求ID"],
        "状态": "模拟成功",
        "回复标题": "企业微信助手本地联动预演",
        "回复内容": "标准消息已完成OpenClaw映射、n8n检查项读取和统一消息出口预演；n8n检查项可读，真实触发关闭，未触发真实系统。",
        "优先级": "低",
        "是否需要人工复核": True,
    }
    outlet_preview = {
        "消息ID": stable_id(simulated_agent_response),
        "来源系统": "00公共组件/企业微信接入设置",
        "业务类型": "企业微信本地联动预演",
        "优先级": simulated_agent_response["优先级"],
        "标题": simulated_agent_response["回复标题"],
        "内容": simulated_agent_response["回复内容"],
        "创建时间": now,
        "发送状态": "本地预演未发送",
        "是否写入正式队列": False,
        "是否真实发送": False,
    }
    report = {
        "生成时间": now,
        "工作流草案来源": str(workflow_path),
        "工作流节点数量": workflow.get("节点数量"),
        "联动链路": rules.get("联动链路", []),
        "OpenClaw标准请求": standard_request,
        "n8n检查项": workflow.get("工作流草案", {}).get("field_mapping", {}),
        "智能体模拟响应": simulated_agent_response,
        "统一消息出口预演": outlet_preview,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否连接企业微信": False,
        "是否写入统一消息出口正式队列": False,
        "是否真实发送": False,
        "n8n口径": "检查项可读，真实触发关闭",
        "安全说明": "联动预演只验证字段映射和链路顺序；n8n检查项可读，真实触发关闭，不触发真实外部系统。",
    }
    latest = output_dir / "企业微信联动预演_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"workflow_nodes": workflow.get("节点数量"), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_link_preview()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
