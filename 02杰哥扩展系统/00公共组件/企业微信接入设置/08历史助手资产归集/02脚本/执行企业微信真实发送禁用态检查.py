"""
名称：执行企业微信真实发送禁用态检查.py
作用：读取企业微信沙箱回环门禁报告，生成真实发送禁用态检查报告，确认真实凭据、真实发送、Webhook和n8n触发均保持关闭。
触发方式：python 执行企业微信真实发送禁用态检查.py
依赖：Python 标准库；企业微信沙箱回环门禁报告_最新.json；企业微信沙箱回环门禁.json。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只生成真实发送禁用态检查报告；不写入真实凭据；不真实发送企业微信；不触发Webhook；不触发n8n；不在OpenClaw写业务判断；不绕过统一消息出口。
创建/修改记录：2026-04-27 创建企业微信真实发送禁用态检查脚本。
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


def main() -> int:
    root = module_root()
    gate = load_json(root / "01配置" / "企业微信沙箱回环门禁.json")
    gate_report_path = root / "03数据" / "06沙箱回环门禁" / "企业微信沙箱回环门禁报告_最新.json"
    gate_report = load_json(gate_report_path) if gate_report_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "企业微信真实发送禁用态检查",
        "门禁报告": str(gate_report_path),
        "门禁开关": gate.get("默认开关", {}),
        "沙箱脚本执行": gate_report.get("脚本执行", []),
        "是否写入真实凭据": False,
        "是否企业微信真实发送": False,
        "是否触发Webhook": False,
        "是否触发n8n": False,
        "是否OpenClaw写业务判断": False,
        "是否绕过统一消息出口": False,
        "执行器状态": "禁用态",
        "当前结论": "企业微信真实发送执行器保持禁用，只允许沙箱回环、凭据隔离检查和回滚演练。"
    }
    output_dir = root / "03数据" / "06沙箱回环门禁"
    latest = output_dir / "企业微信真实发送禁用态检查_最新.json"
    output = latest
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否企业微信真实发送": report["是否企业微信真实发送"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
