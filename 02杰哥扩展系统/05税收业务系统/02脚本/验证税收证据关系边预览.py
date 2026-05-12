# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
PIPELINE_DIR = ROOT / "03数据" / "13智能政策下载管道"
FORMAL_INDEX = PIPELINE_DIR / "正式依据库" / "正式依据索引_最新.json"
OUT_DIR = ROOT / "03数据" / "14证据关系机制"
PREVIEW_JSON = OUT_DIR / "税收证据关系边预览_最新.json"
PREVIEW_MD = OUT_DIR / "税收证据关系边预览_最新.md"
REPORT_JSON = OUT_DIR / "税收证据关系边预览验收_最新.json"
REPORT_MD = OUT_DIR / "税收证据关系边预览验收_最新.md"


REQUIRED_NODE_FIELDS = [
    "证据ID",
    "资料类别",
    "标题",
    "文件时效",
    "来源链接",
    "最终链接",
    "是否可作当前适用依据",
    "阻断原因",
    "关联证据ID列表",
]

REQUIRED_EDGE_FIELDS = [
    "关系ID",
    "来源证据ID",
    "关系类型",
    "关系标签",
    "目标证据ID",
    "目标标题",
    "是否可支撑当前结论",
    "阻断原因",
    "人工复核状态",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    formal = load_json(FORMAL_INDEX) if FORMAL_INDEX.exists() else {}
    nodes = preview.get("节点", [])
    edges = preview.get("关系边", [])
    node_ids = {node.get("证据ID") for node in nodes}
    edge_ids = [edge.get("关系ID") for edge in edges]
    formal_count = int(formal.get("当前适用数量") or formal.get("资料数量") or 0)
    expected_appendix_count = sum(len(item.get("附件", [])) for item in formal.get("资料", []))

    results = []
    results.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    results.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    results.append(check("正式依据索引存在", FORMAL_INDEX.exists(), str(FORMAL_INDEX)))
    results.append(check("节点数量不少于正式依据数量", len(nodes) >= formal_count, {"节点": len(nodes), "正式依据": formal_count}))
    results.append(check("关系边数量大于0", len(edges) > 0, len(edges)))
    results.append(check("附件边数量覆盖正式依据附件", preview.get("附件边数量", 0) >= expected_appendix_count, {"附件边": preview.get("附件边数量"), "正式依据附件": expected_appendix_count}))
    results.append(check("存在引用或同主题关系", preview.get("引用边数量", 0) + preview.get("同主题边数量", 0) > 0, {"引用": preview.get("引用边数量"), "同主题": preview.get("同主题边数量")}))
    results.append(check("正式依据节点数量正确", preview.get("正式依据节点数量", 0) == formal_count, {"声明": preview.get("正式依据节点数量"), "正式依据": formal_count}))

    missing_node_fields = [
        {"证据ID": node.get("证据ID"), "缺字段": [field for field in REQUIRED_NODE_FIELDS if field not in node]}
        for node in nodes
        if any(field not in node for field in REQUIRED_NODE_FIELDS)
    ]
    results.append(check("节点字段齐备", not missing_node_fields, missing_node_fields))

    missing_edge_fields = [
        {"关系ID": edge.get("关系ID"), "缺字段": [field for field in REQUIRED_EDGE_FIELDS if field not in edge]}
        for edge in edges
        if any(field not in edge for field in REQUIRED_EDGE_FIELDS)
    ]
    results.append(check("关系边字段齐备", not missing_edge_fields, missing_edge_fields))

    bad_sources = [edge for edge in edges if edge.get("来源证据ID") not in node_ids]
    results.append(check("所有关系边来源节点存在", not bad_sources, bad_sources[:5]))

    duplicated_edges = len(edge_ids) != len(set(edge_ids))
    results.append(check("关系边ID无重复", not duplicated_edges, {"关系边数量": len(edge_ids), "唯一数量": len(set(edge_ids))}))

    non_formal_support = [
        node for node in nodes
        if node.get("资料类别") != "正式依据" and node.get("是否可作当前适用依据") is True
    ]
    results.append(check("非正式依据节点不得支撑当前结论", not non_formal_support, non_formal_support[:5]))

    formal_blocked = [
        node for node in nodes
        if node.get("资料类别") == "正式依据" and node.get("是否可作当前适用依据") is not True
    ]
    results.append(check("正式依据节点可作当前适用依据", not formal_blocked, formal_blocked[:5]))

    unsafe_edges = [edge for edge in edges if edge.get("关系类型") != "引用" and edge.get("是否可支撑当前结论") is True]
    results.append(check("关系边不直接支撑当前结论", not unsafe_edges, unsafe_edges[:5]))

    safety = preview.get("安全边界", {})
    required_false = [
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否生成正式税务结论",
        "是否新增端口",
        "是否重启服务",
        "是否影响股票系统",
    ]
    results.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in results if item["结果"] == "通过")
    failed = len(results) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收证据关系边预览验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": results,
        "统计": {
            "节点数量": len(nodes),
            "关系边数量": len(edges),
            "附件边数量": preview.get("附件边数量", 0),
            "引用边数量": preview.get("引用边数量", 0),
            "关联边数量": preview.get("关联边数量", 0),
            "同主题边数量": preview.get("同主题边数量", 0),
            "正式依据节点数量": preview.get("正式依据节点数量", 0),
            "待核验节点数量": preview.get("待核验节点数量", 0),
        },
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收证据关系边预览验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 统计",
        "",
    ]
    for key, value in report["统计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 检查结果", ""])
    for item in results:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
