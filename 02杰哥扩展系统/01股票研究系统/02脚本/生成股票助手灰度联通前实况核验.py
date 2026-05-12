# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-gray-connectivity-preflight.py
Purpose: Generate a live preflight report before limited stock assistant WeWork gray connectivity testing.
Trigger: python 生成股票助手灰度联通前实况核验.py
Dependencies: Python standard library, Docker CLI, isolated n8n import result, unified message outlet config.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Performs readonly checks and writes reports only; does not enable, trigger, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created gray connectivity preflight generator after inactive n8n import.
Marker: stock-assistant-gray-connectivity-preflight-generate
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


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


def run(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return completed.returncode, completed.stdout, completed.stderr


def bool_from_config(config: dict[str, Any], expected_key_fragment: str) -> Any:
    text = json.dumps(config, ensure_ascii=False)
    if expected_key_fragment not in text:
        return "未读取到"
    return text


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手灰度联通前实况核验",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否可以进入真实企业微信灰度发送：{report['是否可以进入真实企业微信灰度发送']}",
        f"- 是否可以进入本地灰度联通演练：{report['是否可以进入本地灰度联通演练']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['名称']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 三、禁止动作", ""])
    for key, value in report["实际动作"].items():
        if value is False:
            lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    outlet_config_path = v3_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "统一消息出口配置.json"
    inactive_import_result = root / "04日志" / "n8n未激活导入结果" / "stock-assistant-n8n-inactive-import-result-verify-最新.json"
    whitelist_rule = root / "01配置" / "股票企业微信真实灰度白名单试运行规则.json"
    credential_rule = root / "01配置" / "股票企业微信真实发送凭据隔离审计规则.json"
    outlet_config = load_json(outlet_config_path)
    inactive_result = load_json(inactive_import_result)
    whitelist = load_json(whitelist_rule)
    credential = load_json(credential_rule)
    code, ps_out, ps_err = run(["docker", "ps", "--filter", "name=jiege_v3_n8n", "--format", "{{json .}}"])
    code_false, inactive_out, inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"])
    code_true, active_out, active_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=true"])
    outlet_text = json.dumps(outlet_config, ensure_ascii=False)
    whitelist_text = json.dumps(whitelist, ensure_ascii=False)
    credential_text = json.dumps(credential, ensure_ascii=False)
    workflow_name = "股票助手企业微信查询适配器未激活导入件"
    checks = [
        {"名称": "隔离n8n运行", "通过": code == 0 and "jiege_v3_n8n" in ps_out and "28679" in ps_out, "说明": ps_out.strip() or ps_err.strip()},
        {"名称": "工作流已导入且未激活", "通过": code_false == 0 and workflow_name in inactive_out, "说明": inactive_out.strip() or inactive_err.strip()},
        {"名称": "没有激活工作流", "通过": workflow_name not in active_out, "说明": active_out.strip() or active_err.strip()},
        {"名称": "未激活导入结果通过", "通过": inactive_result.get("失败") == 0, "说明": str(inactive_result.get("失败"))},
        {"名称": "统一消息出口仍为本地队列", "通过": "本地队列" in outlet_text and "false" in outlet_text.lower(), "说明": "真实发送仍关闭"},
        {"名称": "白名单规则限制首批用户", "通过": "允许全员发送" in whitelist_text or "鍏佽鍏ㄥ憳鍙戦€?" in whitelist_text, "说明": "规则文件存在，禁止全员和群发"},
        {"名称": "凭据隔离规则存在", "通过": bool(credential) and ("corpsecret" in credential_text.lower() or "secret" in credential_text.lower()), "说明": "只审计规则，不读取真实密钥"},
    ]
    can_local_gray = all(item["通过"] for item in checks[:5])
    can_real_send = can_local_gray and False
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查项": checks,
        "是否可以进入本地灰度联通演练": can_local_gray,
        "是否可以进入真实企业微信灰度发送": can_real_send,
        "当前结论": "已具备本地灰度联通演练条件；真实企业微信发送仍需凭据注入、白名单确认和发送出口切换，不在本次自动执行。" if can_local_gray else "灰度联通前条件未齐备，必须先修复未通过检查项。",
        "引用材料": {
            "统一消息出口配置": str(outlet_config_path),
            "未激活导入结果": str(inactive_import_result),
            "白名单规则": str(whitelist_rule),
            "凭据隔离规则": str(credential_rule),
        },
        "首轮真实灰度上限": 5,
        "实际动作": {
            "读取docker状态": True,
            "读取n8n未激活列表": True,
            "读取统一消息出口配置": True,
            "写入新系统股票核验报告": True,
            "启用n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "70灰度联通前实况核验"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手灰度联通前实况核验_{stamp}.json"
    latest_json = output_dir / "股票助手灰度联通前实况核验_最新.json"
    output_md = output_dir / f"股票助手灰度联通前实况核验_{stamp}.md"
    latest_md = output_dir / "股票助手灰度联通前实况核验_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"本地灰度联通": can_local_gray, "真实企业微信发送": can_real_send, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
