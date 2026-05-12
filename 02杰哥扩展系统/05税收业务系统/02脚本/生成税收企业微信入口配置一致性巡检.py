# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信入口配置一致性巡检.py
作用：巡检企业微信正式入口配置、门禁条件、报告产物和全链路预检是否一致。
安全边界：只读本地配置和报告；不读取凭据、不联网、不真实发送、不修改配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
COMPLIANCE_RULE = ROOT / "01配置" / "税收企业微信消息合规审查规则.json"
INPUT_CONTRACT = ROOT / "01配置" / "税收企业微信输入消息契约.json"
RECEIVE_DESIGN = ROOT / "01配置" / "税收企业微信消息接收服务设计.json"
QUEUE_RULE = ROOT / "01配置" / "税收企业微信本地输入队列规则.json"
SHADOW_FLOW_RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
ANALYSIS_INPUT_RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
ANALYSIS_DRAFT_RULE = ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
ANALYSIS_SUMMARY_RULE = ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信入口配置一致性巡检_最新.json"
OUT_MD = OUT_DIR / "税收企业微信入口配置一致性巡检_最新.md"


EXPECTED_CONFIG_SECTIONS = [
    "机器人终端",
    "凭据配置",
    "人工放行",
    "接收范围治理",
    "应急停用与回滚",
    "上线变更管理",
    "发送前门禁",
    "消息格式",
    "安全边界",
]

EXPECTED_GATE_PHRASES = [
    "入口状态为real_send_enabled",
    "真实发送放行为true",
    "存在有效企业微信凭据",
    "凭据接入预检和预检验收通过",
    "消息预演验收通过",
    "消息合规审查报告和验收通过",
    "人工放行清单状态为approved",
    "接收范围清单状态为approved",
    "应急停用与回滚预案状态为approved且未触发紧急停用",
    "真实发送上线变更单状态为approved",
]

