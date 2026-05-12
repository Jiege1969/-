# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "待复核草案出入口状态索引"
OUT_JSON = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.json"
OUT_MD = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信待复核分析草案出入口状态索引.json"


ASSETS = [
    ("批量分析契约输入包", "税收企业微信批量分析契约输入包_最新.json", "read_only_input", "pending_review"),
    ("待复核草案骨架批量预演", "税收企业微信待复核草案骨架批量预演_最新.json", "read_only_input", "draft"),
    ("待复核分析摘要批量预演", "税收企业微信待复核分析摘要批量预演_最新.json", "read_only_input", "draft"),
    ("人工复核阅读包批量预演", "税收企业微信人工复核阅读包批量预演_最新.json", "read_only_input", "pending_human_review"),
    ("人工复核回执空白模板批量预演", "税收企业微信人工复核回执空白模板批量预演_最新.json", "read_only_input", "blank_pending_human_fill"),
    ("复核回执到草案状态回写预演", "税收企业微信复核回执到草案状态回写预演_最新.json", "read_only_evidence", "shadow_dry_run_no_op_status_rewrite"),
    ("人工复核填写规范与状态机规则", "税收企业微信人工复核填写规范与状态机规则_最新.json", "read_only_rule", "rule_only"),
    ("人工复核回执填报校验器预演", "税收企业微信人工复核回执填报校验器预演_最新.json", "read_only_validation", "validation_only_no_status_write"),
    ("人工复核状态机反事实演练", "税收企业微信人工复核状态机反事实演练_最新.json", "read_only_validation", "counterfactual_preview_only"),
    ("人工复核校验失败整改清单", "税收企业微信人工复核校验失败整改清单_最新.json", "read_only_remediation", "remediation_list_only_no_status_write"),
]


SAFETY = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否写草案源文件": False,
    "是否真实回写状态": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否形成正式复核结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset_index = []
    for name, filename, role, default_state in ASSETS:
        path = BASE_DIR / filename
        data = load_json(path)
        count = 0
        for key in ("草案骨架", "摘要预演", "阅读包", "回执模板", "回写预演", "校验记录", "演练结果", "整改清单"):
            if isinstance(data.get(key), list):
                count = len(data[key])
                break
        asset_index.append({
            "资产名称": name,
            "路径": str(path),
            "是否存在": path.exists(),
            "访问角色": role,
            "默认状态": data.get("运行状态", default_state),
            "记录数量": count,
            "是否只读": True,
            "是否允许真实回写": False,
            "是否允许作为正式税务结论": False,
            "是否允许真实发送企业微信": False,
        })

    state_transitions = [
        {
            "入口状态": "draft",
            "允许来源": ["待复核草案骨架批量预演", "待复核分析摘要批量预演"],
            "允许去向": ["pending_review"],
            "限制": "只代表待复核草案存在，不代表适用结论。",
        },
        {
            "入口状态": "pending_review",
            "允许来源": ["分析契约输入包", "人工复核回执填报校验器预演"],
            "允许去向": ["evidence_ready", "blocked"],
            "限制": "只能本地预演，不得真实回写草案源文件。",
        },
        {
            "入口状态": "evidence_ready",
            "允许来源": ["人工复核状态机反事实演练", "人工复核填写规范与状态机规则"],
            "允许去向": ["pending_review"],
            "限制": "只表示证据可供后续待复核草案引用，不代表业务一定适用。",
        },
        {
            "入口状态": "human_reviewed",
            "允许来源": ["人工复核流程记录"],
            "允许去向": ["pending_review"],
            "限制": "只表示流程记录完成，不代表税务结论确认；当前未放行真实回写。",
        },
        {
            "入口状态": "blocked",
            "允许来源": ["禁止短语", "敏感信息", "证据不足", "事实不足", "风险未复核"],
            "允许去向": ["pending_review"],
            "限制": "只登记阻断原因，不删除、不覆盖、不外发。",
        },
    ]

    result = {
        "名称": "税收企业微信待复核分析草案出入口状态索引",
        "生成时间": now,
        "资产身份": "dry-run待复核分析草案出入口状态索引，不是真实状态回写，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "资产索引数量": len(asset_index),
        "资产索引": asset_index,
        "允许状态": ["draft", "evidence_ready", "pending_review", "human_reviewed", "blocked"],
        "禁止状态": ["confirmed_conclusion", "formal_tax_conclusion"],
        "状态流规则": state_transitions,
        "禁止动作": [
            "不得真实回写草案源文件。",
            "不得写正式业务库。",
            "不得真实发送企业微信。",
            "不得读取或保存企业微信凭据。",
            "不得把待复核草案、evidence_ready或human_reviewed解释为正式税务意见。",
            "不得自动申报、退税、开票或接入电子税务局。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信人工复核整改后再校验样例模板。",
            "生成税收企业微信待复核分析草案出入口索引反事实校验。",
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信待复核分析草案出入口状态索引",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run状态索引，不是真实状态回写，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 资产索引数量：{len(asset_index)}",
        "",
        "## 资产索引",
        "",
    ]
    for item in asset_index:
        lines.append(f"- {item['资产名称']}：存在={item['是否存在']}，角色={item['访问角色']}，只读={item['是否只读']}，允许真实回写={item['是否允许真实回写']}。")
    lines.extend(["", "## 状态流规则", ""])
    for item in state_transitions:
        lines.append(f"- {item['入口状态']}：允许去向={item['允许去向']}；限制={item['限制']}")
    lines.extend(["", "## 禁止动作", ""])
    for item in result["禁止动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "报告": str(OUT_MD), "资产索引数量": len(asset_index)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
