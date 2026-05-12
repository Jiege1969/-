# -*- coding: utf-8 -*-
"""
名称：记录语音确认学习样本.py
作用：把语音误识别文本和用户文字确认结果记录为别名学习候选，供后续提炼进正式规则。
触发方式：python 记录语音确认学习样本.py --voice-text "分析新一生" --confirm-text "确认：新易盛"
依赖：Python标准库；语音追问学习规则.json；重点关注股票池.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统语音学习样本和别名候选库；不直接修改正式规则；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建语音确认学习样本记录脚本。
标识：stock-voice-confirmation-learning-record
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_stocks(root: Path) -> list[dict[str, Any]]:
    stocks = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []}).get("股票池", [])
    return [{"代码": item.get("代码"), "名称": item.get("名称")} for item in stocks]


def resolve_confirm_stock(confirm_text: str, stocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = confirm_text.replace("确认：", "").replace("确认:", "").replace("改为：", "").replace("改为:", "").strip()
    for item in stocks:
        if item.get("名称") and item["名称"] in text:
            return item
        code = str(item.get("代码") or "")
        if code and (code in text or code[2:] in text):
            return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice-text", default="分析新一生", help="原语音识别文本")
    parser.add_argument("--confirm-text", default="确认：新易盛", help="用户文字确认文本")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "语音追问学习规则.json")
    stock = resolve_confirm_stock(args.confirm_text, load_stocks(root))
    status = "已识别" if stock else "待人工补充"
    sample = {
        "记录时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原语音识别文本": args.voice_text,
        "用户确认文本": args.confirm_text,
        "标准股票": stock or {},
        "学习状态": status,
        "说明": "本记录进入别名候选库，不直接修改正式规则。",
        "安全边界": rules.get("安全边界", {})
    }
    sample_dir = root / rules.get("保存路径", {}).get("确认学习样本", "03数据/13语音学习/02确认学习样本")
    alias_dir = root / rules.get("保存路径", {}).get("别名候选库", "03数据/13语音学习/03别名候选库")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_output = sample_dir / f"语音确认学习样本_{timestamp}.json"
    sample_latest = sample_dir / "语音确认学习样本_最新.json"
    write_json(sample_output, sample)
    write_json(sample_latest, sample)

    alias_latest = alias_dir / "语音别名候选库_最新.json"
    alias_db = load_json(alias_latest, {"候选别名": []})
    if stock:
        alias_db.setdefault("候选别名", []).append({
            "误识别文本": args.voice_text,
            "标准名称": stock.get("名称"),
            "代码": stock.get("代码"),
            "来源": "用户文字确认",
            "次数": 1,
            "记录时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "是否建议加入正式别名": False
        })
    alias_db["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_json(alias_dir / f"语音别名候选库_{timestamp}.json", alias_db)
    write_json(alias_latest, alias_db)
    print(json.dumps({"学习状态": status, "标准股票": stock or {}, "输出": str(sample_output)}, ensure_ascii=False))
    return 0 if status == "已识别" else 1


if __name__ == "__main__":
    raise SystemExit(main())
