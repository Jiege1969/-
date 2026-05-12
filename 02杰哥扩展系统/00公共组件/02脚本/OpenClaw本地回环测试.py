"""
名称：OpenClaw本地回环测试.py
作用：模拟企业微信消息经 OpenClaw 转换为标准请求，再将模拟响应交给统一消息出口形成本地回环。
触发方式：python OpenClaw本地回环测试.py --self-test
依赖：Python 标准库；同目录公共组件脚本 统一消息出口.py。
所属系统：02杰哥扩展系统/00公共组件
安全边界：只做本地回环测试，不连接企业微信，不调用 n8n，不发送真实消息，不写业务判断逻辑。
创建/修改记录：2026-04-26 创建 OpenClaw 边缘网关本地回环测试脚本。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def contract_path() -> Path:
    return module_root() / "01配置" / "OpenClaw边缘网关契约.json"


def loopback_dir() -> Path:
    target = module_root() / "03数据" / "03OpenClaw回环测试"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_contract() -> dict[str, Any]:
    return json.loads(contract_path().read_text(encoding="utf-8"))


def load_message_outlet() -> Any:
    script_path = module_root() / "02脚本" / "统一消息出口.py"
    spec = importlib.util.spec_from_file_location("message_outlet", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("统一消息出口脚本加载失败")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_sample_wecom_message() -> dict[str, Any]:
    return {
        "消息ID": str(uuid.uuid4()),
        "发送人": "local-test-user",
        "会话ID": "local-loopback",
        "消息类型": "text",
        "文本内容": "请帮我检查今天系统状态",
        "接收时间": now_text(),
    }


def normalize_to_standard_request(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "请求ID": message.get("消息ID") or str(uuid.uuid4()),
        "来源渠道": "企业微信",
        "来源系统": "OpenClaw边缘网关",
        "用户标识": message.get("发送人", ""),
        "会话ID": message.get("会话ID", ""),
        "用户输入": message.get("文本内容", ""),
        "原始消息": message,
        "风险等级": "低",
        "是否人工确认": False,
    }


def build_mock_n8n_response(request_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "请求ID": request_payload.get("请求ID"),
        "状态": "成功",
        "回复标题": "OpenClaw本地回环测试",
        "回复内容": "本地回环链路已完成：企微模拟消息 -> 标准请求 -> 模拟响应 -> 统一消息出口。",
        "优先级": "低",
        "是否需要人工复核": False,
    }


def run_loopback() -> dict[str, Any]:
    contract = load_contract()
    message = build_sample_wecom_message()
    request_payload = normalize_to_standard_request(message)
    response_payload = build_mock_n8n_response(request_payload)
    outlet = load_message_outlet()
    queued = outlet.enqueue_message(
        source_system="OpenClaw边缘网关",
        business_type="本地回环测试",
        priority=response_payload["优先级"],
        title=response_payload["回复标题"],
        content=response_payload["回复内容"],
    )
    merged = outlet.build_merged_message(limit=10)

    report = {
        "测试时间": now_text(),
        "契约状态": contract.get("状态"),
        "测试模式": contract.get("测试策略", {}).get("当前模式"),
        "是否连接企业微信": False,
        "是否调用n8n": False,
        "是否真实发送": False,
        "原始消息": message,
        "标准请求": request_payload,
        "模拟响应": response_payload,
        "入队消息ID": queued.get("消息ID"),
        "合并消息数量": merged.get("消息数量"),
    }
    output = loopback_dir() / f"OpenClaw回环测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = loopback_dir() / "OpenClaw回环测试_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = run_loopback()
    if args.self_test:
        summary = {
            "测试模式": report.get("测试模式"),
            "是否连接企业微信": report.get("是否连接企业微信"),
            "是否调用n8n": report.get("是否调用n8n"),
            "是否真实发送": report.get("是否真实发送"),
            "入队消息ID": report.get("入队消息ID"),
            "合并消息数量": report.get("合并消息数量"),
        }
        print(json.dumps(summary, ensure_ascii=True))
    else:
        print(json.dumps(report, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
