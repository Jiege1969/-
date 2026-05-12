# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
PIPELINE_DIR = ROOT / "03数据" / "13智能政策下载管道"
FORMAL_INDEX = PIPELINE_DIR / "正式依据库" / "正式依据索引_最新.json"
META_DIR = PIPELINE_DIR / "元数据区"
RAW_DIR = PIPELINE_DIR / "原始下载区"
TEXT_DIR = PIPELINE_DIR / "解析文本区"
OUT_DIR = ROOT / "03数据" / "14证据关系机制"
OUT_JSON = OUT_DIR / "税收证据关系边预览_最新.json"
OUT_MD = OUT_DIR / "税收证据关系边预览_最新.md"


RELATION_LABELS = {
    "附件": "appendix",
    "引用": "cite",
    "同主题": "same_topic",
    "关联": "related_to",
    "废止": "abolish",
    "修改": "modify",
}

NO_RUNTIME_CHANGE = {
    "是否触发n8n": False,
    "是否企业微信真实发送": False,
    "是否写向量库": False,
    "是否调用模型推理": False,
    "是否生成正式税务结论": False,
    "是否新增端口": False,
    "是否重启服务": False,
    "是否影响股票系统": False,
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def stable_id(prefix: str, *parts: str) -> str:
    text = "|".join(str(p) for p in parts if p is not None)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def clean_text(value: str) -> str:
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_url(base: str, href: str) -> str:
    href = (href or "").strip()
    if not href or href.startswith("javascript:") or href.startswith("#"):
        return ""
    return urljoin(base or "https://fgk.chinatax.gov.cn/", href)


def find_saved_path(item: dict, kind: str) -> str:
    paths = item.get("保存路径", {}) if isinstance(item.get("保存路径"), dict) else {}
    if kind in paths:
        return paths[kind]
    item_id = item.get("资料ID", "")
    title = item.get("标题", "")
    candidates = {
        "原始文件": RAW_DIR / f"{item_id}_{title}.html",
        "解析文本": TEXT_DIR / f"{item_id}_{title}.txt",
        "元数据": META_DIR / f"{item_id}_{title}.元数据.json",
    }
    path = candidates.get(kind)
    return str(path) if path and path.exists() else ""


def material_category(item: dict) -> tuple[str, str]:
    column = f"{item.get('栏目', '')} {item.get('标签', '')} {item.get('标题', '')}"
    if item.get("可作为当前适用依据") and item.get("文件时效") == "全文有效":
        return "正式依据", "legal_basis"
    if "解读" in column or "案例" in column:
        return "解释材料", "interpretive_guide"
    if "问答" in column or "答疑" in column or "12366" in column:
        return "答疑材料", "practical_qa"
    return "关联材料", "related_material"


def keywords_for(item: dict) -> list[str]:
    text = " ".join([
        item.get("标题", ""),
        item.get("文号", ""),
        item.get("税费政策分类", ""),
        item.get("二级税费政策分类", ""),
        item.get("标签", ""),
    ])
    keywords = []
    for word in ["企业所得税", "研发费用加计扣除", "研发费用", "预缴申报", "年度纳税申报", "工业母机", "税费征管"]:
        if word in text and word not in keywords:
            keywords.append(word)
    if not keywords and item.get("标题"):
        keywords.append(item["标题"][:12])
    return keywords


def make_node(item: dict, meta_path: str = "") -> dict:
    category, tag = material_category(item)
    can_support = category == "正式依据"
    blockers = list(item.get("阻断原因", []))
    if not can_support and not blockers:
        blockers.append("非正式依据或时效未核验，不得作为当前适用依据。")
    return {
        "证据ID": stable_id("tax", item.get("资料ID", ""), item.get("标题", ""), item.get("原文哈希", "")),
        "资料ID": item.get("资料ID", ""),
        "资料类别": category,
        "资料标签": tag,
        "标题": item.get("标题", ""),
        "文号": item.get("文号", ""),
        "发文机关": item.get("发文机关") or item.get("来源名称", ""),
        "发布日期": item.get("发布日期", ""),
        "施行日期": item.get("施行日期", ""),
        "文件时效": item.get("文件时效", "") or "时效缺失",
        "来源名称": item.get("来源名称", ""),
        "来源链接": item.get("来源链接", ""),
        "最终链接": item.get("最终链接", ""),
        "适用税种": item.get("二级税费政策分类") or item.get("税费政策分类", ""),
        "关键词": keywords_for(item),
        "摘要": f"{item.get('栏目', '')}；{item.get('标签', '')}；正文字符数={item.get('正文字符数', '')}",
        "下载时间": item.get("下载时间", ""),
        "原文哈希": item.get("原文哈希", ""),
        "本地原文路径": find_saved_path(item, "原始文件"),
        "本地解析文本路径": find_saved_path(item, "解析文本"),
        "本地元数据路径": meta_path or find_saved_path(item, "元数据"),
        "是否可作当前适用依据": can_support,
        "阻断原因": [] if can_support else blockers,
        "关联证据ID列表": [],
        "人工复核状态": "未人工复核",
        "最后复核时间": "",
    }


def make_edge(source_id: str, relation: str, target_id: str, target_title: str, target_link: str = "", source_field: str = "", support: bool = False, blockers: list[str] | None = None) -> dict:
    blockers = blockers or []
    if not support and not blockers:
        blockers = ["关系边仅用于证据链导航，不能单独支撑当前适用结论。"]
    return {
        "关系ID": stable_id("tax-edge", source_id, relation, target_id, target_title, target_link),
        "来源证据ID": source_id,
        "关系类型": relation,
        "关系标签": RELATION_LABELS[relation],
        "目标证据ID": target_id,
        "目标标题": target_title,
        "目标链接或本地路径": target_link,
        "来源字段": source_field,
        "是否可支撑当前结论": support,
        "阻断原因": blockers,
        "置信等级": "高" if relation == "附件" else "中",
        "人工复核状态": "未人工复核",
    }


def load_all_metadata() -> list[tuple[dict, str]]:
    by_id: dict[str, tuple[dict, str]] = {}
    if FORMAL_INDEX.exists():
        formal = load_json(FORMAL_INDEX)
        for item in formal.get("资料", []):
            by_id[item.get("资料ID", "")] = (item, item.get("保存路径", {}).get("元数据", ""))
    for path in sorted(META_DIR.glob("*.元数据.json")):
        item = load_json(path)
        by_id.setdefault(item.get("资料ID", ""), (item, str(path)))
    return [value for key, value in sorted(by_id.items()) if key]


def extract_html_links(node: dict) -> list[dict]:
    raw_path = node.get("本地原文路径") or ""
    if not raw_path:
        return []
    path = Path(raw_path)
    if not path.is_file():
        return []
    html = path.read_text(encoding="utf-8", errors="ignore")
    base = node.get("最终链接") or node.get("来源链接") or "https://fgk.chinatax.gov.cn/"
    links = []
    for match in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, flags=re.I | re.S):
        href = normalize_url(base, match.group(1))
        title = clean_text(match.group(2))
        if not href or not title:
            continue
        if "/zcfgk/c" not in href:
            continue
        if title in ["首页", "政策法规", "文件", "解读", "搜索", "高级搜索"]:
            continue
        links.append({"标题": title, "链接": href})
    unique = {}
    for link in links:
        unique.setdefault((link["标题"], link["链接"]), link)
    return list(unique.values())


