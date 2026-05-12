# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付提交包.py
作用：汇总股票助手交付前最终自检、交付候选总包、核心入口和用户确认事项，生成提交用户阅读确认的本地交付提交包。
触发方式：python 生成股票助手交付提交包.py
依赖：Python标准库；股票助手交付提交包规则.json；股票助手交付前最终自检包_最新.json；股票助手交付候选总包_最新.json；进度回答标准.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付提交包脚本。
标识：stock-assistant-delivery-submit-package-generate
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


def stock_progress(answer_standard: dict[str, Any]) -> dict[str, Any]:
    for item in answer_standard.get("重点子系统", []):
        if item.get("子系统") == "股票分析系统":
            return item
    return {}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手交付提交包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、提交结论",
        "",
        f"- 是否具备提交用户阅读确认条件：{report['是否具备提交用户阅读确认条件']}",
        f"- 当前股票系统进度：{report['股票系统进度'].get('当前进度', '')}",
        f"- 可交付使用还需有效工作时间：{report['股票系统进度'].get('可交付使用还需有效工作时间', '')}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、提交判定",
        "",
    ]
    for key, value in report["提交判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、提交材料入口", ""])
    for item in report["提交材料入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 四、需要用户确认事项", ""])
    for item in report["提交给用户确认事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、仍未放行边界", ""])
    for item in report["仍未放行边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    manager = sys_root / "00杰哥系统总管"
    rule_path = root / "01配置" / "股票助手交付提交包规则.json"
    paths = {
        "最终自检包": root / "03数据" / "53交付前最终自检" / "股票助手交付前最终自检包_最新.json",
        "交付候选总包": root / "03数据" / "52交付候选总包" / "股票助手交付候选总包_最新.json",
        "股票助手独立使用说明": root / "07文档" / "股票助手独立使用说明.md",
        "进度回答标准": manager / "01配置" / "进度回答标准.json",
    }
    rule = load_json(rule_path)
    final_selfcheck = load_json(paths["最终自检包"])
    candidate = load_json(paths["交付候选总包"])
    progress_standard = load_json(paths["进度回答标准"])
    action_flags = rule.get("安全边界", {})
    all_actions_closed = all(action_flags.values())
    judgement = {
        "最终自检包通过": final_selfcheck.get("是否通过材料侧最终自检") is True,
        "交付候选总包通过": candidate.get("是否具备材料侧交付候选条件") is True,
        "核心入口文件存在": paths["股票助手独立使用说明"].exists(),
        "进度口径存在": bool(stock_progress(progress_standard).get("当前进度")),
        "真实动作仍关闭": all_actions_closed,
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "提交原则": rule.get("提交原则", []),
        "提交判定": judgement,
        "股票系统进度": stock_progress(progress_standard),
        "提交材料入口": [
            {"名称": "股票助手独立使用说明", "路径": str(paths["股票助手独立使用说明"])},
            {"名称": "交付前最终自检包", "路径": str(paths["最终自检包"])},
            {"名称": "交付候选总包", "路径": str(paths["交付候选总包"])},
        ],
        "提交给用户确认事项": rule.get("提交给用户确认事项", []),
        "仍未放行边界": rule.get("仍未放行边界", []),
        "是否具备提交用户阅读确认条件": passed,
        "当前结论": "股票助手已具备提交用户阅读确认的材料条件；真实企业微信发送、n8n导入或启用、OpenClaw真实桥接、服务刷新和交易接口仍需人工确认后另行执行。" if passed else "股票助手提交包前置材料不完整，不能提交用户阅读确认。",
        "实际动作": action_flags,
    }
    output_dir = root / "03数据" / "54交付提交包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付提交包_{stamp}.json"
    latest_json = output_dir / "股票助手交付提交包_最新.json"
    output_md = output_dir / f"股票助手交付提交包_{stamp}.md"
    latest_md = output_dir / "股票助手交付提交包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备提交用户阅读确认条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
