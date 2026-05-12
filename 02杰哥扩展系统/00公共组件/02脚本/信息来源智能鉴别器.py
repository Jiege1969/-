# -*- coding: utf-8 -*-
"""
名称：信息来源智能鉴别器.py
作用：按公共可信度分层规则离线判断 URL 来源等级、用途边界和是否可作正式依据候选。
触发方式：
  python 信息来源智能鉴别器.py --url https://www.gov.cn/
  python 信息来源智能鉴别器.py --self-test
安全边界：不联网、不下载、不写正式库、不写向量库、不触发 n8n、不生成业务结论。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_host(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    host = (parsed.hostname or "").lower().strip(".")
    return host


def domain_match(host: str, rule: str) -> bool:
    rule = str(rule or "").lower().strip(".")
    if not rule:
        return False
    if rule.startswith("*."):
        base = rule[2:]
        return host.endswith(f".{base}") and host != base
    return host == rule or host.endswith(f".{rule}")


def classify_url(url: str, config: dict[str, Any]) -> dict[str, Any]:
    host = normalize_host(url)
    if not host:
        return {
            "来源URL": url,
            "匹配域名": "",
            "可信度等级": "S6",
            "来源类型": "无有效URL",
            "默认用途": "不可用",
            "默认限制": "必须补齐有效 URL。",
            "是否可作正式依据候选": False,
            "是否需要反向追溯": True,
            "人工复核重点": ["补齐来源URL"],
        }

    candidates: list[tuple[int, int, dict[str, Any], str]] = []
    for index, layer in enumerate(config.get("可信度分层", [])):
        for rule in layer.get("域名规则", []):
            if domain_match(host, rule):
                specificity = len(str(rule).replace("*.", ""))
                candidates.append((index, -specificity, layer, rule))
    if not candidates:
        layer = next((item for item in config.get("可信度分层", []) if item.get("等级") == "S6"), {})
        return {
            "来源URL": url,
            "匹配域名": host,
            "可信度等级": "S6",
            "来源类型": layer.get("名称", "普通第三方、自媒体、论坛和未知来源"),
            "默认用途": layer.get("默认用途", "检索线索或人工排查对象"),
            "默认限制": layer.get("默认限制", "默认不得进入正式证据链。"),
            "是否可作正式依据候选": False,
            "是否需要反向追溯": True,
            "人工复核重点": ["反向追溯权威原始来源"],
        }

    _index, _specificity, layer, rule = sorted(candidates, key=lambda item: (item[0], item[1]))[0]
    grade = str(layer.get("等级", "S6"))
    return {
        "来源URL": url,
        "匹配域名": rule,
        "可信度等级": grade,
        "来源类型": layer.get("名称", ""),
        "默认用途": layer.get("默认用途", ""),
        "默认限制": layer.get("默认限制", ""),
        "是否可作正式依据候选": bool(layer.get("是否可作正式依据候选", False)),
        "是否需要反向追溯": grade not in {"S1"},
        "人工复核重点": review_focus(grade),
    }


def review_focus(grade: str) -> list[str]:
    if grade == "S1":
        return ["时效", "完整性", "适用范围", "具体业务边界"]
    if grade == "S2":
        return ["统计口径", "发布机构", "与正式规则的一致性"]
    if grade == "S3":
        return ["学术观点适用范围", "研究方法", "是否需要官方依据支撑"]
    if grade == "S4":
        return ["报道时间", "原始出处", "是否需要官方原文支撑"]
    if grade == "S5":
        return ["转载来源", "原始出处", "反向追溯权威来源"]
    return ["来源真实性", "原始出处", "是否应阻断"]


def self_test(config: dict[str, Any]) -> dict[str, Any]:
    samples = {
        "国家官方": ("https://www.gov.cn/zhengce/index.htm", "S1"),
        "地方税务": ("https://shanghai.chinatax.gov.cn/zcfw/index.html", "S1"),
        "学术权威": ("https://www.pku.edu.cn/research/example.html", "S3"),
        "主流媒体": ("https://www.people.com.cn/example.html", "S4"),
        "商业门户": ("https://news.163.com/example.html", "S5"),
        "未知来源": ("https://example.com/example.html", "S6"),
    }
    results = []
    for name, (url, expected) in samples.items():
        item = classify_url(url, config)
        results.append({
            "样本": name,
            "URL": url,
            "期望等级": expected,
            "实际等级": item["可信度等级"],
            "通过": item["可信度等级"] == expected,
            "结果": item,
        })
    return {
        "样本数量": len(results),
        "通过数量": sum(1 for item in results if item["通过"]),
        "失败数量": sum(1 for item in results if not item["通过"]),
        "样本结果": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    config = load_json(module_root() / "01配置" / "信息来源可信度分层规则.json")
    if args.self_test:
        result = self_test(config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["失败数量"] == 0 else 1
    if not args.url:
        print(json.dumps({"错误": "请传入 --url 或 --self-test"}, ensure_ascii=False))
        return 2
    print(json.dumps(classify_url(args.url, config), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
