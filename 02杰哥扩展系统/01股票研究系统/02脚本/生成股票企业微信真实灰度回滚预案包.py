# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度回滚预案包.py
作用：生成股票企业微信真实灰度启用前的回滚触发条件、人工边界、退回本地队列和复盘验收预案。
触发方式：python 生成股票企业微信真实灰度回滚预案包.py
依赖：Python标准库；股票企业微信真实灰度回滚预案规则.json；统一消息出口配置.json；股票企业微信真实灰度最终闸口包_最新.json；股票企业微信真实发送凭据隔离审计包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度回滚预案包脚本。
标识：stock-wework-real-gray-rollback-plan-package-generate
"""

from __future__ import annotations

import json
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信真实灰度回滚预案包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否满足灰度前回滚预案要求：{report['是否满足灰度前回滚预案要求']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、回滚触发条件",
        "",
    ]
    for item in report["回滚触发条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、回滚动作清单", ""])
    for item in report["回滚动作清单"]:
        lines.append(f"- {item['动作']}：{item['说明']}")
    lines.extend(["", "## 四、人工确认边界", ""])
    for key, value in report["人工确认边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、验证命令", ""])
    for command in report["验证命令"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## 六、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度回滚预案规则.json"
    final_gate_path = root / "03数据" / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json"
    credential_audit_path = root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json"
    n8n_audit_path = root / "03数据" / "38n8n导入前只读审计" / "股票n8n未激活导入前只读审计包_最新.json"
    outlet_config_path = sys_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "统一消息出口配置.json"

    rule = load_json(rule_path)
    final_gate = load_json(final_gate_path)
    credential_audit = load_json(credential_audit_path)
    n8n_audit = load_json(n8n_audit_path)
    outlet_config = load_json(outlet_config_path)
    strategy = outlet_config.get("出口策略", {})

    prerequisites = {
        "真实灰度最终闸口包存在": final_gate_path.exists(),
        "凭据隔离审计包存在": credential_audit_path.exists(),
        "n8n导入前只读审计包存在": n8n_audit_path.exists(),
        "统一消息出口配置存在": outlet_config_path.exists(),
        "当前仍为本地队列": strategy.get("当前发送模式") == "本地队列",
        "当前真实发送关闭": strategy.get("是否允许真实发送") is False,
        "凭据隔离审计通过": credential_audit.get("是否通过凭据隔离审计") is True,
    }
    rollback_steps = [
        {"动作": "保持或退回本地队列", "说明": "统一消息出口以本地队列为默认安全落点，真实发送异常时先停止继续放行。"},
        {"动作": "保持n8n未激活", "说明": "工作流导入后仍须保持active=false；启用和停用均需人工确认。"},
        {"动作": "隔离待发送队列", "说明": "异常样本只归档复盘，不自动删除，避免经验样本丢失。"},
        {"动作": "复跑凭据隔离审计", "说明": "回滚后重新验证无明文凭据、无真实发送、无正式库写入。"},
        {"动作": "写入进化候选样本", "说明": "将异常现象、原因、处置动作写入进化系统候选样本，后续再归纳提炼。"},
    ]
    verification_commands = [
        r'python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\验证股票企业微信真实发送凭据隔离审计包.py"',
        r'python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\验证股票n8n未激活导入前只读审计包.py"',
        r'python "D:\杰哥智能化系统\00杰哥系统总管\02脚本\验证股票企业微信真实灰度回滚预案包汇总.py"',
    ]
    passed = all(prerequisites.values()) and len(rollback_steps) >= 5 and len(rule.get("回滚触发条件", [])) >= 5
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "依赖产物": {
            "真实灰度最终闸口包": str(final_gate_path),
            "凭据隔离审计包": str(credential_audit_path),
            "n8n导入前只读审计包": str(n8n_audit_path),
            "统一消息出口配置": str(outlet_config_path),
        },
        "前置条件": prerequisites,
        "回滚原则": rule.get("回滚原则", []),
        "回滚触发条件": rule.get("回滚触发条件", []),
        "回滚动作清单": rollback_steps,
        "人工确认边界": {
            "导入n8n": "必须人工确认，不由本预案执行。",
            "启用n8n": "必须人工确认，不由本预案执行。",
            "停止或重启服务": "属于高风险动作，必须停止说明原因。",
            "真实发送企业微信": "必须人工确认，不由本预案执行。",
            "删除或覆盖样本": "禁止自动执行，只能归档复盘。",
        },
        "验证命令": verification_commands,
        "是否满足灰度前回滚预案要求": passed,
        "当前结论": "回滚预案已具备，可作为真实灰度前的安全门禁材料；当前未执行任何真实回滚动作。" if passed else "回滚预案前置条件不完整，不能进入真实灰度评审。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "41真实灰度回滚预案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度回滚预案包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度回滚预案包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度回滚预案包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度回滚预案包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否满足灰度前回滚预案要求": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
