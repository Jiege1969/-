# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
QUEUE_DIR = DATA_DIR / "输入队列"
SHADOW_DIR = DATA_DIR / "证据匹配影子流转"
SOURCE_JSON = DATA_DIR / "税收企业微信脱敏提问样例扩展包_最新.json"
QUEUE_JSON = QUEUE_DIR / "税收企业微信脱敏样例批量输入队列_预演.json"
SHADOW_JSON = SHADOW_DIR / "税收企业微信脱敏样例批量证据匹配影子流转_预演.json"
OUT_JSON = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转_最新.json"
OUT_MD = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转_最新.md"


PROHIBITED = [
    "不得登录电子税务局",
    "不得接财税软件",
    "不得触发n8n",
    "不得读取或保存企业微信凭据",
    "不得真实发送企业微信",
    "不得写正式业务库",
    "不得生成正式税务结论",
    "不得把待复核草案标记为结论确认",
]

LEVELS = [
    "法律",
    "行政法规",
    "部门规章/规范性文件",
    "财税文件",
    "政策解读",
    "地方口径",
    "案例",
    "人工经验",
]


def load_source() -> dict:
    if not SOURCE_JSON.exists():
        return {}
    return json.loads(SOURCE_JSON.read_text(encoding="utf-8"))


def classify(sample: dict) -> tuple[str, list[str], list[str], list[str]]:
    text = f"{sample.get('业务事项', '')} {sample.get('原始问题', '')}"
    if "研发" in text or "加计扣除" in text:
        return (
            "研发费用加计扣除",
            ["企业所得税"],
            ["研发费用加计扣除政策链", "企业所得税税前扣除", "研发费用归集与备查资料"],
            ["企业类型", "所属年度", "研发项目类型", "研发费用归集口径", "已取得资料清单", "地方执行口径是否需要复核"],
        )
    if "固定资产" in text or "折旧" in text:
        return (
            "固定资产税前扣除",
            ["企业所得税"],
            ["固定资产税前扣除", "折旧与一次性扣除政策", "企业所得税税前扣除"],
            ["资产类型", "取得时间", "投入使用时间", "会计处理口径", "发票合同资料"],
        )
    if "小规模" in text or "增值税优惠" in text:
        return (
            "小规模纳税人增值税优惠",
            ["增值税"],
            ["增值税小规模纳税人优惠", "销售额口径", "发票开具与优惠适用条件"],
            ["月度销售额", "开票类型", "特殊销售事项", "是否叠加其他优惠"],
        )
    if "资料补充" in text or "补充资料" in text:
        return (
            "资料补充",
            sample.get("适用税种", ["待识别"]),
            ["资料接收台账", "资料脱敏复核", "政策证据关联"],
            ["资料编号", "人工核验人", "资料入库状态", "证据关联主题"],
        )
    if "跨地区" in text or "施工" in text or "预缴" in text:
        return (
            "跨地区施工涉税分析",
            ["增值税", "企业所得税", "附加税费"],
            ["跨地区经营涉税政策", "建筑服务预缴规则", "地方口径待复核"],
            ["项目所在地", "合同金额口径", "计税方法", "预缴记录", "地方口径"],
        )
    return (
        "涉税业务分析",
        sample.get("适用税种", ["待识别"]),
        ["待政策证据底座匹配"],
        ["业务事项", "适用税种", "所属期间", "地区", "纳税人主体", "已提供资料"],
    )


def queue_record(sample: dict, idx: int) -> dict:
    status = sample.get("输入状态")
    rejected = status == "rejected"
    message_type = "mixed" if sample.get("附件提示", {}).get("是否提到附件") else "text"
    return {
        "入队ID": f"tax-wecom-masked-batch-queue-{idx:03d}",
        "消息ID": sample.get("消息ID"),
        "入队时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "机器人名称": sample.get("机器人名称"),
        "提问人标识": sample.get("提问人标识"),
        "消息类型": message_type,
        "脱敏文本": sample.get("原始问题"),
        "附件元数据": sample.get("附件提示", {}),
        "分流结果": "高风险请求" if rejected else ("资料补充" if status == "normalized" else "涉税问题"),
        "处理状态": "rejected" if rejected else "queued",
        "拒收原因": "红线请求：不得通过企业微信触发办税执行、真实发送或正式税务结论。" if rejected else "",
        "输入契约状态": status,
        "审计编号": f"tax-wecom-masked-batch-audit-{idx:03d}",
        "来源通道": sample.get("来源通道"),
    }


