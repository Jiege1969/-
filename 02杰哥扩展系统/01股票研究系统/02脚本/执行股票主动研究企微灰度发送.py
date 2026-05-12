# -*- coding: utf-8 -*-
"""
名称：执行股票主动研究企微灰度发送.py
作用：读取股票主动研究企微推送草案，通过公共组件企业微信受控发送器进行dry-run或本人白名单真实灰度发送。
审计说明：本脚本实现《2000只标准大股票池主动研究执行方案》中的“主动推送规则”受控发送部分。
触发方式：python 执行股票主动研究企微灰度发送.py [--real-send]
依赖：03数据/136推送草案/股票企微推送草案_最新.md；00公共组件/企业微信受控发送器.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只发送股票主动研究摘要；真实发送必须显式参数；只发本人白名单；最多5条首轮灰度；不群发；不外部客户；不写旧系统；不交易。
标识：stock-active-research-wework-gray-send
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


def read_text_required(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"必需文件不存在: {path}")
    text = path.read_text(encoding="utf-8-sig", errors="replace").strip()
    if not text:
        raise ValueError(f"必需文件为空: {path}")
    return text


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def utf8_len(text: str) -> int:
    return len(str(text or "").encode("utf-8"))


def trim_message(text: str, limit: int = 1600) -> str:
    # 企业微信长 markdown 在手机端容易截断，单条按 UTF-8 字节保守控制。
    value = str(text or "").strip()
    if utf8_len(value) <= limit:
        return value
    suffix = "\n\n[内容过长，已截断；完整报告见本地文件]"
    budget = limit - utf8_len(suffix)
    kept: list[str] = []
    used = 0
    for char in value:
        size = utf8_len(char)
        if used + size > budget:
            break
        kept.append(char)
        used += size
    return "".join(kept).rstrip() + suffix


def split_long_paragraph(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for char in str(text or ""):
        candidate = current + char
        if utf8_len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = char
    if current:
        chunks.append(current)
    return chunks


def split_message(text: str, limit: int = 1600) -> list[str]:
    value = str(text or "").strip()
    if not value:
        return []
    paragraphs = value.split("\n\n")
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        part = paragraph.strip()
        if not part:
            continue
        candidate = f"{current}\n\n{part}".strip() if current else part
        if utf8_len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if utf8_len(part) <= limit:
            current = part
            continue
        chunks.extend(split_long_paragraph(part, limit))
    if current:
        chunks.append(current)
    if len(chunks) <= 1:
        return chunks
    labeled: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        prefix = f"【第{index}/{len(chunks)}段】\n"
        if utf8_len(prefix + chunk) <= limit:
            labeled.append(prefix + chunk)
        else:
            labeled.append(prefix + trim_message(chunk, limit - utf8_len(prefix)))
    return labeled


def parse_sender_stdout(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text.splitlines()[-1])
    except json.JSONDecodeError:
        return {"原始stdout": text}


def run_sender(sender_path: Path, content: str, real_send: bool) -> dict[str, Any]:
    args = [sys.executable, str(sender_path), "--content", content, "--msgtype", "markdown"]
    if real_send:
        args.append("--real-send")
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    return {
        "命令": " ".join([Path(args[0]).name, Path(args[1]).name] + args[2:3] + (["--real-send"] if real_send else [])),
        "返回码": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stdout_json": parse_sender_stdout(completed.stdout),
        "stderr": completed.stderr.strip(),
    }


def run_senders(sender_path: Path, chunks: list[str], real_send: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for chunk in chunks:
        results.append(run_sender(sender_path, chunk, real_send))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-send", action="store_true", help="显式开启本人白名单真实灰度发送")
    parser.add_argument("--source-md", default="", help="可选：指定推送草案Markdown路径")
    args = parser.parse_args()

    root = module_root()
    common_sender = root.parents[0] / "00公共组件" / "02脚本" / "企业微信受控发送器.py"
    source_md = Path(args.source_md) if args.source_md else root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
    source_json = source_md.with_suffix(".json") if source_md.name != "股票企微推送草案_最新.md" else root / "03数据" / "136推送草案" / "股票企微推送草案_最新.json"
    log_dir = root / "04日志" / "企业微信主动研究灰度发送"

    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S-%f")
    draft_text = read_text_required(source_md)
    draft_meta = load_json(source_json, {})
    chunks = split_message(draft_text)
    if not chunks:
        raise ValueError("待发送内容为空")
    sender_results = run_senders(common_sender, chunks, args.real_send)

    sender_stdout_list = [item.get("stdout_json", {}) for item in sender_results]
    real_success = bool(args.real_send and all(item.get("real_send_success") is True for item in sender_stdout_list))
    dry_success = bool((not args.real_send) and all(item.get("返回码") == 0 and item.get("stdout_json", {}).get("allowed") is True for item in sender_results))
    result = {
        "名称": "股票主动研究企微灰度发送记录",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "real-send" if args.real_send else "dry-run",
        "上游草案Markdown": str(source_md),
        "上游草案JSON": str(source_json),
        "草案数据日期": draft_meta.get("数据日期", ""),
        "内容长度": len(draft_text),
        "内容字节数": utf8_len(draft_text),
        "分段数量": len(chunks),
        "分段长度": [len(chunk) for chunk in chunks],
        "分段字节数": [utf8_len(chunk) for chunk in chunks],
        "发送器路径": str(common_sender),
        "发送器结果": sender_results,
        "结果判定": {
            "dry_run成功": dry_success,
            "真实发送成功": real_success,
            "是否通过公共发送器检查": all(item.get("allowed") is True for item in sender_stdout_list),
            "是否使用公共受控发送器": True,
            "是否分段发送": len(chunks) > 1,
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否绕过统一消息出口": False,
            "是否群发": False,
            "是否外部客户发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取推送草案": True,
            "调用公共受控发送器": True,
            "企业微信真实发送": bool(args.real_send),
            "企业微信真实发送成功": real_success,
            "写入04日志": True,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    output = log_dir / f"stock-active-research-wework-gray-send-{stamp}.json"
    latest = log_dir / "stock-active-research-wework-gray-send-最新.json"
    latest_by_mode = log_dir / ("stock-active-research-wework-gray-send-最新真实.json" if args.real_send else "stock-active-research-wework-gray-send-最新演练.json")
    write_json(output, result)
    write_json(latest, result)
    write_json(latest_by_mode, result)

    ok = real_success if args.real_send else dry_success
    print(json.dumps({
        "ok": ok,
        "模式": result["模式"],
        "通过公共发送器检查": result["结果判定"]["是否通过公共发送器检查"],
        "真实发送成功": real_success,
        "分段数量": len(chunks),
        "输出": str(output),
    }, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
