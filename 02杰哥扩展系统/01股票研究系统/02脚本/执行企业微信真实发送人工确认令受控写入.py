# -*- coding: utf-8 -*-
"""
名称：执行企业微信真实发送人工确认令受控写入.py
作用：基于本轮用户授权，写入公共受控发送器当天有效人工确认令。
安全边界：仅写公共组件确认令配置；先备份；只允许本人白名单和 text/markdown；禁止 n8n、券商接口和自动交易。
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
AUTH = ROOT / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json"
CONFIRMATION = COMMON_ROOT / "01配置" / "企业微信真实发送人工确认令.json"
OUT_DIR = ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入"


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


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    now = datetime.now()
    auth = load_json(AUTH)
    allowed = auth.get("允许事项", {}).get("允许单人白名单企业微信真实灰度") is True
    if not allowed:
        raise RuntimeError("本轮用户授权记录不存在或不允许单人白名单企业微信真实灰度")

    stamp = now.strftime("%Y%m%d_%H%M%S")
    backup_dir = OUT_DIR / "备份" / stamp
    backup_file = backup_dir / "企业微信真实发送人工确认令_写入前备份.json"
    backup_exists = CONFIRMATION.exists()
    if backup_exists:
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONFIRMATION, backup_file)

    confirmation = {
        "确认状态": "已人工确认",
        "允许真实发送": True,
        "有效日期": now.strftime("%Y-%m-%d"),
        "确认令": f"ALLOW_WECOM_REAL_SEND_{now.strftime('%Y%m%d')}",
        "允许接收人": ["ChenXiaoJie"],
        "允许消息类型": ["text", "markdown"],
        "允许n8n": False,
        "允许自动交易": False,
        "确认说明": "本轮用户已授权推进股票系统受控单人真实灰度；仅本人白名单、单条股票短回复消息；禁止群发、n8n、券商接口、自动交易和正式库写入。",
        "授权记录": str(AUTH),
        "写入时间": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    before_hash = sha256(CONFIRMATION)
    write_json(CONFIRMATION, confirmation)
    after_hash = sha256(CONFIRMATION)

    report = {
        "名称": "企业微信真实发送人工确认令受控写入",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "完成",
        "确认令路径": str(CONFIRMATION),
        "写入前存在": backup_exists,
        "写入前sha256": before_hash,
        "写入后sha256": after_hash,
        "备份文件": str(backup_file) if backup_exists else "",
        "确认令摘要": {
            "确认状态": confirmation["确认状态"],
            "允许真实发送": confirmation["允许真实发送"],
            "有效日期": confirmation["有效日期"],
            "允许接收人": confirmation["允许接收人"],
            "允许消息类型": confirmation["允许消息类型"],
            "允许n8n": confirmation["允许n8n"],
            "允许自动交易": confirmation["允许自动交易"],
        },
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
            "重启正式服务": False,
        },
        "回滚方式": "如需回滚，删除确认令文件；若存在写入前备份，则复制备份回确认令路径。",
    }
    write_json(OUT_DIR / "企业微信真实发送人工确认令受控写入_最新.json", report)
    lines = [
        "# 企业微信真实发送人工确认令受控写入",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 确认令路径：{report['确认令路径']}",
        f"- 写入后sha256：{report['写入后sha256']}",
        f"- 回滚方式：{report['回滚方式']}",
        "",
    ]
    write_text(OUT_DIR / "企业微信真实发送人工确认令受控写入_最新.md", "\n".join(lines))
    print(json.dumps({"状态": "完成", "确认令路径": str(CONFIRMATION), "写入后sha256": after_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
