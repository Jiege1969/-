# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信单条真实灰度发送闭环报告.py
作用：汇总本轮股票短回复单条企业微信真实灰度发送结果、确认令、计数和安全边界。
安全边界：只读日志和配置；只写股票系统本地报告；不再次发送、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
OUT_DIR = ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环"


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


def latest_json(directory: Path, pattern: str = "*.json") -> Path:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else Path()


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信单条真实灰度发送闭环报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['总结论']}",
        f"- 真实发送成功：{report['真实发送成功']}",
        f"- 目标用户：{report['目标用户']}",
        f"- 当天计数：{report['当天计数']}",
        "",
        "## 关键证据",
        "",
    ]
    for key, value in report["关键证据"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stock_log_dir = ROOT / "04日志" / "企业微信主动研究灰度发送"
    common_log_dir = COMMON_ROOT / "04日志" / "企业微信受控发送器"
    counter_path = COMMON_ROOT / "03数据" / "04企业微信灰度发送计数" / f"企业微信灰度发送计数_{datetime.now().strftime('%Y%m%d')}.json"
    confirmation_path = COMMON_ROOT / "01配置" / "企业微信真实发送人工确认令.json"
    auth_path = ROOT / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json"

    stock_log_path = latest_json(stock_log_dir, "stock-active-research-wework-gray-send-*.json")
    common_log_path = latest_json(common_log_dir, "wework-controlled-sender-*.json")
    stock_log = load_json(stock_log_path)
    common_log = load_json(common_log_path)
    counter = load_json(counter_path)
    confirmation = load_json(confirmation_path)

    send_ok = (
        stock_log.get("结果判定", {}).get("真实发送成功") is True
        and common_log.get("发送结果", {}).get("ok") is True
        and common_log.get("发送结果", {}).get("企业微信返回", {}).get("errcode") == 0
    )
    safe = (
        stock_log.get("实际动作", {}).get("触发n8n") is False
        and stock_log.get("实际动作", {}).get("调用券商接口") is False
        and stock_log.get("实际动作", {}).get("自动交易") is False
        and common_log.get("实际动作", {}).get("写旧系统") is False
        and common_log.get("实际动作", {}).get("写正式库") is False
        and common_log.get("实际动作", {}).get("自动交易") is False
    )
    target_ok = common_log.get("目标用户") == "ChenXiaoJie"
    confirmation_ok = common_log.get("真实发送人工确认令", {}).get("有效") is True
    count_ok = int(counter.get("已真实发送", 999)) <= int(common_log.get("最大计数", 0) or 0)
    ok = send_ok and safe and target_ok and confirmation_ok and count_ok

    report = {
        "名称": "股票企业微信单条真实灰度发送闭环报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总结论": "通过" if ok else "需复核",
        "真实发送成功": send_ok,
        "目标用户": common_log.get("目标用户", ""),
        "当天计数": f"{counter.get('已真实发送', '')}/{common_log.get('最大计数', '')}",
        "关键证据": {
            "股票发送日志": str(stock_log_path),
            "公共发送器日志": str(common_log_path),
            "计数文件": str(counter_path),
            "确认令文件": str(confirmation_path),
            "授权记录": str(auth_path),
            "企业微信msgid": common_log.get("发送结果", {}).get("企业微信返回", {}).get("msgid", ""),
            "确认令有效": confirmation_ok,
            "目标用户本人白名单": target_ok,
            "计数未超限": count_ok,
        },
        "安全边界": {
            "群发": False,
            "外部客户发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
            "重启正式服务": False,
            "输出密钥": False,
            "确认令允许n8n": confirmation.get("允许n8n"),
            "确认令允许自动交易": confirmation.get("允许自动交易"),
        },
        "下一步": "本轮单条本人白名单真实灰度发送已完成；若扩大范围，必须重新生成授权、确认令、计数和回滚验收。",
    }
    write_json(OUT_DIR / "股票企业微信单条真实灰度发送闭环报告_最新.json", report)
    write_text(OUT_DIR / "股票企业微信单条真实灰度发送闭环报告_最新.md", build_markdown(report))
    print(json.dumps({"状态": report["总结论"], "真实发送成功": send_ok, "当天计数": report["当天计数"], "输出": str(OUT_DIR / "股票企业微信单条真实灰度发送闭环报告_最新.md")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
