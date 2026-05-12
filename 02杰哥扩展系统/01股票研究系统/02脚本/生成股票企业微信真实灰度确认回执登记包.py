# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度确认回执登记包.py
作用：生成股票企业微信真实灰度人工确认回执模板、未确认状态登记和禁止自动执行边界报告。
触发方式：python 生成股票企业微信真实灰度确认回执登记包.py
依赖：Python标准库；股票企业微信真实灰度确认回执登记规则.json；股票企业微信真实灰度放行前总验收包_最新.json；股票企业微信真实灰度人工确认单包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度确认回执登记包脚本。
标识：stock-wework-real-gray-confirmation-receipt-package-generate
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
        "# 股票企业微信真实灰度确认回执登记包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备等待人工确认登记条件：{report['是否具备等待人工确认登记条件']}",
        f"- 当前确认状态：{report['当前确认状态']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、确认回执字段",
        "",
    ]
    for item in report["确认回执字段"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、未确认状态", ""])
    for key, value in report["未确认状态登记"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、登记原则", ""])
    for item in report["登记原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度确认回执登记规则.json"
    preflight_path = root / "03数据" / "44真实灰度放行前总验收" / "股票企业微信真实灰度放行前总验收包_最新.json"
    human_confirmation_path = root / "03数据" / "43真实灰度人工确认单" / "股票企业微信真实灰度人工确认单包_最新.json"
    authorization_path = root / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json"
    rule = load_json(rule_path)
    authorization = load_json(authorization_path)
    authorized = authorization.get("允许事项", {}).get("允许单人白名单企业微信真实灰度") is True
    preflight = load_json(preflight_path)
    human_confirmation = load_json(human_confirmation_path)
    default_state = rule.get("默认状态", {})
    prerequisites = {
        "真实灰度放行前总验收包存在": preflight_path.exists(),
        "放行前总验收可提交人工确认": preflight.get("是否具备提交人工确认条件") is True,
        "人工确认单包存在": human_confirmation_path.exists(),
        "人工确认单具备提交条件": human_confirmation.get("是否具备提交人工确认条件") is True,
        "默认状态仍为未确认": default_state.get("确认状态") == "未确认",
        "默认真实动作仍关闭": all(default_state.get(key) is False for key in [
            "允许真实发送",
            "允许导入n8n",
            "允许启用n8n",
            "允许调用OpenClaw",
            "允许自动交易",
        ]),
    }
    receipt_template = {
        "确认人": "当前施工线程用户" if authorized else "",
        "确认时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if authorized else "",
        "企业微信真实接收人ID": "本人白名单" if authorized else "",
        "是否允许未激活导入n8n": False,
        "是否允许指定时间窗口启用n8n": False,
        "是否允许首轮最多5条企业微信真实测试消息": True if authorized else False,
        "是否确认异常立即回滚": True if authorized else False,
        "是否确认交易接口继续禁用": True,
        "备注": "本轮用户已授权单人白名单受控灰度；仍禁止群发、n8n、券商接口和自动交易。" if authorized else "本模板为空白未确认状态；填写并验收前不得执行真实动作。",
    }
    passed = all(prerequisites.values()) and len(rule.get("确认回执字段", [])) >= 8
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "前置材料": {
            "真实灰度放行前总验收包": str(preflight_path),
            "真实灰度人工确认单包": str(human_confirmation_path),
            "本轮用户授权记录": str(authorization_path),
        },
        "前置条件": prerequisites,
        "确认回执字段": rule.get("确认回执字段", []),
        "确认回执空白模板": receipt_template,
        "未确认状态登记": default_state,
        "授权记录存在": authorization_path.exists(),
        "当前确认状态": "已确认" if authorized else default_state.get("确认状态", "未确认"),
        "登记原则": rule.get("登记原则", []),
        "是否具备等待人工确认登记条件": passed,
        "当前结论": "本轮用户授权已登记，可进入本人白名单单条企业微信真实灰度；n8n、服务重启、券商接口和自动交易仍关闭。" if passed and authorized else ("确认回执登记包已生成，系统仍处于未确认状态；当前不得执行真实发送、n8n导入、n8n启用或OpenClaw真实桥接。" if passed else "确认回执登记前置材料不足，不能等待真实灰度确认。"),
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "45真实灰度确认回执登记"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度确认回执登记包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度确认回执登记包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度确认回执登记包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度确认回执登记包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备等待人工确认登记条件": passed, "当前确认状态": report["当前确认状态"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
