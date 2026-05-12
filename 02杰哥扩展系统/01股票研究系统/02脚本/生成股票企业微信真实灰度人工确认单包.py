# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度人工确认单包.py
作用：生成股票企业微信真实灰度前必须人工确认的事项清单、放行边界和禁止自动执行声明。
触发方式：python 生成股票企业微信真实灰度人工确认单包.py
依赖：Python标准库；股票企业微信真实灰度人工确认单规则.json；股票企业微信真实灰度最终闸口包_最新.json；股票企业微信真实发送凭据隔离审计包_最新.json；股票企业微信真实灰度回滚预案包_最新.json；股票企业微信真实灰度白名单试运行包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度人工确认单包脚本。
标识：stock-wework-real-gray-human-confirmation-package-generate
"""

from __future__ import annotations

import json
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信真实灰度人工确认单包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备提交人工确认条件：{report['是否具备提交人工确认条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、人工确认事项",
        "",
    ]
    for index, item in enumerate(report["人工确认事项"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 三、放行边界", ""])
    for key, value in report["放行边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、前置材料", ""])
    for key, value in report["前置材料"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度人工确认单规则.json"
    final_gate_path = root / "03数据" / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json"
    credential_audit_path = root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json"
    rollback_plan_path = root / "03数据" / "41真实灰度回滚预案" / "股票企业微信真实灰度回滚预案包_最新.json"
    whitelist_trial_path = root / "03数据" / "42真实灰度白名单试运行" / "股票企业微信真实灰度白名单试运行包_最新.json"

    rule = load_json(rule_path)
    final_gate = load_json(final_gate_path)
    credential_audit = load_json(credential_audit_path)
    rollback_plan = load_json(rollback_plan_path)
    whitelist_trial = load_json(whitelist_trial_path)
    prerequisites = {
        "真实灰度最终闸口包存在": final_gate_path.exists(),
        "凭据隔离审计通过": credential_audit.get("是否通过凭据隔离审计") is True,
        "回滚预案具备": rollback_plan.get("是否满足灰度前回滚预案要求") is True,
        "白名单试运行材料具备": whitelist_trial.get("是否满足灰度试运行材料要求") is True,
        "真实发送仍未放行": final_gate.get("当前结论", "").find("未放行") >= 0 or credential_audit.get("当前结论", "").find("未放行") >= 0,
    }
    release_boundary = rule.get("放行边界", {})
    boundary_ok = (
        release_boundary.get("允许提交人工确认") is True
        and release_boundary.get("允许自动导入n8n") is False
        and release_boundary.get("允许自动启用n8n") is False
        and release_boundary.get("允许自动发送企业微信") is False
        and release_boundary.get("允许自动交易") is False
    )
    passed = all(prerequisites.values()) and boundary_ok and len(rule.get("人工确认事项", [])) >= 7
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "前置材料": {
            "真实灰度最终闸口包": str(final_gate_path),
            "凭据隔离审计包": str(credential_audit_path),
            "真实灰度回滚预案包": str(rollback_plan_path),
            "真实灰度白名单试运行包": str(whitelist_trial_path),
        },
        "前置条件": prerequisites,
        "人工确认事项": rule.get("人工确认事项", []),
        "放行边界": release_boundary,
        "是否具备提交人工确认条件": passed,
        "当前结论": "人工确认单已具备，可作为真实灰度前提交给用户确认的唯一放行清单；当前未执行任何真实动作。" if passed else "人工确认单前置材料不足，不能提交真实灰度确认。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "43真实灰度人工确认单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度人工确认单包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度人工确认单包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度人工确认单包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度人工确认单包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备提交人工确认条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
