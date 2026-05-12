# -*- coding: utf-8 -*-
"""生成低风险自主命令白名单与红线静态扫描包。

本脚本只写入本包 JSON/MD 材料，不执行候选命令，不调用外部接口，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101低风险自主命令白名单与红线静态扫描包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险自主命令白名单与红线静态扫描包验收"

WHITELIST_JSON = DATA_DIR / "低风险自主命令白名单_最新.json"
WHITELIST_MD = DATA_DIR / "低风险自主命令白名单_最新.md"
REDLINE_JSON = DATA_DIR / "低风险自主命令红线静态扫描规则_最新.json"
REDLINE_MD = DATA_DIR / "低风险自主命令红线静态扫描规则_最新.md"
SAMPLE_COMMANDS_JSON = DATA_DIR / "本包样例候选命令_最新.json"
SAMPLE_COMMANDS_MD = DATA_DIR / "本包样例候选命令_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险自主命令白名单与红线静态扫描包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险自主命令白名单与红线静态扫描包_最新.md"
GEN_LOG = LOG_DIR / "low-risk-autonomous-command-whitelist-redline-scan-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "real_wecom_send": False,
        "connect_n8n": False,
        "connect_broker": False,
        "trade_order": False,
        "login_tax_bureau": False,
        "connect_finance_tax_software": False,
        "real_render_publish": False,
        "write_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
    }


def build_whitelist(generated_at: str) -> dict[str, Any]:
    allowed_script_examples = [
        str(SCRIPT_DIR / "验证日常可用交付版一键只读总回归.py"),
        str(SCRIPT_DIR / "验证低风险自主任务本地只读调度预演包.py"),
        str(SCRIPT_DIR / "生成日常可用版自主巡检快照.py"),
        str(SCRIPT_DIR / "生成日常可用交付版状态包.py"),
    ]
    return {
        "name": "低风险自主命令白名单",
        "generated_at": generated_at,
        "scope": "static_draft_command_text_only",
        "default_decision": "deny",
        "allowed_command_families": [
            {
                "id": "python_readonly_acceptance_script",
                "decision": "allow",
                "description": "允许 Python 启动本地只读验收脚本，脚本名必须以 验证 或 只读验证 开头。",
                "command_prefixes": ["python", "py", "python3"],
                "script_dir": str(SCRIPT_DIR),
                "filename_rules": ["验证*.py", "只读验证*.py"],
                "must_keep_flags": safety_flags(),
            },
            {
                "id": "python_snapshot_generator",
                "decision": "allow",
                "description": "允许 Python 启动本地快照生成脚本，脚本名必须以 生成 开头且包含 快照。",
                "command_prefixes": ["python", "py", "python3"],
                "script_dir": str(SCRIPT_DIR),
                "filename_rules": ["生成*快照*.py"],
                "must_keep_flags": safety_flags(),
            },
            {
                "id": "python_status_package_generator",
                "decision": "allow",
                "description": "允许 Python 启动本地状态包生成脚本，脚本名必须以 生成 开头且包含 状态包。",
                "command_prefixes": ["python", "py", "python3"],
                "script_dir": str(SCRIPT_DIR),
                "filename_rules": ["生成*状态包*.py"],
                "must_keep_flags": safety_flags(),
            },
        ],
        "explicit_denies": [
            "Start-Process 服务重载或后台启动",
            "企业微信真实发送",
            "n8n/webhook/外部 HTTP 接口",
            "券商连接、交易、下单",
            "税局登录",
            "财税软件连接",
            "真实渲染发布",
            "正式规则写入或自动转正式规则",
            "总管面板修改",
            "一键接续包修改",
        ],
        "allowed_script_examples": allowed_script_examples,
        "hard_red_line_confirmation": safety_flags(),
    }


def build_redline_rules(generated_at: str) -> dict[str, Any]:
    return {
        "name": "低风险自主命令红线静态扫描规则",
        "generated_at": generated_at,
        "scope": "scan_draft_command_text_do_not_execute",
        "violation_policy": "any_hit_blocks_command",
        "redline_terms": [
            "Start-Process",
            "Restart-Service",
            "Stop-Service",
            "Start-Service",
            "Reload-Service",
            "iisreset",
            "nssm restart",
            "pm2 restart",
            "docker restart",
            "docker compose restart",
            "systemctl",
            "net stop",
            "net start",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "curl ",
            "wget ",
            "requests.",
            "http://",
            "https://",
            "webhook",
            "n8n",
            "qyapi.weixin.qq.com",
            "api.weixin.qq.com",
            "企业微信真实发送",
            "企业微信发送",
            "send_wecom",
            "wecom",
            "券商",
            "broker",
            "交易",
            "trade",
            "下单",
            "order_submit",
            "税局",
            "电子税务局",
            "tax bureau",
            "财税软件",
            "真实渲染发布",
            "publish",
            "自动转正式规则",
            "写入正式规则",
            "正式规则写入",
        ],
        "path_redlines": [
            "总管面板",
            "一键接续包",
            "正式规则",
            "03数据\\08规则沉淀",
            "03数据\\30最终规则封版冻结包",
        ],
        "port_reload_redlines": [
            ":5678",
            "--port 5678",
            "localhost:5678",
            "127.0.0.1:5678",
            "重载端口",
            "reload port",
            "restart port",
        ],
        "external_interface_redlines": [
            "http://",
            "https://",
            "webhook",
            "api.",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "curl ",
            "wget ",
            "requests.",
            "socket.",
            "n8n",
            "qyapi.weixin.qq.com",
            "api.weixin.qq.com",
        ],
        "command_shape_denies": [
            "管道符 |",
            "重定向 > 或 >>",
            "命令串联 && 或 ;",
            "PowerShell 后台任务",
            "计划任务注册",
            "服务启动/停止/重启",
        ],
        "hard_red_line_confirmation": safety_flags(),
    }


def build_sample_commands(generated_at: str) -> dict[str, Any]:
    samples = [
        {
            "id": "CMD-SAMPLE-096-VERIFY",
            "source_hint": "96低风险自主任务本地只读调度预演包",
            "category": "python_readonly_acceptance_script",
            "draft_command": f'python "{SCRIPT_DIR / "验证低风险自主任务本地只读调度预演包.py"}"',
            "expected_decision": "allow",
        },
        {
            "id": "CMD-SAMPLE-097-VERIFY",
            "source_hint": "97低风险自主任务失败暂停与恢复演练包",
            "category": "python_readonly_acceptance_script",
            "draft_command": f'python "{SCRIPT_DIR / "验证低风险自主任务失败暂停与恢复演练包.py"}"',
            "expected_decision": "allow",
        },
        {
            "id": "CMD-SAMPLE-099-VERIFY",
            "source_hint": "99稳定交付版本地试运行达标复核与签收完成包",
            "category": "python_readonly_acceptance_script",
            "draft_command": f'python "{SCRIPT_DIR / "验证稳定交付版本地试运行达标复核与签收完成包.py"}"',
            "expected_decision": "allow",
        },
        {
            "id": "CMD-SAMPLE-100-VERIFY",
            "source_hint": "100稳定版样本等待期低风险保活巡检包",
            "category": "python_readonly_acceptance_script",
            "draft_command": f'python "{SCRIPT_DIR / "验证稳定版样本等待期低风险保活巡检包.py"}"',
            "expected_decision": "allow",
        },
        {
            "id": "CMD-SAMPLE-SNAPSHOT",
            "source_hint": "本包内样例命令",
            "category": "python_snapshot_generator",
            "draft_command": f'python "{SCRIPT_DIR / "生成日常可用版自主巡检快照.py"}"',
            "expected_decision": "allow",
        },
        {
            "id": "CMD-SAMPLE-STATUS",
            "source_hint": "本包内样例命令",
            "category": "python_status_package_generator",
            "draft_command": f'python "{SCRIPT_DIR / "生成日常可用交付版状态包.py"}"',
            "expected_decision": "allow",
        },
    ]
    return {
        "name": "本包样例候选命令",
        "generated_at": generated_at,
        "source_strategy": "scan_local_safe_samples_referencing_99_100_96_97_packages",
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "candidate_count": len(samples),
        "candidates": samples,
    }


def whitelist_md(whitelist: dict[str, Any]) -> str:
    families = "\n".join(
        f"- {item['id']}: {item['description']}" for item in whitelist["allowed_command_families"]
    )
    denies = "\n".join(f"- {item}" for item in whitelist["explicit_denies"])
    examples = "\n".join(f"- `{item}`" for item in whitelist["allowed_script_examples"])
    return "\n".join(
        [
            "# 低风险自主命令白名单",
            "",
            f"- 生成时间: {whitelist['generated_at']}",
            "- 范围: 仅扫描草案命令文本，默认拒绝。",
            "- 允许: Python 本地只读验收脚本、快照生成脚本、状态包生成脚本。",
            "",
            "## 允许族",
            families,
            "",
            "## 明确禁止",
            denies,
            "",
            "## 允许脚本示例",
            examples,
        ]
    )


def redline_md(rules: dict[str, Any]) -> str:
    sections = []
    for key in ["redline_terms", "path_redlines", "port_reload_redlines", "external_interface_redlines", "command_shape_denies"]:
        rows = "\n".join(f"- `{item}`" for item in rules[key])
        sections.extend([f"## {key}", rows, ""])
    return "\n".join(
        [
            "# 低风险自主命令红线静态扫描规则",
            "",
            f"- 生成时间: {rules['generated_at']}",
            "- 策略: 任一命中即阻断候选命令。",
            "- 注意: 只扫描草案命令文本，不执行候选命令。",
            "",
            *sections,
        ]
    )


def sample_commands_md(samples: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['source_hint']} | {item['category']} | `{item['draft_command']}` |"
        for item in samples["candidates"]
    ]
    return "\n".join(
        [
            "# 本包样例候选命令",
            "",
            f"- 生成时间: {samples['generated_at']}",
            f"- candidate_count: {samples['candidate_count']}",
            "- commands_executed: false",
            "",
            "| id | source | category | draft_command |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    outputs = "\n".join(f"- {key}: `{value}`" for key, value in package["outputs"].items())
    return "\n".join(
        [
            "# 低风险自主命令白名单与红线静态扫描包",
            "",
            f"- 生成时间: {package['generated_at']}",
            "- 状态: ready_for_static_scan",
            "- commands_executed: false",
            "- external_call: false",
            "- reload_service: false",
            "",
            "## 产物",
            outputs,
        ]
    )


def main() -> int:
    generated_at = now()
    whitelist = build_whitelist(generated_at)
    redline_rules = build_redline_rules(generated_at)
    sample_commands = build_sample_commands(generated_at)
    package = {
        "name": "低风险自主命令白名单与红线静态扫描包",
        "generated_at": generated_at,
        "status": "ready_for_static_scan",
        "commands_executed": False,
        "external_call": False,
        "reload_service": False,
        "violation_count": 0,
        "hard_red_line_confirmation": safety_flags(),
        "outputs": {
            "whitelist_json": str(WHITELIST_JSON),
            "whitelist_md": str(WHITELIST_MD),
            "redline_json": str(REDLINE_JSON),
            "redline_md": str(REDLINE_MD),
            "sample_commands_json": str(SAMPLE_COMMANDS_JSON),
            "sample_commands_md": str(SAMPLE_COMMANDS_MD),
            "package_json": str(PACKAGE_JSON),
            "package_md": str(PACKAGE_MD),
        },
    }

    write_json(WHITELIST_JSON, whitelist)
    write_text(WHITELIST_MD, whitelist_md(whitelist))
    write_json(REDLINE_JSON, redline_rules)
    write_text(REDLINE_MD, redline_md(redline_rules))
    write_json(SAMPLE_COMMANDS_JSON, sample_commands)
    write_text(SAMPLE_COMMANDS_MD, sample_commands_md(sample_commands))
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))
    write_json(GEN_LOG, package)
    print(json.dumps({"pass": True, "error_count": 0, "output": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
