# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-real-wework-gray-gap-list.py
Purpose: Generate the remaining gap list before real WeWork whitelist gray tests for the stock assistant.
Trigger: python 生成股票助手真实企业微信灰度差距清单.py
Dependencies: Python standard library; local gray connectivity drill report; gray connectivity preflight report.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and writes a gap list only; does not enable n8n, trigger n8n, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created real WeWork gray gap list generator.
Marker: stock-assistant-real-wework-gray-gap-list-generate
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
        "# 股票助手真实企业微信灰度差距清单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 是否具备真实企业微信灰度发送条件：{report['是否具备真实企业微信灰度发送条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、已完成",
        "",
    ]
    for item in report["已完成"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、剩余差距", ""])
    for item in report["剩余差距"]:
        lines.append(f"- {item['事项']}：{item['处理方式']}")
    lines.extend(["", "## 四、禁止事项", ""])
    for key, value in report["实际动作"].items():
        if value is False:
            lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    preflight = load_json(root / "03数据" / "70灰度联通前实况核验" / "股票助手灰度联通前实况核验_最新.json")
    drill = load_json(root / "03数据" / "71本地灰度联通演练" / "股票助手本地灰度联通演练_最新.json")
    completed = [
        "新系统隔离 n8n 已运行，端口 127.0.0.1:28679。",
        "股票助手工作流已导入新系统隔离 n8n，并保持 active=false。",
        "灰度联通前实况核验通过，本地灰度联通条件成立。",
        "5 条本地灰度样例通过，覆盖文字查询、关注池查询、重庆话语音、模糊追问和交易拦截。",
        "旧系统 D:\\杰哥智能体操作系统 未写入、未重启、未影响。",
    ]
    gaps = [
        {"事项": "统一消息出口仍为本地队列，真实发送=false", "处理方式": "后续生成受控真实发送配置，不直接修改现有配置。"},
        {"事项": "企业微信真实发送凭据未注入受控环境", "处理方式": "只允许放入统一消息出口受控配置或环境变量，股票系统不得持有明文密钥。"},
        {"事项": "企业微信白名单接收人未写成实际可发送ID", "处理方式": "只允许首轮本人白名单，最多5条测试消息，禁止群发和外部客户。"},
        {"事项": "OpenClaw真实桥接仍未接入新系统n8n", "处理方式": "继续保持OpenClaw只做消息代理，业务判断留在n8n和股票助手。"},
        {"事项": "n8n工作流仍未启用真实Webhook", "处理方式": "先生成启用前闸口，启用后仍先走本地回环，再进入最多5条真实灰度。"},
    ]
    real_ready = False
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "引用材料": {
            "灰度联通前实况核验": str(root / "03数据" / "70灰度联通前实况核验" / "股票助手灰度联通前实况核验_最新.json"),
            "本地灰度联通演练": str(root / "03数据" / "71本地灰度联通演练" / "股票助手本地灰度联通演练_最新.json"),
        },
        "前置状态": {
            "本地灰度联通": preflight.get("是否可以进入本地灰度联通演练"),
            "真实企业微信发送": preflight.get("是否可以进入真实企业微信灰度发送"),
            "本地演练通过": drill.get("是否通过"),
            "本地演练通过样例": drill.get("通过样例"),
        },
        "已完成": completed,
        "剩余差距": gaps,
        "是否具备真实企业微信灰度发送条件": real_ready,
        "当前结论": "股票系统已具备本地灰度联通能力；真实企业微信白名单发送还差受控凭据、真实白名单、消息出口切换和OpenClaw桥接闸口，不自动发送。",
        "实际动作": {
            "生成差距清单": True,
            "启用n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "72真实企业微信灰度差距清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手真实企业微信灰度差距清单_{stamp}.json"
    latest_json = output_dir / "股票助手真实企业微信灰度差距清单_最新.json"
    output_md = output_dir / f"股票助手真实企业微信灰度差距清单_{stamp}.md"
    latest_md = output_dir / "股票助手真实企业微信灰度差距清单_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"真实企业微信灰度就绪": real_ready, "剩余差距": len(gaps), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
