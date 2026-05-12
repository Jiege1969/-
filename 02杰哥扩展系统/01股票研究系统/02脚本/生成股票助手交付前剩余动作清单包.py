# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付前剩余动作清单包.py
作用：生成股票助手交付前剩余低风险动作、高风险需确认动作、交付判定和禁止动作清单。
触发方式：python 生成股票助手交付前剩余动作清单包.py
依赖：Python标准库；股票助手交付前剩余动作清单规则.json；股票助手交付材料索引包_最新.json；股票助手交付前只读总状态面板_最新.json；股票企业微信真实灰度未确认拦截包_最新.json；进度回答标准.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付前剩余动作清单包脚本。
标识：stock-assistant-delivery-remaining-action-package-generate
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
        "# 股票助手交付前剩余动作清单包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备剩余动作清单条件：{report['是否具备剩余动作清单条件']}",
        f"- 当前股票系统进度：{report['股票系统进度'].get('当前进度', '')}",
        f"- 可交付使用还需有效工作时间：{report['股票系统进度'].get('可交付使用还需有效工作时间', '')}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、低风险可继续施工动作",
        "",
    ]
    for item in report["低风险可继续施工动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、高风险必须人工确认动作", ""])
    for item in report["高风险必须人工确认动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、交付判定", ""])
    for key, value in report["交付判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    manager = sys_root / "00杰哥系统总管"
    rule_path = root / "01配置" / "股票助手交付前剩余动作清单规则.json"
    index_path = root / "03数据" / "49交付材料索引" / "股票助手交付材料索引包_最新.json"
    dashboard_path = root / "03数据" / "48交付前只读总状态面板" / "股票助手交付前只读总状态面板_最新.json"
    guard_path = root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json"
    progress_standard_path = manager / "01配置" / "进度回答标准.json"

    rule = load_json(rule_path)
    index = load_json(index_path)
    dashboard = load_json(dashboard_path)
    guard = load_json(guard_path)
    progress_standard = load_json(progress_standard_path)
    prerequisites = {
        "交付材料索引包存在": index_path.exists(),
        "交付材料索引具备": index.get("是否具备交付材料索引条件") is True,
        "只读状态面板存在": dashboard_path.exists(),
        "只读状态面板适合继续低风险施工": dashboard.get("是否适合继续低风险施工") is True,
        "未确认拦截包存在": guard_path.exists(),
        "未确认拦截仍启用": guard.get("是否启用未确认拦截") is True,
        "进度回答标准存在": progress_standard_path.exists(),
    }
    delivery_judgement = rule.get("交付判定", {})
    passed = (
        all(prerequisites.values())
        and delivery_judgement.get("材料侧是否接近交付") is True
        and delivery_judgement.get("真实企业微信是否已放行") is False
        and delivery_judgement.get("交易接口是否放行") is False
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "依赖材料": {
            "交付材料索引包": str(index_path),
            "交付前只读总状态面板": str(dashboard_path),
            "未确认拦截包": str(guard_path),
            "进度回答标准": str(progress_standard_path),
        },
        "前置条件": prerequisites,
        "股票系统进度": stock_progress(progress_standard),
        "剩余动作原则": rule.get("剩余动作原则", []),
        "低风险可继续施工动作": rule.get("低风险可继续施工动作", []),
        "高风险必须人工确认动作": rule.get("高风险必须人工确认动作", []),
        "交付判定": delivery_judgement,
        "是否具备剩余动作清单条件": passed,
        "当前结论": "股票助手交付前剩余动作已分层：低风险动作可继续施工，高风险动作必须人工确认；当前真实企业微信和交易接口仍未放行。" if passed else "股票助手交付前剩余动作清单前置材料不足，不能进入交付收口。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "50交付前剩余动作清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付前剩余动作清单包_{stamp}.json"
    latest_json = output_dir / "股票助手交付前剩余动作清单包_最新.json"
    output_md = output_dir / f"股票助手交付前剩余动作清单包_{stamp}.md"
    latest_md = output_dir / "股票助手交付前剩余动作清单包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备剩余动作清单条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