def extract_citations(node: dict) -> list[str]:
    raw_path = node.get("本地解析文本路径") or ""
    if not raw_path:
        return []
    path = Path(raw_path)
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    titles = re.findall(r"《([^》]{6,80})》", text)
    wenhao = re.findall(r"[\u4e00-\u9fa5]{1,12}〔\d{4}〕\d+号|国家税务总局公告\d{4}年第\d+号", text)
    citations = []
    for item in titles + wenhao:
        item = clean_text(item)
        if item and item not in citations and item not in node.get("标题", ""):
            citations.append(item)
    return citations[:12]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = load_all_metadata()
    nodes = [make_node(item, meta_path) for item, meta_path in metadata]
    node_by_id = {node["证据ID"]: node for node in nodes}
    title_to_id = {node["标题"]: node["证据ID"] for node in nodes}
    edges = []

    for item, _meta_path in metadata:
        source = make_node(item)
        source_id = source["证据ID"]
        for appendix in item.get("附件", []):
            target_title = appendix.get("标题", "")
            target_link = appendix.get("链接", "")
            target_id = stable_id("tax-appendix", source_id, target_title, target_link)
            if target_id not in node_by_id:
                node_by_id[target_id] = {
                    "证据ID": target_id,
                    "资料类别": "关联材料",
                    "资料标签": "appendix",
                    "标题": target_title,
                    "文号": "",
                    "发文机关": source.get("发文机关", ""),
                    "发布日期": source.get("发布日期", ""),
                    "施行日期": "",
                    "文件时效": source.get("文件时效", "时效缺失"),
                    "来源名称": "国家税务总局政策法规库附件",
                    "来源链接": target_link,
                    "最终链接": target_link,
                    "适用税种": source.get("适用税种", ""),
                    "关键词": source.get("关键词", []),
                    "摘要": f"附件后缀={appendix.get('后缀', '')}",
                    "下载时间": source.get("下载时间", ""),
                    "原文哈希": "",
                    "本地原文路径": "",
                    "本地解析文本路径": "",
                    "本地元数据路径": "",
                    "是否可作当前适用依据": False,
                    "阻断原因": ["附件需下载并解析后才能进入正式依据链。"],
                    "关联证据ID列表": [],
                    "人工复核状态": "未人工复核",
                    "最后复核时间": "",
                }
            edges.append(make_edge(source_id, "附件", target_id, target_title, target_link, "附件", support=False))

        for link in extract_html_links(source):
            target_id = title_to_id.get(link["标题"], stable_id("tax-link", link["标题"], link["链接"]))
            edges.append(make_edge(source_id, "关联", target_id, link["标题"], link["链接"], "原始HTML链接", support=False))

        for citation in extract_citations(source):
            target_id = title_to_id.get(citation, stable_id("tax-citation", citation))
            relation = "引用"
            if "废止" in citation:
                relation = "废止"
            elif "修改" in citation:
                relation = "修改"
            edges.append(make_edge(source_id, relation, target_id, citation, "", "解析文本引用", support=False))

    nodes = list(node_by_id.values())
    for i, left in enumerate(nodes):
        if left.get("资料标签") == "appendix":
            continue
        for right in nodes[i + 1:]:
            if right.get("资料标签") == "appendix":
                continue
            shared = sorted(set(left.get("关键词", [])) & set(right.get("关键词", [])))
            if not shared:
                continue
            edges.append(make_edge(
                left["证据ID"],
                "同主题",
                right["证据ID"],
                right.get("标题", ""),
                right.get("最终链接", ""),
                f"共享关键词：{','.join(shared)}",
                support=False,
            ))

    unique_edges = {}
    for edge in edges:
        unique_edges.setdefault(edge["关系ID"], edge)
    edges = list(unique_edges.values())

    for edge in edges:
        source = node_by_id.get(edge["来源证据ID"])
        if source is not None and edge["目标证据ID"] not in source["关联证据ID列表"]:
            source["关联证据ID列表"].append(edge["目标证据ID"])

    preview = {
        "名称": "税收证据关系边预览",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change",
        "来源": {
            "正式依据索引": str(FORMAL_INDEX),
            "元数据区": str(META_DIR),
            "原始下载区": str(RAW_DIR),
            "解析文本区": str(TEXT_DIR),
        },
        "节点数量": len(nodes),
        "关系边数量": len(edges),
        "附件边数量": sum(1 for edge in edges if edge["关系类型"] == "附件"),
        "引用边数量": sum(1 for edge in edges if edge["关系类型"] == "引用"),
        "关联边数量": sum(1 for edge in edges if edge["关系类型"] == "关联"),
        "同主题边数量": sum(1 for edge in edges if edge["关系类型"] == "同主题"),
        "正式依据节点数量": sum(1 for node in nodes if node.get("是否可作当前适用依据") is True),
        "待核验节点数量": sum(1 for node in nodes if node.get("是否可作当前适用依据") is False),
        "节点": nodes,
        "关系边": edges,
        "安全边界": NO_RUNTIME_CHANGE,
        "下一步建议": [
            "对关联链接执行受控下载和元数据补齐。",
            "将附件下载解析后回填附件节点本地路径。",
            "把引用到的外部政策与本地正式依据库做标题、文号和链接匹配。",
            "仍不接企业微信、不写向量库、不生成正式税务结论。",
        ],
    }
    OUT_JSON.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收证据关系边预览",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change",
        f"- 节点数量：{preview['节点数量']}",
        f"- 关系边数量：{preview['关系边数量']}",
        f"- 附件边数量：{preview['附件边数量']}",
        f"- 引用边数量：{preview['引用边数量']}",
        f"- 关联边数量：{preview['关联边数量']}",
        f"- 同主题边数量：{preview['同主题边数量']}",
        f"- 正式依据节点数量：{preview['正式依据节点数量']}",
        f"- 待核验节点数量：{preview['待核验节点数量']}",
        "",
        "## 节点摘要",
        "",
    ]
    for node in nodes:
        lines.extend([
            f"### {node['标题']}",
            f"- 证据ID：{node['证据ID']}",
            f"- 资料类别：{node['资料类别']}",
            f"- 文件时效：{node['文件时效']}",
            f"- 是否可作当前适用依据：{node['是否可作当前适用依据']}",
            f"- 关联数量：{len(node.get('关联证据ID列表', []))}",
            "",
        ])
    lines.extend(["## 关系边摘要", ""])
    for edge in edges:
        lines.append(f"- [{edge['关系类型']}] {edge['来源证据ID']} -> {edge['目标标题']}（{edge['来源字段']}）")
    lines.extend(["", "## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "节点数量": len(nodes), "关系边数量": len(edges), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
