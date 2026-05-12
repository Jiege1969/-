# -*- coding: utf-8 -*-
"""
名称：生成语音追问确认单.py
作用：当语音股票指令解析不确定时，生成一次追问确认单，等待用户文字确认。
触发方式：python 生成语音追问确认单.py --text "分析新一生"
依赖：Python标准库；语音追问学习规则.json；解析语音股票指令.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地追问确认单；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建语音追问确认单生成脚本。
标识：stock-voice-clarification-card-generate
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_voice_parser(root: Path):
    path = root / "02脚本" / "解析语音股票指令.py"
    spec = importlib.util.spec_from_file_location("voice_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("voice parser import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="分析新一生", help="语音识别后的低置信文本")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "语音追问学习规则.json")
    voice_parser = load_voice_parser(root)
    parsed = voice_parser.parse_command(args.text)
    candidates = [item.get("标准名称") for item in parsed.get("候选", []) if item.get("标准名称")]
    candidates = list(dict.fromkeys(candidates))[:3]
    candidate_text = "、".join(candidates) if candidates else "未识别到明确候选"
    templates = rules.get("追问模板", [])
    question = templates[0].replace("{候选股票}", candidate_text) if templates else f"请文字确认股票：{candidate_text}"
    should_ask = parsed.get("执行判断", {}).get("执行状态") != "可执行" or parsed.get("股票", {}).get("置信度", 0) < rules.get("触发条件", {}).get("置信度低于", 0.82)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原始文本": args.text,
        "解析结果": parsed,
        "是否需要追问": bool(should_ask),
        "追问文本": question if should_ask else "",
        "候选股票": candidates,
        "用户文字回复格式": ["确认：股票名称", "改为：股票名称", "取消"],
        "安全边界": rules.get("安全边界", {})
    }
    output_dir = root / rules.get("保存路径", {}).get("追问确认单", "03数据/13语音学习/01追问确认单")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"语音追问确认单_{timestamp}.json"
    latest = output_dir / "语音追问确认单_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"是否需要追问": report["是否需要追问"], "追问文本": report["追问文本"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
