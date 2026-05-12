# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度未确认拦截包.py
作用：根据真实灰度确认回执登记状态生成未确认拦截报告，明确未确认前所有真实动作均被拦截。
触发方式：python 生成股票企业微信真实灰度未确认拦截包.py
依赖：Python标准库；股票企业微信真实灰度未确认拦截规则.json；股票企业微信真实灰度确认回执登记包_最新.json；股票企业微信真实灰度放行前总验收包_最新.json；统一消息出口配置.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度未确认拦截包脚本。
标识：stock-wework-real-gray-unconfirmed-guard-package-generate
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
        "# 股票企业微信真实灰度未确认拦截包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否启用未确认拦截：{report['是否启用未确认拦截']}",
        f"- 当前确认状态：{report['当前确认状态']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、必须拦截动作",
        "",
    ]
    for item in report["必须拦截动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、允许动作", ""])
    for item in report["允许动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、拦截判定", ""])
    for key, value in report["拦截判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度未确认拦截规则.json"
    receipt_path = root / "03数据" / "45真实灰度确认回执登记" / "股票企业微信真实灰度确认回执登记包_最新.json"
    preflight_path = root / "03数据" / "44真实灰度放行前总验收" / "股票企业微信真实灰度放行前总验收包_最新.json"
    outlet_config_path = sys_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "统一消息出口配置.json"
    authorization_path = root / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json"

    rule = load_json(rule_path)
    receipt = load_json(receipt_path)
    preflight = load_json(preflight_path)
    outlet_config = load_json(outlet_config_path)
    authorization = load_json(authorization_path)
    authorized = authorization.get("允许事项", {}).get("允许单人白名单企业微信真实灰度") is True
    state = receipt.get("未确认状态登记", {})
    strategy = outlet_config.get("出口策略", {})
    is_unconfirmed = receipt.get("当前确认状态") == "未确认" and state.get("确认状态") == "未确认"
    real_actions_closed = all(state.get(key) is False for key in [
        "允许真实发送",
        "允许导入n8n",
        "允许启用n8n",
        "允许调用OpenClaw",
        "允许自动交易",
    ])
    outlet_still_disabled = (
        strategy.get("当前发送模式") == "本地队列"
        and strategy.get("是否允许真实发送") is False
    )
    guard_enabled = (not authorized) and (
        receipt_path.exists()
        and preflight_path.exists()
        and preflight.get("是否具备提交人工确认条件") is True
        and is_unconfirmed
        and real_actions_closed
        and outlet_still_disabled
    )
    blocking = {
        "确认回执登记包存在": receipt_path.exists(),
        "放行前总验收包存在": preflight_path.exists(),
        "总验收只允许提交人工确认": preflight.get("是否具备提交人工确认条件") is True,
        "确认状态未确认": is_unconfirmed,
        "真实动作默认关闭": real_actions_closed,
        "统一消息出口仍为本地队列": outlet_still_disabled,
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "依赖材料": {
            "确认回执登记包": str(receipt_path),
            "放行前总验收包": str(preflight_path),
            "统一消息出口配置": str(outlet_config_path),
        },
        "拦截原则": rule.get("拦截原则", []),
        "必须拦截动作": rule.get("必须拦截动作", []),
        "允许动作": rule.get("允许动作", []),
        "拦截判定": blocking,
        "授权记录": str(authorization_path),
        "本轮授权已登记": authorized,
        "当前确认状态": receipt.get("当前确认状态", "未确认"),
        "是否启用未确认拦截": guard_enabled,
        "当前结论": "本轮用户授权已登记，未确认拦截不再阻断本人白名单单条企业微信真实灰度；n8n、OpenClaw、正式写库和交易接口仍保持拦截。" if authorized else ("确认回执仍为未确认，真实发送、n8n导入/启用、OpenClaw真实桥接、正式写库和交易接口均保持拦截。" if guard_enabled else "未确认拦截条件不完整，不能进入任何真实灰度动作。"),
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "46真实灰度未确认拦截"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度未确认拦截包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度未确认拦截包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度未确认拦截包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度未确认拦截包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否启用未确认拦截": guard_enabled, "当前确认状态": report["当前确认状态"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
