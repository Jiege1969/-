# -*- coding: utf-8 -*-
"""
名称：生成企业微信语音确认学习回复.py
作用：在用户文字确认语音识别结果后，记录学习样本并生成企业微信学习确认回复草稿。
触发方式：python 生成企业微信语音确认学习回复.py --voice-text "分析新一生" --confirm-text "确认：新易盛"
依赖：Python标准库；记录语音确认学习样本.py；语音追问学习规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统语音学习样本和回复草稿；不修改正式别名规则；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信语音确认学习回复脚本。
标识：stock-wework-voice-confirm-learning-reply-generate
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


def record_learning(root: Path, voice_text: str, confirm_text: str) -> dict[str, Any]:
    script = root / "02脚本" / "记录语音确认学习样本.py"
    result = subprocess.run(
        [sys.executable, str(script), "--voice-text", voice_text, "--confirm-text", confirm_text],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = root / "03数据" / "13语音学习" / "02确认学习样本" / "语音确认学习样本_最新.json"
    sample = load_json(latest, {})
    return {
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
        "学习样本": sample,
        "学习样本路径": str(latest),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice-text", default="分析新一生")
    parser.add_argument("--confirm-text", default="确认：新易盛")
    args = parser.parse_args()
    root = module_root()
    learning = record_learning(root, args.voice_text, args.confirm_text)
    sample = learning.get("学习样本", {})
    stock = sample.get("标准股票", {})
    status = sample.get("学习状态", "未知")
    reply = (
        f"已记录语音学习样本：原识别“{args.voice_text}”，文字确认“{args.confirm_text}”。\n"
        f"识别结果：{stock.get('名称', '待人工补充')}（{stock.get('代码', '')}），状态：{status}。\n"
        "说明：本次只进入别名候选库，不直接修改正式规则；后续由进化系统归纳提炼后再决定是否纳入正式别名。"
    )
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "voice_confirm_learning_reply_only",
        "原语音识别文本": args.voice_text,
        "用户确认文本": args.confirm_text,
        "学习记录": learning,
        "回复": reply,
        "实际动作": {
            "修改正式规则": False,
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
    json_path = output_dir / "企业微信语音确认学习回复_最新.json"
    latest_json = output_dir / "企业微信语音确认学习回复_最新.json"
    md_path = output_dir / "企业微信语音确认学习回复_最新.md"
    latest_md = output_dir / "企业微信语音确认学习回复_最新.md"
    log_path = log_dir / "stock-wework-voice-confirm-learning-reply-generate-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    write_text(md_path, "# 企业微信语音确认学习回复草稿\n\n" + reply)
    write_text(latest_md, "# 企业微信语音确认学习回复草稿\n\n" + reply)
    write_json(log_path, package)
    print(json.dumps({"学习状态": status, "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if learning.get("返回码") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
