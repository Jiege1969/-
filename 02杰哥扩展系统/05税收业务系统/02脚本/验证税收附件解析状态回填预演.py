# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "19附件解析状态回填预演"
PREVIEW_JSON = OUT_DIR / "税收附件解析状态回填预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收附件解析状态回填预演_最新.md"
REPORT_JSON = OUT_DIR / "税收附件解析状态回填预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收附件解析状态回填预演验收_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    questions = preview.get("增强问题包复核清单", [])
    nodes = preview.get("增强证据节点", [])
    edges = preview.get("增强关系边", [])
    checks = []

    checks.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("附件解析数量大于0", preview.get("附件解析数量", 0) > 0, preview.get("附件解析数量", 0)))
    checks.append(check("问题清单数量大于0", len(questions) > 0, len(questions)))
    checks.append(check("至少回填一个问题", preview.get("回填问题数量", 0) > 0, preview.get("回填问题数量", 0)))
    checks.append(check("至少回填一个证据节点", preview.get("回填节点数量", 0) > 0, preview.get("回填节点数量", 0)))
    checks.append(check("至少回填一个附件关系边", preview.get("回填关系边数量", 0) > 0, preview.get("回填关系边数量", 0)))

    missing_review = [
        item.get("问题ID")
        for item in questions
        if "附件是否已解析" not in item.get("人工复核清单", {})
    ]
    checks.append(check("所有问题均有附件解析复核状态", not missing_review, missing_review))

    bad_support_nodes = [
        node.get("标题")
        for node in nodes
        if node.get("附件解析状态") and node.get("是否可作当前适用依据") is True
    ]
    checks.append(check("回填附件节点不得作为当前适用依据", not bad_support_nodes, bad_support_nodes))

    bad_support_edges = [
        edge.get("目标标题")
        for edge in edges
        if edge.get("附件解析状态") and edge.get("是否可支撑当前结论") is True
    ]
    checks.append(check("回填附件关系边不得支撑当前结论", not bad_support_edges, bad_support_edges))

    partial_without_blocker = [
        item.get("问题ID")
        for item in questions
        if item.get("附件解析状态") == "部分解析"
        and not any("轻量解析" in reason or "正式文档解析器" in reason for reason in item.get("当前阻断原因", []))
    ]
    checks.append(check("部分解析问题保留正式解析器阻断", not partial_without_blocker, partial_without_blocker))

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
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))
    checks.append(check("模式为回填预演", preview.get("模式") == "preview_only_no_runtime_change_backfill", preview.get("模式")))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收附件解析状态回填预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件解析状态回填预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
