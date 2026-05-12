# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收证据节点与关系图谱规则.json"
DOC = ROOT / "07文档" / "税收官方政策生态证据化行动方案.md"
SMART_PIPELINE_CONFIG = ROOT / "01配置" / "税收政策智能查询下载管道配置.json"
POLICY_ENTRY_RULES = ROOT / "01配置" / "税收政策入库规则.json"
FORMAL_INDEX = ROOT / "03数据" / "13智能政策下载管道" / "正式依据库" / "正式依据索引_最新.json"
OUT_DIR = ROOT / "03数据" / "14证据关系机制"
REPORT_MD = OUT_DIR / "税收证据节点与关系图谱规则验收_最新.md"
REPORT_JSON = OUT_DIR / "税收证据节点与关系图谱规则验收_最新.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    cfg = load_json(CONFIG) if CONFIG.exists() else {}
    doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    pipeline_cfg = load_json(SMART_PIPELINE_CONFIG) if SMART_PIPELINE_CONFIG.exists() else {}
    entry_rules = load_json(POLICY_ENTRY_RULES) if POLICY_ENTRY_RULES.exists() else {}
    formal_index = load_json(FORMAL_INDEX) if FORMAL_INDEX.exists() else {}

    results.append(check("证据规则配置存在", CONFIG.exists(), str(CONFIG)))
    results.append(check("行动方案文档存在", DOC.exists(), str(DOC)))
    results.append(check("智能下载管道配置仍存在", SMART_PIPELINE_CONFIG.exists(), str(SMART_PIPELINE_CONFIG)))
    results.append(check("政策入库规则仍存在", POLICY_ENTRY_RULES.exists(), str(POLICY_ENTRY_RULES)))
    results.append(check("正式依据索引仍存在", FORMAL_INDEX.exists(), str(FORMAL_INDEX)))

    layers = cfg.get("资料四层", {})
    required_layers = ["正式依据", "解释材料", "答疑材料", "关联材料"]
    results.append(check("资料四层齐备", all(k in layers for k in required_layers), list(layers.keys())))

    layer_tags = [layers.get(k, {}).get("标签") for k in required_layers]
    results.append(check("四层标签齐备", all(layer_tags), layer_tags))

    legal_basis = layers.get("正式依据", {})
    results.append(check("正式依据可支撑当前结论", legal_basis.get("是否可支撑当前结论") is True, legal_basis))
    for name in ["解释材料", "答疑材料", "关联材料"]:
        results.append(check(f"{name}不得单独支撑当前结论", layers.get(name, {}).get("是否可支撑当前结论") is False, layers.get(name, {})))

    evidence_fields = cfg.get("证据卡最小字段", [])
    required_fields = ["证据ID", "资料类别", "标题", "文号", "文件时效", "来源链接", "原文哈希", "是否可作当前适用依据", "阻断原因", "关联证据ID列表"]
    results.append(check("证据卡关键字段齐备", all(f in evidence_fields for f in required_fields), evidence_fields))
    no_inherited_doc_no = "引用文件文号" in entry_rules.get("风险规则", {}) and "不得自动写入本资料文号字段" in entry_rules.get("风险规则", {}).get("引用文件文号", "") and "不得继承被引用文件" in doc_text
    results.append(check("证据卡不得继承引用文件文号", no_inherited_doc_no, entry_rules.get("风险规则", {}).get("引用文件文号", "")))

    source_rules = cfg.get("官方来源智能鉴别规则", {})
    results.append(check("官方来源智能鉴别规则已纳入证据图谱配置", bool(source_rules), source_rules))
    auto_scope = " ".join(source_rules.get("自动识别范围", []))
    results.append(check("自动识别范围包含各级地方税务局", "各级地方税务局" in auto_scope, source_rules.get("自动识别范围", [])))
    machine_work = " ".join(source_rules.get("系统自动负责", []))
    human_work = " ".join(source_rules.get("人工复核负责", []))
    results.append(check("系统负责来源身份识别", "域名" in machine_work and "最终链接" in machine_work, source_rules.get("系统自动负责", [])))
    results.append(check("人工复核聚焦高风险判断", "地方口径" in human_work and "具体企业事实" in human_work, source_rules.get("人工复核负责", [])))
    trust_layers = cfg.get("信息来源可信度分层", [])
    trust_text = json.dumps(trust_layers, ensure_ascii=False)
    results.append(check("信息来源可信度分层齐备", all(level in trust_text for level in ["S1", "S2", "S3", "S4", "S5", "S6"]), trust_layers))
    results.append(check("商业门户不得直接进入正式证据链", "反向追溯" in trust_text and "大型商业门户" in trust_text, trust_layers))

    relations = cfg.get("关系类型", {})
    required_relations = ["解释", "答疑", "关联", "修改", "废止", "替代", "引用", "附件", "地方补充", "同主题"]
    results.append(check("关系类型齐备", all(k in relations for k in required_relations), relations))

    answer_rules = cfg.get("回答分层规则", {})
    results.append(check("回答分层包含微信端", "微信端" in answer_rules, answer_rules.get("微信端")))
    results.append(check("回答分层包含本地详情页", "本地详情页" in answer_rules, answer_rules.get("本地详情页")))
    results.append(check("无依据处理规则存在", "无依据处理" in answer_rules and any("不得编造" in item for item in answer_rules.get("无依据处理", [])), answer_rules.get("无依据处理")))

    safety = cfg.get("安全边界", {})
    high_risk_closed = all(safety.get(k) is False for k in [
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否生成正式税务结论",
        "是否重启服务",
        "是否影响股票系统",
    ])
    results.append(check("高风险动作全部关闭", high_risk_closed, safety))

    actions = cfg.get("行动阶段", [])
    statuses = {item.get("阶段"): item.get("状态") for item in actions}
    results.append(check("行动阶段A-E齐备", all(stage in statuses for stage in ["A", "B", "C", "D", "E"]), statuses))
    results.append(check("当前只完成规则固化", statuses.get("A") == "本次完成" and statuses.get("B") == "下一步", statuses))
    results.append(check("RAG和企业微信灰度需另行确认", statuses.get("E") == "必须另行停下确认", statuses))

    doc_required = ["资料不是文件", "证据节点", "政策关系图谱", "微信端", "当前仍禁止"]
    results.append(check("行动方案关键表述齐备", all(word in doc_text for word in doc_required), doc_required))

    pipeline_safety = pipeline_cfg.get("安全边界", {})
    results.append(check("沿用智能下载管道安全边界", pipeline_safety.get("是否触发n8n") is False and pipeline_safety.get("是否企业微信真实发送") is False, pipeline_safety))

    results.append(check("正式依据索引可读", isinstance(formal_index.get("资料", []), list), {"资料数量": formal_index.get("资料数量"), "当前适用数量": formal_index.get("当前适用数量")}))

    passed = sum(1 for item in results if item["结果"] == "通过")
    failed = len(results) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收证据节点与关系图谱规则验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": results,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收证据节点与关系图谱规则验收",
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
    lines.extend([
        "",
        "## 安全边界",
        "",
    ])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
