# -*- coding: utf-8 -*-
"""
名称：生成股票助手n8n未激活导入人工确认回执模板.py
作用：生成股票助手n8n未激活导入前的人工确认回执模板，明确有效确认文本、无效确认示例、确认范围和仍禁止事项。
触发方式：python 生成股票助手n8n未激活导入人工确认回执模板.py
依赖：Python标准库；股票助手n8n未激活导入人工确认回执模板规则.json；股票助手n8n未激活导入申请单_最新.json；股票助手n8n未激活导入执行前只读核验包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不导入n8n；不启用n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手n8n未激活导入人工确认回执模板脚本。
标识：stock-assistant-n8n-inactive-import-human-confirmation-receipt-template-generate
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


def blank_receipt(fields: list[str]) -> dict[str, str]:
    return {field: "" for field in fields}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手n8n未激活导入人工确认回执模板",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、模板结论",
        "",
        f"- 是否具备人工确认回执模板条件：{report['是否具备人工确认回执模板条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、有效确认文本",
        "",
        report["有效确认文本"],
        "",
        "## 三、无效确认示例",
        "",
    ]
    for item in report["无效确认示例"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、回执字段", ""])
    for key, value in report["回执空白模板"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、前置判定", ""])
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 六、仍禁止事项", ""])
    for item in report["仍禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手n8n未激活导入人工确认回执模板规则.json"
    paths = {
        "n8n未激活导入申请单": root / "03数据" / "63n8n未激活导入申请单" / "股票助手n8n未激活导入申请单_最新.json",
        "n8n未激活导入执行前只读核验包": root / "03数据" / "64n8n未激活导入执行前只读核验" / "股票助手n8n未激活导入执行前只读核验包_最新.json",
    }
    rule = load_json(rule_path)
    request = load_json(paths["n8n未激活导入申请单"])
    precheck = load_json(paths["n8n未激活导入执行前只读核验包"])
    actions = rule.get("安全边界", {})
    judgement = {
        "n8n未激活导入申请单通过": request.get("是否具备n8n未激活导入申请条件") is True,
        "执行前只读核验通过": precheck.get("是否具备执行前只读核验条件") is True,
        "有效确认文本存在": bool(rule.get("有效确认文本")),
        "无效确认示例完整": len(rule.get("无效确认示例", [])) >= 6,
        "回执字段完整": len(rule.get("回执字段", [])) >= 12,
        "仍禁止事项完整": len(rule.get("仍禁止事项", [])) >= 8,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "确认原则": rule.get("确认原则", []),
        "前置判定": judgement,
        "有效确认文本": rule.get("有效确认文本", ""),
        "无效确认示例": rule.get("无效确认示例", []),
        "回执空白模板": blank_receipt(rule.get("回执字段", [])),
        "仍禁止事项": rule.get("仍禁止事项", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备人工确认回执模板条件": passed,
        "当前结论": "n8n未激活导入人工确认回执模板已具备；当前只是模板，未代表用户确认，未执行任何真实动作。" if passed else "n8n未激活导入人工确认回执模板前置材料不完整，不能作为确认依据。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "65n8n未激活导入人工确认回执模板"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n未激活导入人工确认回执模板_{stamp}.json"
    latest_json = output_dir / "股票助手n8n未激活导入人工确认回执模板_最新.json"
    output_md = output_dir / f"股票助手n8n未激活导入人工确认回执模板_{stamp}.md"
    latest_md = output_dir / "股票助手n8n未激活导入人工确认回执模板_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备人工确认回执模板条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
