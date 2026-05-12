# -*- coding: utf-8 -*-
"""
名称：生成企业微信语音追问短回复.py
作用：根据语音股票指令解析结果生成企业微信追问或可执行提示草稿。
触发方式：python 生成企业微信语音追问短回复.py --text "给我看哈新一盛"
依赖：Python标准库；解析语音股票指令.py；语音股票指令容错规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地配置和股票池；只写03数据/24企业微信短回复和04日志/企业微信短回复；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信语音追问短回复生成脚本。
标识：stock-wework-voice-clarification-reply-generate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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


def parse_voice(root: Path, text: str) -> dict[str, Any]:
    script = root / "02脚本" / "解析语音股票指令.py"
    result = subprocess.run([sys.executable, str(script), "--text", text], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest = root / "04日志" / "语音股票指令" / "stock-voice-command-tolerance-parse-最新.json"
    parsed = load_json(latest, {})
    parsed["解析返回码"] = result.returncode
    parsed["解析输出"] = result.stdout.strip()
    parsed["解析错误"] = result.stderr.strip()
    return parsed


def candidate_text(candidates: list[dict[str, Any]]) -> str:
    lines = []
    seen: set[str] = set()
    for item in candidates:
        name = item.get("标准名称", "")
        code = item.get("代码", "")
        if not name or name in seen:
            continue
        seen.add(name)
        lines.append(f"{name}（{code}，置信度{item.get('置信度')}）")
        if len(lines) >= 3:
            break
    return "；".join(lines) or "未找到候选股票"


def build_reply(parsed: dict[str, Any]) -> dict[str, Any]:
    decision = parsed.get("执行判断", {})
    stock = parsed.get("股票", {})
    status = decision.get("执行状态")
    if status == "可执行":
        reply = (
            f"我识别为：{stock.get('名称')}（{stock.get('代码')}），匹配文本“{stock.get('匹配文本')}”，"
            f"置信度{stock.get('置信度')}。可以生成研究摘要。\n"
            "声明：当前为禁用态草稿，不真实发送企业微信，不触发n8n，不连接券商接口。"
        )
        need_clarification = False
    else:
        reply = (
            "这条语音我还不能确定股票对象，请文字确认一次。\n"
            f"候选：{candidate_text(parsed.get('候选', []))}\n"
            "回复格式：确认：股票名称。确认后会记录为学习样本，下次同类语音优先识别。"
        )
        need_clarification = True
    return {"需要追问": need_clarification, "回复": reply}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="给我看哈新一盛")
    args = parser.parse_args()
    root = module_root()
    parsed = parse_voice(root, args.text)
    reply_info = build_reply(parsed)
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "voice_clarification_dry_run_only",
        "原始语音文本": args.text,
        "解析结果": parsed,
        "需要追问": reply_info["需要追问"],
        "回复": reply_info["回复"],
        "实际动作": {
            "联网": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "24企业微信短回复"
    log_dir = root / "04日志" / "企业微信短回复"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "企业微信语音追问短回复_最新.json"
    latest_json = output_dir / "企业微信语音追问短回复_最新.json"
    md_path = output_dir / "企业微信语音追问短回复_最新.md"
    latest_md = output_dir / "企业微信语音追问短回复_最新.md"
    log_path = log_dir / "stock-wework-voice-clarification-reply-generate-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    write_text(md_path, "# 企业微信语音追问短回复草稿\n\n" + package["回复"])
    write_text(latest_md, "# 企业微信语音追问短回复草稿\n\n" + package["回复"])
    write_json(log_path, package)
    print(json.dumps({"需要追问": package["需要追问"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
