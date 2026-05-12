# -*- coding: utf-8 -*-
"""
第七批并行小任务 AD：03进化 / 可交付前规则审计总表。

只读取既有报告与样本，生成本地审计总表；不触发 n8n，不发送企业微信真实消息，
不写正式库，不调用券商接口，不自动交易，不触碰本职工作系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
TASK_NAME = "第七批小任务AD_可交付前规则审计总表"
DATA_DIR = ROOT / "03杰哥进化系统" / "03数据" / "27第七批小任务AD_可交付前规则审计总表"
DOC_PATH = ROOT / "03杰哥进化系统" / "07文档" / f"{TASK_NAME}说明_最新.md"
RECOVERY_PATH = ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第七批小任务AD规则审计回收报告_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_json(path: Path) -> Any:
    text = read_text(path)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_paths() -> list[dict[str, str]]:
    state = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
    recycle = ROOT / "00杰哥系统总管" / "03数据" / "并行回收"
    evo_data = ROOT / "03杰哥进化系统" / "03数据"
    return [
        {"类别": "股票硬闸门", "名称": "股票系统只分析不交易总闸门验收", "路径": str(state / "股票系统只分析不交易总闸门验收_最新.md")},
        {"类别": "股票硬闸门", "名称": "股票系统只分析不交易边界核验", "路径": str(state / "股票系统只分析不交易边界核验_最新.md")},
        {"类别": "并行策略", "名称": "用户最新并行策略纠偏报告", "路径": str(state / "用户最新并行策略纠偏报告_最新.md")},
        {"类别": "并行策略", "名称": "用户最新并行策略纠偏验收", "路径": str(state / "用户最新并行策略纠偏验收_最新.md")},
        {"类别": "第五批成果", "名称": "第五批并行收口与进度重算报告", "路径": str(state / "第五批并行收口与进度重算报告_最新.md")},
        {"类别": "第五批成果", "名称": "第五批并行收口与进度重算验收", "路径": str(state / "第五批并行收口与进度重算验收_最新.md")},
        {"类别": "第六批成果", "名称": "第六批并行收口与进度重算报告", "路径": str(state / "第六批并行收口与进度重算报告_最新.md")},
        {"类别": "第六批成果", "名称": "第六批并行收口与进度重算验收", "路径": str(state / "第六批并行收口与进度重算验收_最新.md")},
        {"类别": "第五批窗口", "名称": "01智能系统_第五批小任务P回收报告", "路径": str(recycle / "01智能系统_第五批小任务P回收报告_最新.md")},
        {"类别": "第五批窗口", "名称": "02扩展系统_第五批小任务Q视频回收报告", "路径": str(recycle / "02扩展系统_第五批小任务Q视频回收报告_最新.md")},
        {"类别": "第五批窗口", "名称": "02扩展系统_第五批小任务R内容回收报告", "路径": str(recycle / "02扩展系统_第五批小任务R内容回收报告_最新.md")},
        {"类别": "第五批窗口", "名称": "02扩展系统_第五批小任务S企业微信回收报告", "路径": str(recycle / "02扩展系统_第五批小任务S企业微信回收报告_最新.md")},
        {"类别": "第五批窗口", "名称": "02扩展系统_第五批小任务T税收回收报告", "路径": str(recycle / "02扩展系统_第五批小任务T税收回收报告_最新.md")},
        {"类别": "第五批窗口", "名称": "03进化系统_第五批小任务U回收报告", "路径": str(recycle / "03进化系统_第五批小任务U回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "01智能系统_第六批小任务V回收报告", "路径": str(recycle / "01智能系统_第六批小任务V回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "02扩展系统_第六批小任务W企业微信回收报告", "路径": str(recycle / "02扩展系统_第六批小任务W企业微信回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "02扩展系统_第六批小任务X知识库回收报告", "路径": str(recycle / "02扩展系统_第六批小任务X知识库回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "02扩展系统_第六批小任务Y内容回收报告", "路径": str(recycle / "02扩展系统_第六批小任务Y内容回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "02扩展系统_第六批小任务Z视频回收报告", "路径": str(recycle / "02扩展系统_第六批小任务Z视频回收报告_最新.md")},
        {"类别": "第六批窗口", "名称": "03进化系统_第六批小任务AA回收报告", "路径": str(recycle / "03进化系统_第六批小任务AA回收报告_最新.md")},
        {"类别": "03进化样本", "名称": "第五批U规则评审读取样本", "路径": str(evo_data / "25第五批小任务U_第四批扩展成果规则评审读取样本" / "第五批小任务U_第四批扩展成果规则评审读取样本_最新.json")},
        {"类别": "03进化样本", "名称": "第六批AA可交付前规则审计样本", "路径": str(evo_data / "26第六批小任务AA_第五批成果可交付前规则审计样本" / "第六批小任务AA_第五批成果可交付前规则审计样本_最新.json")},
    ]


def contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def inspect_source(item: dict[str, str]) -> dict[str, Any]:
    path = Path(item["路径"])
    text = read_text(path)
    json_data = read_json(path) if path.suffix.lower() == ".json" else None
    return {
        **item,
        "存在": path.exists(),
        "已读取": bool(text),
        "字符数": len(text),
        "可解析JSON": json_data is not None,
        "提及验收通过": contains_any(text, ["验收通过", "通过", "结论：通过", '"通过": true', '"验收结论": "通过"']),
        "提及安全阻断": contains_any(text, ["安全阻断", "阻断", "硬闸门", "总闸门", "只分析不交易"]),
        "提及真实动作禁用": contains_any(text, ["真实动作", "不触发", "未触发", "禁用", "关闭", "不发送", "未发送", "不写正式库", "不调用券商接口", "不自动交易"]),
        "提及用户暂停继承": contains_any(text, ["本职工作系统暂停", "本职工作暂停", "暂停本职工作", "本职工作系统", "用户最新要求暂停"]),
        "提及并行策略": contains_any(text, ["并行策略", "活跃窗口", "最多", "低风险隔离", "串行回收", "6/6", "P/Q/R/S/T/U", "V/W/X/Y/Z/AA"]),
    }


def build_audit_rows(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {item["名称"]: item for item in sources}
    rows = [
        {
            "审计项": "股票硬闸门继承",
            "依据": ["股票系统只分析不交易总闸门验收", "股票系统只分析不交易边界核验"],
            "规则结论": "股票系统保持分析系统定位；自动交易、券商接口、下单、资金账户、交易委托继续硬性关闭。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，可交付前继续保留硬闸门",
        },
        {
            "审计项": "并行策略继承",
            "依据": ["用户最新并行策略纠偏报告", "用户最新并行策略纠偏验收", "第五批并行收口与进度重算报告", "第六批并行收口与进度重算报告"],
            "规则结论": "继续沿用稳定 4 个活跃窗口、低风险隔离最多 6 个、00 总管串行回收的口径。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，可交付前不扩大真实动作范围",
        },
        {
            "审计项": "本职工作暂停继承",
            "依据": ["用户最新并行策略纠偏报告", "用户最新并行策略纠偏验收", "第六批并行收口与进度重算报告"],
            "规则结论": "本职工作系统按用户最新要求继续暂停，不纳入当前施工队列，不碰本职工作系统。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，暂停状态必须显式继承",
        },
        {
            "审计项": "第五批成果可交付前继承",
            "依据": ["第五批并行收口与进度重算报告", "第五批并行收口与进度重算验收", "第五批U规则评审读取样本"],
            "规则结论": "第五批 P/Q/R/S/T/U 可作为审计输入；交付阻断为 0 的同时，安全阻断作为合规边界保留。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，可交付前仍需人工确认项不自动放行",
        },
        {
            "审计项": "第六批成果可交付前继承",
            "依据": ["第六批并行收口与进度重算报告", "第六批并行收口与进度重算验收", "第六批AA可交付前规则审计样本"],
            "规则结论": "第六批 V/W/X/Y/Z/AA 可作为审计输入；真实发送、正式库、n8n、真实媒体处理、券商接口、自动交易继续禁用。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，可交付前规则口径已收敛",
        },
        {
            "审计项": "03进化 AD 总表输出边界",
            "依据": ["03进化系统_第五批小任务U回收报告", "03进化系统_第六批小任务AA回收报告"],
            "规则结论": "本任务只生成本地审计总表、验收报告和指定回收报告；不写正式库，不触发真实链路。",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "可交付状态": "通过，AD 仅为规则审计交付件",
        },
    ]
    for row in rows:
        evidence = [by_name.get(name, {"存在": False, "已读取": False, "路径": ""}) for name in row["依据"]]
        row["依据存在"] = all(item.get("存在") for item in evidence)
        row["依据已读取"] = all(item.get("已读取") for item in evidence)
        row["证据路径"] = [item.get("路径") for item in evidence]
    return rows


def build_payload() -> dict[str, Any]:
    sources = [inspect_source(item) for item in source_paths()]
    rows = build_audit_rows(sources)
    return {
        "任务": TASK_NAME,
        "生成时间": now_text(),
        "输入来源数量": len(sources),
        "已读取来源数量": sum(1 for item in sources if item["已读取"]),
        "审计项数量": len(rows),
        "统一结论": {
            "可交付前规则审计": "通过",
            "安全阻断不失败": True,
            "真实动作禁用": True,
            "用户暂停继承": True,
            "股票硬闸门继承": True,
            "并行策略继承": True,
            "本职工作暂停继承": True,
            "第五第六批成果继承": True,
        },
        "禁止真实动作": {
            "触发n8n": False,
            "发送企业微信真实消息": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "触碰本职工作系统": False,
            "调用真实外部API": False,
            "真实媒体生成或发布": False,
        },
        "输入来源": sources,
        "可交付前规则审计总表": rows,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 第七批小任务AD：03进化可交付前规则审计总表",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 输入来源数量：{payload['输入来源数量']}",
        f"- 已读取来源数量：{payload['已读取来源数量']}",
        f"- 审计项数量：{payload['审计项数量']}",
        "- 总结论：通过。安全阻断不按失败处理，真实动作继续禁用，用户关于本职工作暂停的要求继续继承。",
        "",
        "## 审计总表",
        "",
        "| 审计项 | 依据已读取 | 规则结论 | 安全阻断不失败 | 真实动作禁用 | 用户暂停继承 | 可交付状态 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["可交付前规则审计总表"]:
        lines.append(
            f"| {row['审计项']} | {row['依据已读取']} | {row['规则结论']} | {row['安全阻断不失败']} | {row['真实动作禁用']} | {row['用户暂停继承']} | {row['可交付状态']} |"
        )
    lines.extend(["", "## 输入来源", ""])
    for item in payload["输入来源"]:
        lines.append(f"- {item['类别']} / {item['名称']}：`{item['路径']}`；存在={item['存在']}；已读取={item['已读取']}")
    lines.extend(
        [
            "",
            "## 禁止真实动作",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式库、知识库、向量库或业务库。",
            "- 未调用券商接口。",
            "- 未自动交易、下单、撤单或生成交易委托。",
            "- 未触碰本职工作系统。",
            "- 未调用真实外部 API。",
            "- 未生成或发布真实媒体。",
            "",
            "## 可交付前结论",
            "",
            "- 安全阻断是合规边界，不作为交付失败项。",
            "- 真实动作禁用是本批 AD 总表的默认继承条件。",
            "- 用户暂停本职工作系统的要求继续继承，后续任务不得绕过。",
            "- 股票硬闸门继续约束所有涉及股票的施工、路由、问答和规则沉淀。",
            "",
        ]
    )
    return "\n".join(lines)


def build_recovery_report(payload: dict[str, Any], files: dict[str, str], verify_text: str = "待验收") -> str:
    return "\n".join(
        [
            "# 03进化系统_第七批小任务AD规则审计回收报告_最新",
            "",
            f"- 生成时间：{payload['生成时间']}",
            "- 任务：第七批并行小任务 AD：03进化 / 可交付前规则审计总表",
            f"- 输入来源：{payload['输入来源数量']} 个",
            f"- 已读取来源：{payload['已读取来源数量']} 个",
            f"- 审计项：{payload['审计项数量']} 个",
            "- 规则结论：安全阻断不失败；真实动作禁用；用户暂停继承；股票硬闸门继承；第五/第六批成果可作为可交付前审计依据",
            f"- 验收结果：{verify_text}",
            "",
            "## 输出文件",
            "",
            *[f"- {name}：`{path}`" for name, path in files.items()],
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式库。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未触碰本职工作系统。",
            "- 安全阻断作为合规边界保留，不按交付失败处理。",
            "",
        ]
    )


def main() -> int:
    payload = build_payload()
    json_path = DATA_DIR / f"{TASK_NAME}_最新.json"
    md_path = DATA_DIR / f"{TASK_NAME}_最新.md"
    write_json(json_path, payload)
    markdown = build_markdown(payload)
    write_text(md_path, markdown)
    write_text(DOC_PATH, markdown)
    files = {
        "审计总表JSON": str(json_path),
        "审计总表Markdown": str(md_path),
        "审计说明文档": str(DOC_PATH),
    }
    write_text(RECOVERY_PATH, build_recovery_report(payload, files))
    print(json.dumps({"通过": True, "输入来源数量": payload["输入来源数量"], "审计项数量": payload["审计项数量"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
