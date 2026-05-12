# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "待复核草案出入口反事实校验"
SOURCE_INDEX = BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.json"
SOURCE_SAMPLE = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信待复核分析草案出入口索引反事实校验_最新.json"
OUT_MD = BASE_DIR / "税收企业微信待复核分析草案出入口索引反事实校验_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信待复核分析草案出入口索引反事实校验.json"


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


SCENARIOS = [
    {
        "场景ID": "tax-draft-io-counterfactual-001",
        "场景": "只读资产被请求真实回写草案源文件",
        "资产只读": True,
        "请求真实回写": True,
        "请求真实发送": False,
        "请求正式结论": False,
        "请求读取凭据": False,
        "状态": "pending_review",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-002",
        "场景": "evidence_ready被误解释为正式税务意见",
        "资产只读": True,
        "请求真实回写": False,
        "请求真实发送": False,
        "请求正式结论": True,
        "请求读取凭据": False,
        "状态": "evidence_ready",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-003",
        "场景": "human_reviewed被误解释为结论确认",
        "资产只读": True,
        "请求真实回写": False,
        "请求真实发送": False,
        "请求正式结论": True,
        "请求读取凭据": False,
        "状态": "human_reviewed",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-004",
        "场景": "待复核摘要被请求真实发送企业微信",
        "资产只读": True,
        "请求真实回写": False,
        "请求真实发送": True,
        "请求正式结论": False,
        "请求读取凭据": False,
        "状态": "draft",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-005",
        "场景": "凭据未放行但请求读取企业微信凭据",
        "资产只读": True,
        "请求真实回写": False,
        "请求真实发送": False,
        "请求正式结论": False,
        "请求读取凭据": True,
        "状态": "pending_review",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-006",
        "场景": "blocked状态被请求删除历史审计记录",
        "资产只读": True,
        "请求真实回写": True,
        "请求真实发送": False,
        "请求正式结论": False,
        "请求读取凭据": False,
        "请求删除历史审计": True,
        "状态": "blocked",
    },
    {
        "场景ID": "tax-draft-io-counterfactual-007",
        "场景": "只读资产仅进入本地预演索引",
        "资产只读": True,
        "请求真实回写": False,
        "请求真实发送": False,
        "请求正式结论": False,
        "请求读取凭据": False,
        "状态": "pending_review",
    },
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def decide(scenario: dict) -> dict:
    blockers = []
    if scenario.get("资产只读") and scenario.get("请求真实回写"):
        blockers.append("只读资产不得真实回写")
    if scenario.get("请求真实发送"):
        blockers.append("企业微信真实发送未放行")
    if scenario.get("请求正式结论"):
        blockers.append("待复核链路不得生成正式税务结论")
    if scenario.get("请求读取凭据"):
        blockers.append("不得读取或保存企业微信凭据")
    if scenario.get("请求删除历史审计"):
        blockers.append("不得删除历史审计记录")
    if scenario.get("状态") in {"evidence_ready", "human_reviewed"} and scenario.get("请求正式结论"):
        blockers.append("状态名不得被解释为结论确认")

    allowed_preview = not blockers and scenario.get("资产只读") is True
    return {
        **scenario,
        "阻断原因": blockers,
        "是否允许本地预演": allowed_preview,
        "是否误放行真实回写": False if blockers or not scenario.get("请求真实回写") else True,
        "是否误放行真实发送": False if blockers or not scenario.get("请求真实发送") else True,
        "是否误生成正式税务结论": False if blockers or not scenario.get("请求正式结论") else True,
        "动作": "counterfactual_io_guard_preview_only",
        "是否真实回写状态": False,
        "是否企业微信真实发送": False,
        "是否读取凭据": False,
        "是否写正式业务库": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    index_data = load_json(SOURCE_INDEX)
    sample_data = load_json(SOURCE_SAMPLE)
    results = [decide(item) for item in SCENARIOS]
    mis_allowed = [
        item for item in results
        if item["是否误放行真实回写"] or item["是否误放行真实发送"] or item["是否误生成正式税务结论"]
    ]

    result = {
        "名称": "税收企业微信待复核分析草案出入口索引反事实校验",
        "生成时间": now,
        "资产身份": "dry-run出入口索引反事实校验，不是真实状态回写，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "出入口状态索引来源": str(SOURCE_INDEX),
        "再校验样例来源": str(SOURCE_SAMPLE),
        "索引资产数量": index_data.get("资产索引数量", 0),
        "样例数量": sample_data.get("样例数量", 0),
        "演练场景数量": len(results),
        "误放行数量": len(mis_allowed),
        "演练结果": results,
        "结论": "通过" if not mis_allowed else "失败",
        "下一步低风险队列": [
            "生成税收企业微信人工复核样例敏感信息复扫报告。",
            "生成税收企业微信人工复核链路阶段收口索引。",
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信待复核分析草案出入口索引反事实校验",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run反事实校验，不是真实状态回写，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 演练场景数量：{len(results)}",
        f"- 误放行数量：{len(mis_allowed)}",
        f"- 结论：{result['结论']}",
        "",
        "## 演练结果",
        "",
    ]
    for item in results:
        lines.append(f"- {item['场景ID']}：{item['场景']}，允许本地预演={item['是否允许本地预演']}，阻断={len(item['阻断原因'])}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": result["结论"], "报告": str(OUT_MD), "误放行数量": len(mis_allowed)}, ensure_ascii=False))
    return 0 if not mis_allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