def shadow_task(record: dict, sample: dict, idx: int) -> dict:
    matter, taxes, themes, missing = classify(sample)
    state = "pending_fact_completion" if record["输入契约状态"] == "normalized" else "pending_policy_evidence_match"
    return {
        "流转ID": f"tax-wecom-masked-batch-shadow-{idx:03d}",
        "入队ID": record["入队ID"],
        "消息ID": record["消息ID"],
        "来源机器人": record["机器人名称"],
        "脱敏文本": record["脱敏文本"],
        "原队列状态": record["处理状态"],
        "原输入契约状态": record["输入契约状态"],
        "影子流转状态": state,
        "业务事项猜测": matter,
        "适用税种猜测": taxes,
        "候选证据主题": themes,
        "依据层级要求": LEVELS,
        "待补充事实": missing,
        "待人工复核项": [
            "核验政策依据层级和有效状态",
            "核验业务事实是否足以进入分析契约",
            "核验missing字段是否已明确",
            "核验地方口径是否仅作为辅助或待复核线索",
        ],
        "禁止动作": PROHIBITED,
        "下一步建议": "进入政策证据底座候选匹配，形成待复核分析草案输入；不得形成正式税务结论。",
        "是否写正式业务库": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = load_source()
    samples = source.get("输入样例", [])
    queue_records = [queue_record(sample, idx) for idx, sample in enumerate(samples, start=1)]
    shadow_tasks = [
        shadow_task(record, sample, idx)
        for idx, (record, sample) in enumerate(zip(queue_records, samples), start=1)
        if record["处理状态"] == "queued" and record["输入契约状态"] in {"pending_evidence_match", "normalized"}
    ]
    rejected = [
        {
            "消息ID": record["消息ID"],
            "入队ID": record["入队ID"],
            "原队列状态": record["处理状态"],
            "原输入契约状态": record["输入契约状态"],
            "拒绝流转原因": record["拒收原因"] or "输入状态不允许进入证据匹配影子流转。",
            "是否写正式业务库": False,
            "是否生成正式税务结论": False,
        }
        for record in queue_records
        if record["处理状态"] != "queued" or record["输入契约状态"] not in {"pending_evidence_match", "normalized"}
    ]

    boundaries = {
        "是否接收真实企业微信回调": False,
        "是否联网": False,
        "是否读取凭据": False,
        "是否企业微信真实发送": False,
        "是否修改公共企业微信接入配置": False,
        "是否修改19310": False,
        "是否触发n8n": False,
        "是否写正式业务库": False,
        "是否接电子税务局": False,
        "是否接财税软件": False,
        "是否生成正式税务结论": False,
    }

    queue_package = {
        "名称": "税收企业微信脱敏样例批量输入队列预演",
        "生成时间": now,
        "来源样例包": str(SOURCE_JSON),
        "队列状态": "dry_run",
        "记录数量": len(queue_records),
        "入队数量": sum(1 for item in queue_records if item["处理状态"] == "queued"),
        "拒收数量": sum(1 for item in queue_records if item["处理状态"] == "rejected"),
        "队列记录": queue_records,
        "安全边界": boundaries,
    }
    shadow_package = {
        "名称": "税收企业微信脱敏样例批量证据匹配影子流转",
        "生成时间": now,
        "来源队列": str(QUEUE_JSON),
        "流转状态": "shadow_dry_run",
        "队列记录数量": len(queue_records),
        "影子任务数量": len(shadow_tasks),
        "拒绝流转数量": len(rejected),
        "影子任务": shadow_tasks,
        "拒绝流转留痕": rejected,
        "安全边界": boundaries,
    }
    result = {
        "名称": "税收企业微信脱敏样例批量入队影子流转",
        "生成时间": now,
        "资产身份": "dry-run批量流转预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        "来源样例包": str(SOURCE_JSON),
        "队列文件": str(QUEUE_JSON),
        "影子流转文件": str(SHADOW_JSON),
        "样例数量": len(samples),
        "队列记录数量": len(queue_records),
        "影子任务数量": len(shadow_tasks),
        "拒绝流转数量": len(rejected),
        "队列记录": queue_records,
        "影子任务": shadow_tasks,
        "拒绝流转留痕": rejected,
        "安全边界": boundaries,
    }

    QUEUE_JSON.write_text(json.dumps(queue_package, ensure_ascii=False, indent=2), encoding="utf-8")
    SHADOW_JSON.write_text(json.dumps(shadow_package, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信脱敏样例批量入队影子流转",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run批量流转预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        f"- 样例数量：{len(samples)}",
        f"- 队列记录数量：{len(queue_records)}",
        f"- 影子任务数量：{len(shadow_tasks)}",
        f"- 拒绝流转数量：{len(rejected)}",
        "",
        "## 影子任务",
    ]
    for item in shadow_tasks:
        lines.extend(
            [
                f"### {item['流转ID']} {item['业务事项猜测']}",
                f"- 消息ID：{item['消息ID']}",
                f"- 影子流转状态：{item['影子流转状态']}",
                f"- 适用税种猜测：{'、'.join(item['适用税种猜测'])}",
                f"- 候选证据主题：{'、'.join(item['候选证据主题'])}",
                f"- 下一步建议：{item['下一步建议']}",
                "",
            ]
        )
    lines.extend(["## 拒绝流转留痕"])
    for item in rejected:
        lines.append(f"- {item['消息ID']}：{item['拒绝流转原因']}")
    lines.extend(["", "## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": "完成", "样例数量": len(samples), "影子任务数量": len(shadow_tasks), "拒绝流转数量": len(rejected), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
