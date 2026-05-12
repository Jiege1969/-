# -*- coding: utf-8 -*-
"""
名称：同步股票系统企微真实推送复测成功状态.py
作用：根据正式企业微信灰度发送日志修正复测控制器状态，避免因stdout编码导致真实成功被误判为阻断。
触发方式：python 同步股票系统企微真实推送复测成功状态.py
依赖：04日志/企业微信主动研究灰度发送/stock-active-research-wework-gray-send-最新.json；03数据/157企微真实推送复测/股票系统企微真实推送复测_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读发送日志；只写复测状态文件；不真实发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-wework-real-push-success-state-sync
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统企微真实推送复测控制器 - {report['生成时间']}",
        "",
        "## 一、复测结论",
        "",
        f"- 模式：{report['模式']}",
        f"- 结论：{report['复测结论']}",
        f"- 当前需放行IP：`{report.get('当前需放行IP') or '已无需提取，企业微信返回ok'}`",
        f"- 真实发送成功：{report['真实发送成功']}",
        "",
        "## 二、同步依据",
        "",
        f"- 灰度发送日志：`{report.get('同步依据', {}).get('灰度发送日志', '')}`",
        f"- 灰度日志生成时间：{report.get('同步依据', {}).get('灰度日志生成时间', '')}",
        "- 说明：本次同步不重复发送企业微信，只修正复测状态。",
        "",
        "## 三、下一步",
        "",
    ]
    for item in report["下一步动作"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 本次同步不真实发送企业微信。",
        "- 不启用n8n自动触发。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    log_path = root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新.json"
    latest_json = root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json"
    latest_md = root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md"
    log = load_json(log_path, {})
    report = load_json(latest_json, {})
    real_success = bool(
        log.get("结果判定", {}).get("真实发送成功")
        or log.get("实际动作", {}).get("企业微信真实发送成功")
    )
    if real_success:
        report["真实发送成功"] = True
        report["复测结论"] = "真实推送复测成功：企业微信返回ok，可信IP阻断已解除"
        report["当前需放行IP"] = report.get("当前需放行IP") or ""
        report["同步依据"] = {
            "同步时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "灰度发送日志": str(log_path),
            "灰度日志生成时间": log.get("生成时间", ""),
            "修正原因": "子进程stdout编码导致控制器未识别真实发送成功；以正式JSON日志为准。",
        }
        report["下一步动作"] = [
            "查看企业微信是否收到股票主动研究灰度消息。",
            "运行或查看完全交付最终验收，确认是否5/5通过。",
            "保持n8n自动触发、券商接口、自动交易继续关闭。",
        ]
        report.setdefault("实际动作", {})["企业微信真实发送成功"] = True
    md = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, md)
    print(json.dumps({
        "状态": "完成",
        "真实发送成功": real_success,
        "报告": str(latest_md),
        "未重复发送企业微信": True,
    }, ensure_ascii=False))
    return 0 if real_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
