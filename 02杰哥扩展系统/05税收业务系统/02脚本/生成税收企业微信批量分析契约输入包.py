# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SOURCE_JSON = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转_最新.json"
OUT_JSON = DATA_DIR / "税收企业微信批量分析契约输入包_最新.json"
OUT_MD = DATA_DIR / "税收企业微信批量分析契约输入包_最新.md"
PACKAGE_JSON = DATA_DIR / "分析契约输入包" / "税收企业微信批量分析契约输入包_预演.json"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"


DEFAULT_RISKS = [
    "政策依据有效状态未完成逐条核验",
    "地方口径不得越过上位政策作为正式依据",
    "业务事实不足时不得形成适用结论",
    "企业微信输出不得被误解为正式税务意见",
]

PROHIBITED = [
    "不得登录电子税务局",
    "不得接财税软件",
    "不得触发n8n",
    "不得读取或保存企业微信凭据",
    "不得真实发送企业微信",
    "不得写正式业务库",
    "不得生成正式税务结论",
    "不得把输入包状态命名为结论确认类状态",
]


def load_source() -> dict:
    if not SOURCE_JSON.exists():
        return {}
    return json.loads(SOURCE_JSON.read_text(encoding="utf-8"))


def make_package(task: dict, idx: int) -> dict:
    status = "pending_fact_completion" if task.get("影子流转状态") == "pending_fact_completion" else "pending_review_input"
    confidence = "low" if status == "pending_fact_completion" else "medium"
    return {
        "输入包ID": f"tax-wecom-contract-input-batch-{idx:03d}",
        "来源流转ID": task.get("流转ID"),
        "消息ID": task.get("消息ID"),
        "来源机器人": task.get("来源机器人"),
        "输入包状态": status,
        "业务事项": task.get("业务事项猜测"),
        "适用税种": task.get("适用税种猜测", []),
        "政策依据候选主题": task.get("候选证据主题", []),
        "依据层级": task.get("依据层级要求", []),
        "业务事实摘要": {
            "脱敏文本": task.get("脱敏文本"),
            "原队列状态": task.get("原队列状态"),
            "原输入契约状态": task.get("原输入契约状态"),
            "事实充分性": "待补充" if status == "pending_fact_completion" else "待证据匹配",
        },
        "资料缺口": task.get("待补充事实", []),
        "风险点": DEFAULT_RISKS,
        "置信度": confidence,
        "人工复核项": task.get("待人工复核项", []) + [
            "确认政策证据是否来自可信来源",
            "确认有效状态是否为全文有效或人工确认有效",
            "确认本输入包只能进入待复核草案",
        ],
        "禁止动作": PROHIBITED,
        "下一步建议": "进入待复核草案骨架批量预演；不得生成正式税务结论。",
        "是否写正式业务库": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_JSON.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = load_source()
    tasks = source.get("影子任务", [])
    rejected = source.get("拒绝流转留痕", [])
    packages = [make_package(task, idx) for idx, task in enumerate(tasks, start=1)]
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
    package_file = {
        "名称": "税收企业微信批量分析契约输入包预演",
        "生成时间": now,
        "规则来源": str(RULE_PATH),
        "来源影子流转": str(SOURCE_JSON),
        "运行状态": "shadow_dry_run",
        "输入包数量": len(packages),
        "拒绝承接数量": len(rejected),
        "输入包": packages,
        "拒绝承接留痕": rejected,
        "安全边界": boundaries,
    }
    result = {
        "名称": "税收企业微信批量分析契约输入包",
        "生成时间": now,
        "资产身份": "dry-run批量分析契约输入包，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        "规则来源": str(RULE_PATH),
        "来源影子流转": str(SOURCE_JSON),
        "输入包文件": str(PACKAGE_JSON),
        "影子任务数量": len(tasks),
        "输入包数量": len(packages),
        "拒绝承接数量": len(rejected),
        "输入包状态统计": {
            "pending_review_input": sum(1 for item in packages if item["输入包状态"] == "pending_review_input"),
            "pending_fact_completion": sum(1 for item in packages if item["输入包状态"] == "pending_fact_completion"),
        },
        "输入包": packages,
        "拒绝承接留痕": rejected,
        "安全边界": boundaries,
    }
    PACKAGE_JSON.write_text(json.dumps(package_file, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信批量分析契约输入包",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run批量分析契约输入包，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        f"- 输入包数量：{len(packages)}",
        f"- 拒绝承接数量：{len(rejected)}",
        "",
        "## 输入包清单",
    ]
    for item in packages:
        lines.extend(
            [
                f"### {item['输入包ID']} {item['业务事项']}",
                f"- 消息ID：{item['消息ID']}",
                f"- 输入包状态：{item['输入包状态']}",
                f"- 适用税种：{'、'.join(item['适用税种'])}",
                f"- 政策依据候选主题：{'、'.join(item['政策依据候选主题'])}",
                f"- 资料缺口：{'、'.join(item['资料缺口'])}",
                f"- 置信度：{item['置信度']}",
                f"- 下一步建议：{item['下一步建议']}",
                "",
            ]
        )
    lines.extend(["## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": "完成", "输入包数量": len(packages), "拒绝承接数量": len(rejected), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