EXPECTED_REPORTS = {
    "机器人终端绑定验收": OUT_DIR / "税收企业微信机器人终端绑定报告验收_最新.json",
    "公共组件对齐核实验收": OUT_DIR / "税收企业微信公共组件对齐核实报告验收_最新.json",
    "输入消息契约样例验收": OUT_DIR / "税收企业微信输入消息契约样例验收_最新.json",
    "消息接收服务设计验收": OUT_DIR / "税收企业微信消息接收服务设计报告验收_最新.json",
    "本地输入队列预演验收": OUT_DIR / "税收企业微信本地输入队列预演验收_最新.json",
    "输入队列证据匹配影子流转验收": OUT_DIR / "税收企业微信输入队列证据匹配影子流转验收_最新.json",
    "证据匹配到分析契约输入包验收": OUT_DIR / "税收企业微信证据匹配到分析契约输入包验收_最新.json",
    "分析契约输入包到待复核草案骨架验收": OUT_DIR / "税收企业微信分析契约输入包到待复核草案骨架验收_最新.json",
    "待复核草案骨架到分析摘要预演验收": OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演验收_最新.json",
    "消息预演验收": OUT_DIR / "税收企业微信正式入口消息预演验收_最新.json",
    "消息合规审查验收": OUT_DIR / "税收企业微信消息合规审查报告验收_最新.json",
    "凭据预检验收": OUT_DIR / "税收企业微信凭据接入预检验收_最新.json",
    "接收范围验收": OUT_DIR / "税收企业微信接收范围与消息分级验收_最新.json",
    "回滚预案验收": OUT_DIR / "税收企业微信应急停用与回滚预案验收_最新.json",
    "准备清单验收": OUT_DIR / "税收企业微信真实发送准备清单验收_最新.json",
    "上线变更单验收": OUT_DIR / "税收企业微信真实发送上线变更单验收_最新.json",
    "发送门禁验收": OUT_DIR / "税收企业微信正式入口发送门禁验收_最新.json",
    "审计汇总验收": OUT_DIR / "税收企业微信发送审计台账汇总验收_最新.json",
    "上线矩阵验收": OUT_DIR / "税收企业微信上线就绪度矩阵验收_最新.json",
    "反事实演练验收": OUT_DIR / "税收企业微信门禁反事实演练验收_最新.json",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def item(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"巡检项": name, "是否一致": ok, "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    compliance = load_json(COMPLIANCE_RULE)
    input_contract = load_json(INPUT_CONTRACT)
    receive_design = load_json(RECEIVE_DESIGN)
    queue_rule = load_json(QUEUE_RULE)
    shadow_flow_rule = load_json(SHADOW_FLOW_RULE)
    analysis_input_rule = load_json(ANALYSIS_INPUT_RULE)
    analysis_draft_rule = load_json(ANALYSIS_DRAFT_RULE)
    analysis_summary_rule = load_json(ANALYSIS_SUMMARY_RULE)
    gate_phrases = config.get("发送前门禁", {}).get("真实发送必须同时满足", [])
    safety = config.get("安全边界", {})
    report_status = {
        name: {
            "路径": str(path),
            "是否存在": path.exists(),
            "结论": load_json(path).get("结论", "缺失") if path.exists() else "缺失",
        }
        for name, path in EXPECTED_REPORTS.items()
    }
    checks = [
        item("配置主文件存在", CONFIG.exists(), str(CONFIG)),
        item("公共组件接入口径存在", "公共组件接入口径" in config and config.get("公共组件接入口径", {}).get("公共公网回调路径") == "/wecom/work-secretary", config.get("公共组件接入口径", {})),
        item("消息合规规则存在", COMPLIANCE_RULE.exists(), str(COMPLIANCE_RULE)),
        item("输入消息契约存在", INPUT_CONTRACT.exists(), str(INPUT_CONTRACT)),
        item("消息接收服务设计存在", RECEIVE_DESIGN.exists(), str(RECEIVE_DESIGN)),
        item("本地输入队列规则存在", QUEUE_RULE.exists(), str(QUEUE_RULE)),
        item("输入队列证据匹配影子流转规则存在", SHADOW_FLOW_RULE.exists(), str(SHADOW_FLOW_RULE)),
        item("证据匹配到分析契约输入包规则存在", ANALYSIS_INPUT_RULE.exists(), str(ANALYSIS_INPUT_RULE)),
        item("分析契约输入包到待复核草案骨架规则存在", ANALYSIS_DRAFT_RULE.exists(), str(ANALYSIS_DRAFT_RULE)),
        item("待复核草案骨架到分析摘要预演规则存在", ANALYSIS_SUMMARY_RULE.exists(), str(ANALYSIS_SUMMARY_RULE)),
        item("配置章节齐备", all(section in config for section in EXPECTED_CONFIG_SECTIONS), {"期望": EXPECTED_CONFIG_SECTIONS, "实际": list(config.keys())}),
        item("入口默认dry_run_only", config.get("入口状态") == "dry_run_only", config.get("入口状态")),
        item("真实发送默认未放行", config.get("真实发送放行") is False, config.get("真实发送放行")),
        item("机器人终端为杰哥工作秘书", config.get("机器人终端", {}).get("机器人名称") == "杰哥工作秘书" and config.get("机器人终端", {}).get("绑定状态") == "configured_pending_integration", config.get("机器人终端", {})),
        item("输入契约绑定杰哥工作秘书", input_contract.get("机器人终端") == "杰哥工作秘书" and "pending_evidence_match" in input_contract.get("输入状态词", []), input_contract),
        item("接收服务为设计状态且不新增端口", receive_design.get("机器人终端") == "杰哥工作秘书" and receive_design.get("服务状态") == "design_only" and receive_design.get("安全边界", {}).get("是否新增端口") is False, receive_design),
        item("输入队列为dry_run且绑定杰哥工作秘书", queue_rule.get("机器人终端") == "杰哥工作秘书" and queue_rule.get("队列状态") == "dry_run" and queue_rule.get("安全边界", {}).get("是否写正式业务库") is False, queue_rule),
        item("输入队列证据匹配影子流转为shadow且不写正式库", shadow_flow_rule.get("流转状态") == "shadow_dry_run" and shadow_flow_rule.get("机器人终端") == "杰哥工作秘书" and shadow_flow_rule.get("安全边界", {}).get("是否写正式业务库") is False and shadow_flow_rule.get("安全边界", {}).get("是否生成正式税务结论") is False, shadow_flow_rule),
        item("证据匹配到分析契约输入包为shadow且不调用模型", analysis_input_rule.get("运行状态") == "shadow_dry_run" and analysis_input_rule.get("安全边界", {}).get("是否调用模型推理") is False and analysis_input_rule.get("安全边界", {}).get("是否生成正式税务结论") is False, analysis_input_rule),
        item("待复核草案骨架为shadow且不调用模型", analysis_draft_rule.get("运行状态") == "shadow_dry_run" and analysis_draft_rule.get("安全边界", {}).get("是否调用模型推理") is False and analysis_draft_rule.get("安全边界", {}).get("是否生成正式税务结论") is False, analysis_draft_rule),
        item("待复核分析摘要预演为shadow且不调用模型", analysis_summary_rule.get("运行状态") == "shadow_dry_run" and analysis_summary_rule.get("安全边界", {}).get("是否调用模型推理") is False and analysis_summary_rule.get("安全边界", {}).get("是否企业微信真实发送") is False and analysis_summary_rule.get("安全边界", {}).get("是否生成正式税务结论") is False, analysis_summary_rule),
        item("真实发送门禁短语齐备", all(phrase in gate_phrases for phrase in EXPECTED_GATE_PHRASES), {"期望": EXPECTED_GATE_PHRASES, "实际": gate_phrases}),
        item("凭据规则不落盘", "不得写入" in config.get("凭据配置", {}).get("凭据保存规则", ""), config.get("凭据配置", {})),
        item("接收范围禁止外部和全员", any("全员" in text or "@all" in text for text in config.get("接收范围治理", {}).get("禁止", [])) and any("外部" in text or "客户群" in text for text in config.get("接收范围治理", {}).get("禁止", [])), config.get("接收范围治理", {}).get("禁止", [])),
        item("合规规则含边界声明和敏感模式", any("边界声明" in text for text in compliance.get("必须包含", [])) and len(compliance.get("敏感信息模式", [])) >= 4, compliance),
        item("安全边界关闭真实发送和办税系统", safety.get("是否企业微信真实发送") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False and safety.get("是否触发n8n") is False, safety),
        item("关键验收报告全部存在", all(status["是否存在"] for status in report_status.values()), report_status),
        item("关键验收报告全部通过", all(status["结论"] == "通过" for status in report_status.values()), report_status),
    ]
    consistent = all(row["是否一致"] for row in checks)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信入口配置一致性巡检",
        "生成时间": now,
        "巡检结论": "通过" if consistent else "失败",
        "通过数量": sum(1 for row in checks if row["是否一致"]),
        "失败数量": sum(1 for row in checks if not row["是否一致"]),
        "巡检结果": checks,
        "报告状态": report_status,
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否修改配置": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信入口配置一致性巡检",
        "",
        f"- 生成时间：{now}",
        f"- 巡检结论：{report['巡检结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 巡检结果",
        "",
    ]
    for row in checks:
        lines.append(f"- {row['巡检项']}：一致={row['是否一致']}。{row['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "巡检结论": report["巡检结论"], "失败数量": report["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
