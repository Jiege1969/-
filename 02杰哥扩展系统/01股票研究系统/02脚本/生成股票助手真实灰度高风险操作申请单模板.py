# -*- coding: utf-8 -*-
"""
名称：生成股票助手真实灰度高风险操作申请单模板.py
作用：生成股票助手真实灰度阶段高风险操作申请单模板，固化申请字段、评估项、停止条件、回滚要求和禁止事项。
触发方式：python 生成股票助手真实灰度高风险操作申请单模板.py
依赖：Python标准库；股票助手真实灰度高风险操作申请单模板规则.json；股票助手真实灰度前用户检查清单_最新.json；股票助手真实灰度放行前最终只读总包_最新.json；股票助手真实灰度人工放行确认书模板_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手真实灰度高风险操作申请单模板脚本。
标识：stock-assistant-real-gray-high-risk-operation-request-template-generate
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


def blank_request(fields: list[str], operation_type: str) -> dict[str, str]:
    row = {field: "" for field in fields}
    row["申请操作类型"] = operation_type
    row["用户确认意见"] = "未确认"
    return row


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手真实灰度高风险操作申请单模板",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、模板结论",
        "",
        f"- 是否具备高风险操作申请单模板条件：{report['是否具备高风险操作申请单模板条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、高风险操作类型", ""])
    for item in report["高风险操作类型"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、申请单空白模板", ""])
    for item in report["申请单空白模板"]:
        lines.append(f"### {item['申请操作类型']}")
        for key, value in item.items():
            lines.append(f"- {key}：{value}")
        lines.append("")
    lines.extend(["## 五、必须评估项", ""])
    for item in report["必须评估项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、默认停止条件", ""])
    for item in report["默认停止条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、仍禁止事项", ""])
    for item in report["仍禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 八、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手真实灰度高风险操作申请单模板规则.json"
    paths = {
        "真实灰度前用户检查清单": root / "03数据" / "61真实灰度前用户检查清单" / "股票助手真实灰度前用户检查清单_最新.json",
        "真实灰度放行前最终只读总包": root / "03数据" / "60真实灰度放行前最终只读总包" / "股票助手真实灰度放行前最终只读总包_最新.json",
        "真实灰度人工放行确认书模板": root / "03数据" / "59真实灰度人工放行确认书模板" / "股票助手真实灰度人工放行确认书模板_最新.json",
    }
    rule = load_json(rule_path)
    loaded = {name: load_json(path) for name, path in paths.items()}
    actions = rule.get("安全边界", {})
    operation_types = rule.get("高风险操作类型", [])
    fields = rule.get("申请字段", [])
    judgement = {
        "用户检查清单通过": loaded["真实灰度前用户检查清单"].get("是否具备用户检查清单条件") is True,
        "最终只读总包通过": loaded["真实灰度放行前最终只读总包"].get("是否具备放行前最终只读总包条件") is True,
        "人工放行确认书模板通过": loaded["真实灰度人工放行确认书模板"].get("是否具备人工放行确认书模板条件") is True,
        "高风险操作类型完整": len(operation_types) >= 6,
        "申请字段完整": len(fields) >= 14,
        "必须评估项完整": len(rule.get("必须评估项", [])) >= 8,
        "默认停止条件完整": len(rule.get("默认停止条件", [])) >= 7,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "申请原则": rule.get("申请原则", []),
        "前置判定": judgement,
        "高风险操作类型": operation_types,
        "申请字段": fields,
        "申请单空白模板": [blank_request(fields, operation_type) for operation_type in operation_types],
        "必须评估项": rule.get("必须评估项", []),
        "默认停止条件": rule.get("默认停止条件", []),
        "仍禁止事项": rule.get("仍禁止事项", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备高风险操作申请单模板条件": passed,
        "当前结论": "真实灰度高风险操作申请单模板已具备；当前仅生成申请材料，不执行任何高风险动作。" if passed else "真实灰度高风险操作申请单模板前置材料不完整，不能作为申请依据。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "62真实灰度高风险操作申请单模板"
    latest_json = output_dir / "股票助手真实灰度高风险操作申请单模板_最新.json"
    latest_md = output_dir / "股票助手真实灰度高风险操作申请单模板_最新.md"
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备高风险操作申请单模板条件": passed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
