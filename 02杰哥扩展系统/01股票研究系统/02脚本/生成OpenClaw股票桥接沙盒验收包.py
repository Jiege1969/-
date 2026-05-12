# -*- coding: utf-8 -*-
"""
名称：生成OpenClaw股票桥接沙盒验收包.py
作用：模拟股票企业微信消息经OpenClaw桥接契约转为n8n输入，再调用股票统一路由禁用态和统一消息出口禁用态生成沙盒验收包。
触发方式：python 生成OpenClaw股票桥接沙盒验收包.py
依赖：Python标准库；OpenClaw股票桥接沙盒验收规则.json；执行企业微信股票消息统一路由禁用态.py；生成股票统一消息出口禁用态回复包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只做本地沙盒模拟并写入股票模块03数据目录；不调用真实OpenClaw；不调用n8n API；不导入n8n；不启用Webhook；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建OpenClaw股票桥接沙盒验收包脚本。
标识：stock-openclaw-bridge-sandbox-acceptance-package-generate
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(script: Path, args: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    return {"返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def build_n8n_input(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "gateway": "openclaw",
        "business": "stock",
        "mode": "sandbox_disabled",
        "payload": message,
        "safety": {
            "real_send": False,
            "trade": False,
            "write_official_db": False,
            "write_old_system": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenClaw股票桥接沙盒验收包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否通过沙盒验收：{report['是否通过沙盒验收']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、沙盒输入",
        "",
        f"```json\n{json.dumps(report['沙盒输入'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## 三、n8n标准输入",
        "",
        f"```json\n{json.dumps(report['n8n标准输入'], ensure_ascii=False, indent=2)}\n```",
        "",
        "## 四、脚本运行",
        "",
        f"- 统一路由返回码：{report['统一路由运行'].get('返回码')}",
        f"- 统一出口返回码：{report['统一出口运行'].get('返回码')}",
        "",
        "## 五、输出文件",
        "",
        f"- 统一路由最新：{report['统一路由最新']}",
        f"- 统一出口最新：{report['统一出口最新']}",
        "",
        "## 六、实际动作",
        "",
    ]
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "OpenClaw股票桥接沙盒验收规则.json"
    rule = load_json(rule_path)
    message = dict(rule.get("沙盒输入", {}))
    message["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n8n_input = build_n8n_input(message)

    router_script = root / "02脚本" / "执行企业微信股票消息统一路由禁用态.py"
    outlet_script = root / "02脚本" / "生成股票统一消息出口禁用态回复包.py"
    router_run = run_script(router_script, ["--message-type", message.get("message_type", "text"), "--text", message.get("text", "分析新易盛"), "--sender", message.get("sender", "sandbox")])
    outlet_run = run_script(outlet_script, [])
    router_latest = root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json"
    outlet_latest = root / "03数据" / "34统一消息出口禁用态" / "股票统一消息出口禁用态回复包_最新.json"
    router_payload = load_json(router_latest)
    outlet_payload = load_json(outlet_latest)
    passed = (
        n8n_input.get("gateway") == "openclaw"
        and n8n_input.get("business") == "stock"
        and n8n_input.get("safety", {}).get("real_send") is False
        and n8n_input.get("safety", {}).get("trade") is False
        and router_run.get("返回码") == 0
        and bool(router_payload.get("reply_text"))
        and outlet_run.get("返回码") == 0
        and outlet_payload.get("real_send") is False
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "沙盒链路": rule.get("沙盒链路", []),
        "验收标准": rule.get("验收标准", []),
        "沙盒输入": message,
        "n8n标准输入": n8n_input,
        "统一路由运行": router_run,
        "统一出口运行": outlet_run,
        "统一路由最新": str(router_latest),
        "统一出口最新": str(outlet_latest),
        "是否通过沙盒验收": passed,
        "当前结论": "OpenClaw股票桥接沙盒链路通过，可作为真实桥接前的本地验收材料；当前未调用真实OpenClaw、未触发n8n、未发送企业微信。" if passed else "OpenClaw股票桥接沙盒链路存在失败项，不能进入真实桥接评审。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "39OpenClaw桥接沙盒验收"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"OpenClaw股票桥接沙盒验收包_{stamp}.json"
    latest_json = output_dir / "OpenClaw股票桥接沙盒验收包_最新.json"
    output_md = output_dir / f"OpenClaw股票桥接沙盒验收包_{stamp}.md"
    latest_md = output_dir / "OpenClaw股票桥接沙盒验收包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否通过沙盒验收": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
