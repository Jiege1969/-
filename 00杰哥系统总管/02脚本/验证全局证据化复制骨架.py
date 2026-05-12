# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
GLOBAL_RULE = ROOT / "00杰哥系统总管" / "01配置" / "全局证据节点与关系管理规则.json"
COPY_RULE = ROOT / "00杰哥系统总管" / "01配置" / "新业务系统复制搭建规则.json"
MIGRATION_RULE = ROOT / "03杰哥进化系统" / "01配置" / "方法迁移规则.json"
METHOD_DOC = ROOT / "02杰哥扩展系统" / "07文档" / "扩展系统证据化复制骨架方法论.md"
TAX_RULE = ROOT / "02杰哥扩展系统" / "05税收业务系统" / "01配置" / "税收证据节点与关系图谱规则.json"
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "证据化复制骨架"
REPORT_MD = OUT_DIR / "全局证据化复制骨架验收_最新.md"
REPORT_JSON = OUT_DIR / "全局证据化复制骨架验收_最新.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    global_rule = load_json(GLOBAL_RULE) if GLOBAL_RULE.exists() else {}
    copy_rule = load_json(COPY_RULE) if COPY_RULE.exists() else {}
    migration_rule = load_json(MIGRATION_RULE) if MIGRATION_RULE.exists() else {}
    tax_rule = load_json(TAX_RULE) if TAX_RULE.exists() else {}
    method_doc = METHOD_DOC.read_text(encoding="utf-8") if METHOD_DOC.exists() else ""

    results.append(check("全局证据规则存在", GLOBAL_RULE.exists(), str(GLOBAL_RULE)))
    results.append(check("扩展系统方法论文档存在", METHOD_DOC.exists(), str(METHOD_DOC)))
    results.append(check("新业务复制规则存在", COPY_RULE.exists(), str(COPY_RULE)))
    results.append(check("进化方法迁移规则存在", MIGRATION_RULE.exists(), str(MIGRATION_RULE)))
    results.append(check("税收证据规则可作为首个落地样板", TAX_RULE.exists(), str(TAX_RULE)))

    principles = global_rule.get("工程原则", [])
    results.append(check("工程原则包含证据节点", any("证据节点" in item for item in principles), principles))
    results.append(check("工程原则包含关系管理器", any("证据关系管理器" in item for item in principles), principles))

    layers = global_rule.get("四层资料模型", {})
    required_layers = ["正式依据", "解释材料", "答疑材料", "关联材料"]
    results.append(check("全局四层资料模型齐备", all(k in layers for k in required_layers), list(layers.keys())))

    mappings = global_rule.get("各业务映射", {})
    required_business = ["股票研究系统", "税收业务系统", "文稿质检与办公材料系统", "视频制作系统", "知识库与资料检索系统"]
    results.append(check("业务映射覆盖关键扩展系统", all(k in mappings for k in required_business), list(mappings.keys())))

    evidence_fields = global_rule.get("证据卡最小字段", [])
    required_fields = ["证据ID", "业务系统", "资料类别", "来源主体", "状态", "是否可支撑当前结论", "关联证据ID列表", "人工复核状态"]
    results.append(check("全局证据卡关键字段齐备", all(f in evidence_fields for f in required_fields), evidence_fields))

    relations = global_rule.get("通用关系类型", [])
    required_relations = ["解释", "答疑", "关联", "修改", "废止", "替代", "引用", "附件", "上下游", "复盘验证"]
    results.append(check("全局通用关系类型齐备", all(r in relations for r in required_relations), relations))

    output_rules = global_rule.get("分层输出规则", {})
    results.append(check("全局输出分层齐备", all(k in output_rules for k in ["短输出", "详情输出", "无依据输出"]), output_rules))

    skeleton_requirements = global_rule.get("复制骨架要求", [])
    results.append(check("复制骨架要求包含四层映射", any("四层资料" in item for item in skeleton_requirements), skeleton_requirements))
    results.append(check("复制骨架要求包含证据卡", any("证据卡" in item for item in skeleton_requirements), skeleton_requirements))
    results.append(check("复制骨架要求包含无依据处理", any("无依据" in item for item in skeleton_requirements), skeleton_requirements))

    safety = global_rule.get("安全边界", {})
    high_risk_closed = all(safety.get(k) is False for k in [
        "是否自动生成正式结论",
        "是否绕过人工复核",
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否重启服务",
        "是否影响股票系统",
    ])
    results.append(check("全局高风险动作默认关闭", high_risk_closed, safety))

    allowed_copy = copy_rule.get("复制对象", {}).get("允许复制", [])
    required_copy_terms = ["证据节点与证据卡模板", "关系类型和关系图谱模板", "分层引用和无依据降级模板"]
    results.append(check("新业务复制规则已纳入证据化骨架", all(term in allowed_copy for term in required_copy_terms), allowed_copy))

    required_declarations = ["四层资料映射", "证据卡字段", "关系类型", "无依据降级规则"]
    declarations = copy_rule.get("新系统必须声明", [])
    results.append(check("新系统必须声明证据化字段", all(term in declarations for term in required_declarations), declarations))

    methods = migration_rule.get("可迁移方法", [])
    results.append(check("进化方法迁移纳入证据关系管理", any(item.get("方法名") == "证据关系管理" for item in methods), methods))

    doc_terms = ["资料不是文件", "四层资料模型", "各业务映射", "证据卡字段", "复制准入"]
    results.append(check("扩展系统方法论文档关键章节齐备", all(term in method_doc for term in doc_terms), doc_terms))

    tax_layers = tax_rule.get("资料四层", {})
    results.append(check("税收样板与全局四层模型一致", all(k in tax_layers for k in required_layers), list(tax_layers.keys())))

    passed = sum(1 for item in results if item["结果"] == "通过")
    failed = len(results) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "全局证据化复制骨架验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": results,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 全局证据化复制骨架验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
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
