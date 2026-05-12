"""
名称：核验税收政策官方来源.py
作用：基于本地政策全文索引和信息来源智能鉴别规则，识别政策来源链接属于国家官方、地方官方、学术权威、主流媒体、商业门户或低可信来源。
触发方式：python 核验税收政策官方来源.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只做本地来源身份智能鉴别，不联网抓取政策，不替代时效、附件、地方边界和具体业务适用复核。
创建/修改记录：2026-04-26 创建政策官方来源核验脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_host(link: str) -> str:
    parsed = urlparse(link.strip())
    host = parsed.netloc.lower()
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.strip(".")


def domain_match_score(host: str, domain: str) -> tuple[int, int] | None:
    normalized = domain.lower().strip(".")
    if not normalized:
        return None
    if normalized.startswith("*."):
        base = normalized[2:]
        if host.endswith(f".{base}") and host != base:
            return (1, len(base))
        return None
    if host == normalized:
        return (0, len(normalized))
    if host.endswith(f".{normalized}"):
        return (2, len(normalized))
    return None


def source_level(item: dict[str, Any]) -> str:
    if item.get("来源级别"):
        return str(item.get("来源级别"))
    name = str(item.get("名称", ""))
    domain = str(item.get("域名", ""))
    if "地方" in name or domain.startswith("*."):
        return "地方官方来源"
    if "政策法规库" in name or "总局" in name or "财政部" in name:
        return "中央官方来源"
    return "官方候选来源"


def review_focus_for_level(level: str) -> list[str]:
    common = ["文件时效", "附件解析", "适用期间"]
    if "地方官方" in level:
        return common + ["适用地区", "上位文件关系", "地方口径能否外推"]
    if "学术" in level:
        return ["研究结论适用范围", "与官方政策原文的一致性", "是否只是学术观点"]
    if "媒体" in level or "传播" in level:
        return ["反向追溯官方原文", "核验报道时间和原始出处", "不得单独作为正式政策依据"]
    if "低可信" in level or "未知" in level:
        return ["必须反向找到权威原始来源"]
    return common + ["具体业务适用判断"]


def expanded_source_rules(rules: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in rules.get("官方域名", []):
        enriched = dict(item)
        enriched.setdefault("可信度等级", "S1")
        enriched.setdefault("可作为正式政策依据", True)
        items.append(enriched)
    priority = 100
    for layer in rules.get("可信来源分层", []):
        for domain in layer.get("域名规则", []):
            items.append(
                {
                    "名称": layer.get("名称", ""),
                    "域名": domain,
                    "优先级": priority,
                    "可信度等级": layer.get("等级", ""),
                    "来源级别": layer.get("来源级别", ""),
                    "可作为正式政策依据": bool(layer.get("可作为正式政策依据", False)),
                    "使用边界": layer.get("使用边界", ""),
                }
            )
            priority += 1
    return items


def match_official_domain(host: str, official_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    matched = []
    for item in official_items:
        domain = str(item.get("域名", "")).lower().strip(".")
        score = domain_match_score(host, domain)
        if score is not None:
            matched.append((score, item))
    if not matched:
        return None
    _score, item = sorted(
        matched,
        key=lambda pair: (
            pair[0][0],
            int(pair[1].get("优先级", 999)),
            -pair[0][1],
        ),
    )[0]
    return item


def classify_link(link: str, official_items: list[dict[str, Any]]) -> dict[str, Any]:
    clean_link = str(link or "").strip()
    if not clean_link:
        return {
            "来源核验结论": "无来源链接",
            "匹配域名": "",
            "来源级别": "无来源",
            "可信度等级": "S6",
            "智能鉴别依据": "来源链接为空",
            "用途边界": "不得作为任何正式依据",
            "阻断原因": "来源链接为空",
            "来源名称": "",
            "可作为正式政策依据": False,
            "仍需人工复核事项": [],
        }
    if not clean_link.lower().startswith(("http://", "https://")):
        if "本地测试" in clean_link:
            return {
                "来源核验结论": "本地测试来源",
                "匹配域名": "",
                "来源级别": "本地测试",
                "可信度等级": "S6",
                "智能鉴别依据": "本地测试占位资料",
                "用途边界": "仅用于系统测试",
                "阻断原因": "本地测试文件不能作为正式依据",
                "来源名称": "",
                "可作为正式政策依据": False,
                "仍需人工复核事项": [],
            }
        return {
            "来源核验结论": "待人工核验",
            "匹配域名": "",
            "来源级别": "来源待补证",
            "可信度等级": "S6",
            "智能鉴别依据": "非标准网页链接",
            "用途边界": "必须补齐可追溯来源后才能判断",
            "阻断原因": "非标准网页链接，需人工核验来源",
            "来源名称": "",
            "可作为正式政策依据": False,
            "仍需人工复核事项": ["补齐可追溯官方链接"],
        }
    host = normalize_host(clean_link)
    matched = match_official_domain(host, official_items)
    if matched:
        level = source_level(matched)
        grade = str(matched.get("可信度等级", "S1"))
        can_formal_policy = bool(matched.get("可作为正式政策依据", grade == "S1"))
        if "地方官方" in level:
            conclusion = "地方官方来源已核验"
        elif can_formal_policy:
            conclusion = "官方来源已核验"
        elif grade in {"S2", "S3", "S4", "S5"}:
            conclusion = "可信来源已识别"
        else:
            conclusion = "来源已识别"
        return {
            "来源核验结论": conclusion,
            "匹配域名": matched.get("域名", ""),
            "来源级别": level,
            "可信度等级": grade,
            "智能鉴别依据": f"命中官方来源规则：{matched.get('名称', '')} / {matched.get('域名', '')}",
            "用途边界": matched.get("使用边界", "可信来源身份已识别，但仍需按业务场景判断用途边界。"),
            "阻断原因": "",
            "来源名称": matched.get("名称", ""),
            "可作为正式政策依据": can_formal_policy,
            "仍需人工复核事项": review_focus_for_level(level),
        }
    return {
        "来源核验结论": "非登记官方来源",
        "匹配域名": host,
        "来源级别": "非官方或未登记来源",
        "可信度等级": "S6",
        "智能鉴别依据": "未命中官方来源规则",
        "用途边界": "不得进入正式证据链，只能作为检索线索",
        "阻断原因": "来源域名未登记为官方来源",
        "来源名称": "",
        "可作为正式政策依据": False,
        "仍需人工复核事项": ["如需使用，必须反向找到官方原文"],
    }


def verify_official_sources() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "税收官方来源核验规则.json")
    latest_policy_index = root / "03数据" / "02分类索引" / "税收政策全文索引_最新.json"
    policy_index = load_json(latest_policy_index) if latest_policy_index.exists() else {}
    output_dir = root / "03数据" / "06依据过滤"
    output_dir.mkdir(parents=True, exist_ok=True)

    official_items = expanded_source_rules(rules)
    allowed_states = set(rules.get("有效状态允许值", []))
    results = []
    for policy in policy_index.get("政策文件", []):
        link_result = classify_link(policy.get("来源链接", ""), official_items)
        can_candidate = (
            link_result["来源核验结论"] in {"官方来源已核验", "地方官方来源已核验"}
            and link_result.get("可作为正式政策依据") is True
            and policy.get("可作为正式依据") is True
            and policy.get("有效状态") in allowed_states
        )
        block_reasons = []
        if link_result.get("阻断原因"):
            block_reasons.append(link_result["阻断原因"])
        if policy.get("有效状态") not in allowed_states:
            block_reasons.append(f"有效状态不在允许范围：{policy.get('有效状态', '未标注')}")
        if policy.get("可作为正式依据") is not True:
            block_reasons.append("政策全文索引未允许作为正式依据")
        results.append(
            {
                "政策ID": policy.get("政策ID", ""),
                "标题": policy.get("标题", policy.get("文件名", "")),
                "文号": policy.get("文号", ""),
                "来源链接": policy.get("来源链接", ""),
                "有效状态": policy.get("有效状态", "待核实"),
                "来源核验结论": link_result["来源核验结论"],
                "匹配域名": link_result["匹配域名"],
                "来源级别": link_result["来源级别"],
                "可信度等级": link_result["可信度等级"],
                "来源名称": link_result["来源名称"],
                "智能鉴别依据": link_result["智能鉴别依据"],
                "用途边界": link_result["用途边界"],
                "可作为正式政策依据": link_result["可作为正式政策依据"],
                "仍需人工复核事项": link_result["仍需人工复核事项"],
                "阻断原因": block_reasons,
                "是否可进入正式依据候选": can_candidate,
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "核验模式": rules.get("核验模式", "本地只读域名核验"),
        "是否联网核验": False,
        "是否替代人工判断": False,
        "政策索引来源": str(latest_policy_index),
        "核验结果": results,
        "统计": {
            "政策数量": len(results),
            "官方来源数量": sum(1 for item in results if item["来源核验结论"] in {"官方来源已核验", "地方官方来源已核验"}),
            "地方官方来源数量": sum(1 for item in results if item["来源核验结论"] == "地方官方来源已核验"),
            "可信来源数量": sum(1 for item in results if item["可信度等级"] in {"S1", "S2", "S3", "S4", "S5"}),
            "正式依据候选数量": sum(1 for item in results if item["是否可进入正式依据候选"]),
            "阻断数量": sum(1 for item in results if not item["是否可进入正式依据候选"]),
        },
        "安全说明": "来源身份由系统智能鉴别；时效、附件、地方边界和具体业务适用仍需人工复核。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收政策来源核验_{timestamp}.json"
    latest = output_dir / "税收政策来源核验_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"policy_count": len(results), "candidate_count": report["统计"]["正式依据候选数量"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    verify_official_sources()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
