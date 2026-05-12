# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度白名单试运行包.py
作用：生成股票企业微信真实灰度启用前的白名单草案、试运行用例、合格标准和安全边界报告。
触发方式：python 生成股票企业微信真实灰度白名单试运行包.py
依赖：Python标准库；股票企业微信真实灰度白名单试运行规则.json；股票企业微信真实灰度最终闸口包_最新.json；股票企业微信真实发送凭据隔离审计包_最新.json；股票企业微信真实灰度回滚预案包_最新.json；OpenClaw股票桥接沙盒验收包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度白名单试运行包脚本。
标识：stock-wework-real-gray-whitelist-trial-package-generate
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
        "# 股票企业微信真实灰度白名单试运行包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否满足灰度试运行材料要求：{report['是否满足灰度试运行材料要求']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、白名单草案",
        "",
    ]
    for key, value in report["白名单草案"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、试运行用例", ""])
    for case in report["试运行用例"]:
        lines.append(f"- {case['编号']}｜{case['输入类型']}｜{case['输入内容']}｜{case['合格标准']}")
    lines.extend(["", "## 四、前置条件", ""])
    for key, value in report["前置条件"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度白名单试运行规则.json"
    final_gate_path = root / "03数据" / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json"
    credential_audit_path = root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json"
    rollback_plan_path = root / "03数据" / "41真实灰度回滚预案" / "股票企业微信真实灰度回滚预案包_最新.json"
    sandbox_path = root / "03数据" / "39OpenClaw桥接沙盒验收" / "OpenClaw股票桥接沙盒验收包_最新.json"

    rule = load_json(rule_path)
    final_gate = load_json(final_gate_path)
    credential_audit = load_json(credential_audit_path)
    rollback_plan = load_json(rollback_plan_path)
    sandbox = load_json(sandbox_path)
    whitelist = rule.get("白名单规则", {})
    cases = rule.get("试运行用例", [])

    prerequisites = {
        "真实灰度最终闸口包存在": final_gate_path.exists(),
        "凭据隔离审计通过": credential_audit.get("是否通过凭据隔离审计") is True,
        "回滚预案具备": rollback_plan.get("是否满足灰度前回滚预案要求") is True,
        "OpenClaw桥接沙盒验收包存在": sandbox_path.exists(),
        "真实发送仍未放行": final_gate.get("当前结论", "").find("未放行") >= 0 or credential_audit.get("当前结论", "").find("未放行") >= 0,
    }
    case_types = {item.get("输入类型") for item in cases}
    whitelist_ok = (
        whitelist.get("允许全员发送") is False
        and whitelist.get("禁止群发") is True
        and whitelist.get("禁止外部客户") is True
        and "待人工确认" in str(whitelist.get("默认接收人", ""))
    )
    cases_ok = (
        len(cases) >= 5
        and "文字" in case_types
        and "重庆话语音转写" in case_types
        and "模糊语音转写" in case_types
        and "越权请求" in case_types
    )
    passed = all(prerequisites.values()) and whitelist_ok and cases_ok
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "依赖产物": {
            "真实灰度最终闸口包": str(final_gate_path),
            "凭据隔离审计包": str(credential_audit_path),
            "真实灰度回滚预案包": str(rollback_plan_path),
            "OpenClaw桥接沙盒验收包": str(sandbox_path),
        },
        "前置条件": prerequisites,
        "白名单草案": whitelist,
        "试运行用例": cases,
        "合格标准": rule.get("合格标准", []),
        "是否满足灰度试运行材料要求": passed,
        "当前结论": "白名单和试运行用例已具备，可作为真实灰度前人工确认材料；当前未发送企业微信。" if passed else "白名单或试运行用例不完整，不能进入真实灰度试运行评审。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "42真实灰度白名单试运行"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度白名单试运行包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度白名单试运行包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度白名单试运行包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度白名单试运行包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否满足灰度试运行材料要求": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
