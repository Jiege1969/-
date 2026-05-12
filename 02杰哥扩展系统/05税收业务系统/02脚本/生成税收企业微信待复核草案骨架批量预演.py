# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SOURCE_JSON = DATA_DIR / "税收企业微信批量分析契约输入包_最新.json"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
OUT_JSON = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.md"
SKELETON_JSON = DATA_DIR / "待复核分析草案骨架" / "税收企业微信待复核草案骨架批量预演.json"


APPLICABILITY_SKELETON = [
    "适用主体待人工补充",
    "适用事项待证据匹配",
    "适用期间待核验",
    "关键条件待政策证据底座抽取",
    "排除条件待政策证据底座抽取",
    "所需资料待人工复核",
]

OUTPUT_BOUNDARY = [
    "这是待复核分析草案骨架，不是正式税务意见。",
    "政策依据仅为候选主题，未完成人工有效性核验前不得进入当前适用结论。",
    "不得输出可以享受、不能享受、应纳税额、退税金额、开票或申报指令。",
    "正式结论必须由人工复核后作出。",
]

PROHIBITED = [
    "不得登录电子税务局",
    "不得接财税软件",
    "不得触发n8n",
    "不得读取或保存企业微信凭据",
    "不得真实发送企业微信",
    "不得写正式业务库",
    "不得调用模型推理",
    "不得生成正式税务结论",
]


def load_source() -> dict:
    if not SOURCE_JSON.exists():
        return {}
    return json.loads(SOURCE_JSON.read_text(encoding="utf-8"))


def make_skeleton(package: dict, idx: int) -> dict:
    contract_status = "draft" if package.get("输入包状态") == "pending_fact_completion" else "pending_review"
    return {
        "草案ID": f"tax-wecom-review-draft-skeleton-batch-{idx:03d}",
        "来源输入包ID": package.get("输入包ID"),
        "消息ID": package.get("消息ID"),
        "契约状态": contract_status,
        "业务事项": package.get("业务事项"),
        "业务事实": {
            "摘要": package.get("业务事实摘要", {}).get("脱敏文本", ""),
            "来源机器人": package.get("来源机器人"),
            "事实充分性": package.get("业务事实摘要", {}).get("事实充分性", "待核验"),
            "待补充事实": package.get("资料缺口", []),
        },
        "政策依据": {
            "依据状态": "candidate_only_pending_evidence_review",
            "候选主题": package.get("政策依据候选主题", []),
            "说明": "只登记候选主题和待核验依据层级，不写适用结论。",
        },
        "依据层级": package.get("依据层级", []),
        "依据层级明细": package.get("依据层级明细", []),
        "适用条件": APPLICABILITY_SKELETON,
        "待复核资料清单": package.get("待复核资料清单", []),
        "待复核说明": package.get("待复核说明", ""),
        "资料缺口": package.get("资料缺口", []),
        "风险点": package.get("风险点", []),
        "置信度": package.get("置信度", "low"),
        "人工复核项": package.get("人工复核项", []) + [
            "人工确认候选政策依据是否存在全文有效或已人工确认有效资料",
            "人工确认业务事实和资料缺口是否足以进入下一步待复核分析草案",
            "人工确认不得将本骨架作为正式税务意见或对外结论",
        ],
        "输出边界": OUTPUT_BOUNDARY,
        "禁止动作": PROHIBITED,
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SKELETON_JSON.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = load_source()
    packages = source.get("输入包", [])
    rejected = source.get("拒绝承接留痕", [])
    skeletons = [make_skeleton(package, idx) for idx, package in enumerate(packages, start=1)]
    boundaries = {
        "是否接收真实企业微信回调": False,
        "是否联网": False,
        "是否读取凭据": False,
        "是否企业微信真实发送": False,
        "是否修改公共企业微信接入配置": False,
        "是否修改19310": False,
        "是否触发n8n": False,
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否接电子税务局": False,
        "是否接财税软件": False,
        "是否生成正式税务结论": False,
    }
    skeleton_file = {
        "名称": "税收企业微信待复核草案骨架批量预演文件",
        "生成时间": now,
        "规则来源": str(RULE_PATH),
        "来源输入包": str(SOURCE_JSON),
        "运行状态": "shadow_dry_run",
        "草案骨架数量": len(skeletons),
        "阻断数量": len(rejected),
        "草案骨架": skeletons,
        "阻断留痕": rejected,
        "安全边界": boundaries,
    }
    result = {
        "名称": "税收企业微信待复核草案骨架批量预演",
        "生成时间": now,
        "资产身份": "dry-run待复核草案骨架批量预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        "规则来源": str(RULE_PATH),
        "来源输入包": str(SOURCE_JSON),
        "草案骨架文件": str(SKELETON_JSON),
        "输入包数量": len(packages),
        "草案骨架数量": len(skeletons),
        "阻断数量": len(rejected),
        "草案状态统计": {
            "pending_review": sum(1 for item in skeletons if item["契约状态"] == "pending_review"),
            "draft": sum(1 for item in skeletons if item["契约状态"] == "draft"),
        },
        "草案骨架": skeletons,
        "阻断留痕": rejected,
        "安全边界": boundaries,
    }
    SKELETON_JSON.write_text(json.dumps(skeleton_file, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信待复核草案骨架批量预演",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run待复核草案骨架批量预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        f"- 输入包数量：{len(packages)}",
        f"- 草案骨架数量：{len(skeletons)}",
        f"- 阻断数量：{len(rejected)}",
        "",
        "## 草案骨架清单",
    ]
    for item in skeletons:
        lines.extend(
            [
                f"### {item['草案ID']} {item['业务事项']}",
                f"- 消息ID：{item['消息ID']}",
                f"- 契约状态：{item['契约状态']}",
                f"- 政策依据候选主题：{'、'.join(item['政策依据']['候选主题'])}",
                f"- 资料缺口：{'、'.join(item['资料缺口'])}",
                f"- 置信度：{item['置信度']}",
                "- 输出边界：待复核草案骨架，不是正式税务意见。",
                "",
            ]
        )
    lines.extend(["## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": "完成", "草案骨架数量": len(skeletons), "阻断数量": len(rejected), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
