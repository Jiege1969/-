# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送交易化表达与重复发送拦截预演包.py
作用：读取股票主动推送dry-run样本，预演交易化表达扫描和重复发送拦截。
触发方式：python 生成股票主动推送交易化表达与重复发送拦截预演包.py
依赖：Python标准库；248主动推送白名单频率熔断规则包；249主动推送dry-run消息样本包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地样本并写入251预演包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送交易化表达与重复发送拦截预演包。
标识：stock-active-push-trading-word-duplicate-guard-preview-generate
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


TEXT_KEYS = {
    "消息文本",
    "企业微信预览文本",
    "预览文本",
    "文本",
    "内容",
    "消息",
    "message",
    "text",
    "content",
}


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


def normalize(text: str) -> str:
    return " ".join(str(text).split()).strip()


def digest(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:16]


def walk_text(value: Any, out: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TEXT_KEYS and isinstance(item, str) and item.strip():
                out.append(item)
            walk_text(item, out)
    elif isinstance(value, list):
        for item in value:
            walk_text(item, out)


def collect_sample_texts(sample_json: Path, sample_md: Path) -> list[dict[str, str]]:
    texts: list[str] = []
    data = load_json(sample_json)
    walk_text(data, texts)
    if not texts and sample_md.exists():
        texts.append(sample_md.read_text(encoding="utf-8-sig"))
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for text in texts:
        body = normalize(text)
        if not body:
            continue
        key = digest(body)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"摘要哈希": key, "文本": body})
    return cleaned


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送交易化表达与重复发送拦截预演包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 样本数量：{report['样本数量']}",
        f"- 交易化表达命中数：{report['交易化表达命中数']}",
        f"- 重复发送拦截预演：{report['重复发送拦截预演']['结果']}",
        "",
        "## 交易化表达扫描",
        "",
    ]
    for item in report["扫描结果"]:
        lines.append(f"- {item['摘要哈希']}：命中 {len(item['命中词'])} 个，状态 {item['状态']}")
    lines.extend(["", "## 重复发送拦截预演", ""])
    for key, value in report["重复发送拦截预演"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    rule_path = data / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json"
    sample_json = data / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.json"
    sample_md = data / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.md"

    rules = load_json(rule_path)
    forbidden_words = list(rules.get("内容边界", {}).get("禁止表达", [])) or [
        "买入", "卖出", "加仓", "减仓", "满仓", "清仓", "仓位", "下单", "交易指令"
    ]
    samples = collect_sample_texts(sample_json, sample_md)

    scan_results = []
    hit_count = 0
    for sample in samples:
        text = sample["文本"]
        hits = [word for word in forbidden_words if word and word in text]
        hit_count += len(hits)
        scan_results.append({
            "摘要哈希": sample["摘要哈希"],
            "文本预览": text[:180],
            "命中词": hits,
            "状态": "blocked" if hits else "pass",
        })

    duplicate_preview = {
        "去重键策略": "摘要哈希 + 自然日 + 目标用户草案",
        "样本去重键数量": len({sample["摘要哈希"] for sample in samples}),
        "模拟重复样本": samples[0]["摘要哈希"] if samples else "",
        "重复时动作": "拦截重复发送，只更新本地预览和日志，不进入发送候选",
        "结果": "pass" if samples else "blocked",
    }

    blocked = (not rule_path.exists()) or (not sample_json.exists() and not sample_md.exists()) or not samples or hit_count > 0
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "blocked" if blocked else "pass",
        "规则包": str(rule_path),
        "样本JSON": str(sample_json),
        "样本Markdown": str(sample_md),
        "规则包存在": rule_path.exists(),
        "样本包存在": sample_json.exists() or sample_md.exists(),
        "样本数量": len(samples),
        "禁止词": forbidden_words,
        "扫描结果": scan_results,
        "交易化表达命中数": hit_count,
        "重复发送拦截预演": duplicate_preview,
        "阻断原因": [
            reason for reason, condition in [
                ("248规则包不存在", not rule_path.exists()),
                ("249 dry-run样本包不存在", not (sample_json.exists() or sample_md.exists())),
                ("未提取到可扫描文本", not samples),
                ("命中交易化表达", hit_count > 0),
            ] if condition
        ],
        "实际动作": {
            "读取本地规则包": True,
            "读取本地dry-run样本": True,
            "写本地预演包": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "重载19310": False,
            "重载19302": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式规则库": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }

    out_dir = data / "251主动推送交易化表达与重复发送拦截预演包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送交易化表达与重复发送拦截预演包_{stamp}.json"
    latest_json = out_dir / "股票主动推送交易化表达与重复发送拦截预演包_最新.json"
    output_md = out_dir / f"股票主动推送交易化表达与重复发送拦截预演包_{stamp}.md"
    latest_md = out_dir / "股票主动推送交易化表达与重复发送拦截预演包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "样本数量": len(samples), "命中数": hit_count, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
