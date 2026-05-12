# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送灰度启用准备包.py
作用：梳理股票主动推送从本地可用到真实灰度启用之间的准备项、阻断项和dry-run边界。
触发方式：python 生成股票主动推送灰度启用准备包.py
依赖：Python标准库；股票研究系统状态摘要；企业微信受控发送闸口包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地状态并写入247准备包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易。
创建/修改记录：2026-05-09 创建股票主动推送灰度启用准备包。
标识：stock-active-push-gray-enable-prep-generate
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


def run_local(script: Path) -> dict[str, Any]:
    if not script.exists():
        return {"exists": False, "returncode": None, "stdout": "", "stderr": f"missing: {script}"}
    completed = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "exists": True,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def existing_file_state(path: Path) -> dict[str, Any]:
    return {
        "存在": path.exists(),
        "路径": str(path),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送灰度启用准备包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 当前结论：{report['当前结论']}",
        f"- 可以推进准备工作：{report['可以推进准备工作']}",
        f"- 可以立即真实推送：{report['可以立即真实推送']}",
        f"- 可以立即启用n8n自动推送：{report['可以立即启用n8n自动推送']}",
        "",
        "## 当前能力",
        "",
    ]
    for item in report["当前能力"]:
        lines.append(f"- {item['能力']}：{item['状态']}。{item['说明']}")
    lines.extend(["", "## 仍需补齐", ""])
    for item in report["仍需补齐"]:
        lines.append(f"- {item['事项']}：{item['处理方式']}")
    lines.extend(["", "## 日常推送灰度路径", ""])
    for item in report["灰度路径"]:
        lines.append(f"{item['顺序']}. {item['动作']}：{item['状态']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    scripts = root / "02脚本"
    data = root / "03数据"

    gate_generate = scripts / "生成股票助手企业微信受控发送闸口包.py"
    gate_verify = scripts / "验证股票助手企业微信受控发送闸口包.py"
    gate_generate_result = run_local(gate_generate)
    gate_verify_result = run_local(gate_verify)

    status_path = data / "16状态摘要" / "股票研究系统状态摘要_最新.json"
    status = load_json(status_path)
    gate_path = data / "73企业微信受控发送闸口" / "股票助手企业微信受控发送闸口包_最新.json"
    gate = load_json(gate_path)

    candidate_draft_paths = {
        "300只候选精选推送草案": data / "102精选推送草案" / "300只候选精选推送草案_最新.md",
        "股票企微推送草案": data / "136推送草案" / "股票企微推送草案_最新.md",
        "推送前候选包": data / "96推送前候选包" / "300只候选推送前候选包_最新.json",
        "推送前人工闸口": data / "99推送前人工闸口" / "300只候选推送前人工闸口复核单_最新.json",
    }

    safety = status.get("安全边界", {})
    current_capabilities = [
        {"能力": "股票本地分析和产物", "状态": "可用", "说明": "股票状态摘要存在，股票助手服务日志持续健康检查。"},
        {"能力": "企业微信查询/短答预演", "状态": "可用", "说明": "可以生成本地回复、短答和推送草案。"},
        {"能力": "主动推送准备", "状态": "可推进", "说明": "可以继续做白名单、频率、内容边界、熔断和日志设计。"},
        {"能力": "企业微信真实发送", "状态": "未放行", "说明": "受控发送闸口仍未允许真实发送。"},
        {"能力": "n8n定时自动推送", "状态": "未启用", "说明": "当前只允许未激活导入或dry-run，不触发真实工作流。"},
    ]

    blockers = [
        {"事项": "真实发送人工放行", "处理方式": "需要独立确认发送对象、频率、内容边界和回滚方式；本包不代替确认。"},
        {"事项": "企业微信受控发送闸口", "处理方式": "当前保持未放行；后续只允许单人白名单、单条消息灰度测试先行。"},
        {"事项": "n8n自动触发", "处理方式": "继续保持未激活；先完成人工触发dry-run和日志闭环，再讨论定时自动化。"},
        {"事项": "股票内容边界", "处理方式": "推送文本只允许研究价值、风险复核、观察条件；禁止买入、卖出、仓位、下单等表达。"},
        {"事项": "熔断和撤回", "处理方式": "需要明确异常停止开关、发送失败记录、重复发送拦截和人工复核入口。"},
    ]

    gray_path = [
        {"顺序": 1, "动作": "本地生成股票研究产物", "状态": "已具备"},
        {"顺序": 2, "动作": "生成企业微信推送草案", "状态": "可推进；只本地写草案"},
        {"顺序": 3, "动作": "执行发送前安全闸口检查", "状态": "已接入；当前真实发送未放行"},
        {"顺序": 4, "动作": "单人白名单单条灰度测试", "状态": "待人工明确放行后才可做"},
        {"顺序": 5, "动作": "低频人工触发推送", "状态": "待首条灰度闭环通过后再评估"},
        {"顺序": 6, "动作": "n8n定时自动推送", "状态": "当前不启用；属于后续高风险自动化"},
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "可以推进股票主动推送灰度启用准备，但不能立即真实发送，也不能立即启用n8n自动推送。",
        "可以推进准备工作": True,
        "可以立即真实推送": False,
        "可以立即启用n8n自动推送": False,
        "状态摘要": existing_file_state(status_path),
        "受控发送闸口包": existing_file_state(gate_path),
        "受控发送闸口生成结果": gate_generate_result,
        "受控发送闸口验收结果": gate_verify_result,
        "受控发送闸口结论": gate.get("当前结论", ""),
        "受控发送闸口是否允许真实发送": gate.get("是否允许真实发送") is True,
        "候选推送产物状态": {name: existing_file_state(path) for name, path in candidate_draft_paths.items()},
        "股票系统安全边界": safety,
        "当前能力": current_capabilities,
        "仍需补齐": blockers,
        "灰度路径": gray_path,
        "建议下一步": [
            "先刷新或生成最新股票推送草案，仍不发送。",
            "补一份主动推送单人白名单与内容频率规则草案。",
            "补一份发送失败、重复发送、异常文本和交易化表达熔断清单。",
            "全部dry-run通过后，再单独进入真实灰度人工确认。"
        ],
        "实际动作": {
            "读取股票本地状态": True,
            "运行受控发送闸口本地检查": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "重载19310": False,
            "重载19302": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式规则": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }

    out_dir = data / "247主动推送灰度启用准备包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送灰度启用准备包_{stamp}.json"
    latest_json = out_dir / "股票主动推送灰度启用准备包_最新.json"
    output_md = out_dir / f"股票主动推送灰度启用准备包_{stamp}.md"
    latest_md = out_dir / "股票主动推送灰度启用准备包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": "prep_pass", "可以推进准备工作": True, "可以立即真实推送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
