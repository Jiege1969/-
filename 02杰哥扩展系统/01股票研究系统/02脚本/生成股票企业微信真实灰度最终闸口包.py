# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度最终闸口包.py
作用：生成股票企业微信真实小流量灰度前的最终闸口包，列明放行条件、阻断原因、灰度批次和回滚要求。
触发方式：python 生成股票企业微信真实灰度最终闸口包.py
依赖：Python标准库；股票企业微信真实灰度最终闸口规则.json；股票系统交付验收清单_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地闸口报告；不刷新服务；不导入n8n；不启用Webhook；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度最终闸口包脚本。
标识：stock-wework-real-gray-final-gate-package-generate
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
        "# 股票企业微信真实灰度最终闸口包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否允许真实灰度：{report['是否允许真实灰度']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、放行条件",
        "",
    ]
    for item in report["放行条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、当前阻断原因", ""])
    for item in report["阻断原因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、灰度批次建议", ""])
    for key, value in report["灰度批次建议"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、回滚要求", ""])
    for item in report["回滚要求"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度最终闸口规则.json"
    checklist_path = root / "03数据" / "35交付验收清单" / "股票系统交付验收清单_最新.json"
    authorization_path = root / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json"
    receipt_path = root / "03数据" / "45真实灰度确认回执登记" / "股票企业微信真实灰度确认回执登记包_最新.json"
    rule = load_json(rule_path)
    checklist = load_json(checklist_path)
    authorization = load_json(authorization_path)
    receipt = load_json(receipt_path)
    authorized = (
        authorization.get("允许事项", {}).get("允许单人白名单企业微信真实灰度") is True
        and receipt.get("当前确认状态") == "已确认"
    )
    blockers = list(rule.get("默认阻断原因", []))
    if authorized:
        blockers = [
            item for item in blockers
            if "真实企业微信发送" not in item
            and "用户明确放行" not in item
            and "本地股票助手当前运行进程" not in item
        ]
    if checklist.get("当前可交付层级") != "E交付可用" and not authorized:
        blockers.append(f"当前交付验收层级为{checklist.get('当前可交付层级', '未知')}，尚未达到E交付可用。")
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "交付验收清单": str(checklist_path),
        "授权记录": str(authorization_path),
        "当前确认状态": receipt.get("当前确认状态", "未知"),
        "放行条件": rule.get("放行条件", []),
        "阻断原因": blockers,
        "灰度批次建议": rule.get("灰度批次建议", {}),
        "回滚要求": rule.get("回滚要求", []),
        "是否允许真实灰度": bool(authorized),
        "当前结论": "本轮用户授权已登记，允许本人白名单单条企业微信真实灰度；n8n、OpenClaw、服务刷新、券商接口和自动交易仍关闭。" if authorized else "当前只完成真实灰度前闸口准备；未获得明确放行前，不进入真实企业微信、n8n、OpenClaw或服务刷新动作。",
        "实际动作": {
            "刷新服务": False,
            "导入n8n": False,
            "启用Webhook": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "36真实灰度最终闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度最终闸口包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度最终闸口包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度最终闸口包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度最终闸口包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否允许真实灰度": bool(authorized), "阻断原因数量": len(blockers), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
