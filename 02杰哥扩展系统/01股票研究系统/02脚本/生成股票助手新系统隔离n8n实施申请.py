# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-isolated-n8n-implementation-request.py
Purpose: Generate a no-action implementation request for building an isolated new-system n8n target for the stock assistant.
Trigger: python 生成股票助手新系统隔离n8n实施申请.py
Dependencies: Python standard library; stock n8n target isolation report; isolated n8n implementation request rule JSON.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and config drafts only; writes request materials only under the new stock module data directory; does not start, restart, import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created the isolated n8n implementation request generator.
Marker: stock-assistant-isolated-n8n-implementation-request-generate
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手新系统隔离n8n实施申请",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、申请结论",
        "",
        f"- 是否需要新系统隔离n8n：{report['是否需要新系统隔离n8n']}",
        f"- 是否允许本申请直接启动服务：{report['是否允许本申请直接启动服务']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、目标设计",
        "",
    ]
    for key, value in report["申请目标"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、实施前必须满足", ""])
    for item in report["实施前必须满足"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、本申请禁止动作", ""])
    for key, value in report["本申请禁止动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手新系统隔离n8n实施申请规则.json"
    isolation_path = root / "03数据" / "66n8n目标实例选择与隔离核验" / "股票助手n8n目标实例选择与隔离核验包_最新.json"
    compose_path = v3_root / "01杰哥智能系统" / "01配置" / "docker-compose.v3草案.yml"
    contract_path = v3_root / "01杰哥智能系统" / "01配置" / "n8n接口契约.json"
    rule = load_json(rule_path)
    isolation = load_json(isolation_path)
    contract = load_json(contract_path)
    compose_text = read_text(compose_path)
    needs_isolated_target = isolation.get("是否具备安全导入目标") is not True
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "引用66号核验包": str(isolation_path),
        "申请目标": rule.get("申请目标", {}),
        "实施前必须满足": rule.get("实施前必须满足", []),
        "当前n8n目标隔离结论": isolation.get("当前结论", ""),
        "是否需要新系统隔离n8n": needs_isolated_target,
        "是否允许本申请直接启动服务": False,
        "当前结论": "本申请只把新系统隔离n8n作为下一施工对象登记清楚；不直接启动服务、不导入工作流、不触发真实链路。" if needs_isolated_target else "已存在安全新系统n8n目标；本申请可作为备用说明，后续仍需按未激活导入规则执行。",
        "compose草案摘要": {
            "路径": str(compose_path),
            "存在": bool(compose_text.strip()),
            "包含jiege_v3_n8n": "jiege_v3_n8n" in compose_text,
            "包含28679端口": "28679" in compose_text,
            "包含n8n数据目录": "03数据/n8n" in compose_text or "03数据\\n8n" in compose_text
        },
        "n8n接口契约摘要": {
            "路径": str(contract_path),
            "接管状态": contract.get("接管状态", "未读取到"),
            "允许真实执行": contract.get("允许真实执行", "未读取到")
        },
        "本申请允许动作": rule.get("本申请只允许动作", {}),
        "本申请禁止动作": rule.get("本申请禁止动作", {}),
        "实际动作": {
            "读取66号核验包": True,
            "读取新系统compose草案": True,
            "读取n8n接口契约": True,
            "写入实施申请材料": True,
            "启动n8n服务": False,
            "重启服务": False,
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n工作流": False,
            "写旧系统": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    output_dir = root / "03数据" / "67新系统隔离n8n实施申请"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手新系统隔离n8n实施申请_{stamp}.json"
    latest_json = output_dir / "股票助手新系统隔离n8n实施申请_最新.json"
    output_md = output_dir / f"股票助手新系统隔离n8n实施申请_{stamp}.md"
    latest_md = output_dir / "股票助手新系统隔离n8n实施申请_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否需要新系统隔离n8n": needs_isolated_target, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
