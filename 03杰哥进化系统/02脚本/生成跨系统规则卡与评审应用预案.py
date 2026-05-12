# -*- coding: utf-8 -*-
"""
名称：生成跨系统规则卡与评审应用预案.py
作用：固化 03 进化系统可复用规则卡，并生成跨系统评审小样本、正式接入口径和并行回收报告。
安全边界：只写入 03 进化系统的 02脚本/03数据/07文档，以及总管指定并行回收报告；不触发 n8n、不发送企业微信、不调用券商接口、不自动交易、不写正式库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE_NAME = "跨系统规则卡与评审应用预案"


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return system_root().parents[0]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rule_cards() -> list[dict[str, Any]]:
    return [
        {
            "规则ID": "EVO-CARD-D-001",
            "规则名": "股票交付闭环硬约束",
            "适用系统": ["01股票系统", "03进化系统", "00总管"],
            "触发条件": ["股票相关交付", "生成_最新 文件", "跨窗口并行验收"],
            "规则正文": "股票相关交付必须同时具备版本化产物、_最新 指针、验收记录、回滚口径和人工复核边界；不得把研究结论、候选信号或未验收脚本标记为正式可用。",
            "必须证据": ["版本化 JSON/Markdown", "_最新 JSON/Markdown", "验收 JSON/Markdown", "回滚或补救说明"],
            "阻断条件": ["缺少验收记录", "缺少回滚口径", "将研究输出等同于交易建议", "覆盖正式库前无人工确认"],
            "默认动作": "阻断正式交付，只允许补齐证据或进入影子验证。",
            "风险等级": "高",
        },
        {
            "规则ID": "EVO-CARD-D-002",
            "规则名": "股票自动交易硬闸门",
            "适用系统": ["01股票系统", "03进化系统"],
            "触发条件": ["券商接口", "下单", "自动交易", "实盘委托", "账户资金"],
            "规则正文": "任何股票自动交易、券商接口调用、实盘下单和账户动作默认禁用；研究、复盘、规则沉淀、影子评审均不得隐含开通真实交易权限。",
            "必须证据": ["自动交易禁用声明", "券商接口未调用声明", "人工授权缺省为否", "真实动作审计字段"],
            "阻断条件": ["出现自动下单路径", "调用券商接口", "用灰度授权替代交易授权", "将研究信号写入实盘执行链路"],
            "默认动作": "立即阻断真实动作，保留离线评审和人工复核输出。",
            "风险等级": "极高",
        },
        {
            "规则ID": "EVO-CARD-D-003",
            "规则名": "并行施工容量与写入边界",
            "适用系统": ["00总管", "01股票系统", "02扩展系统", "03进化系统"],
            "触发条件": ["多窗口并行施工", "同名 _最新 文件", "跨系统回收"],
            "规则正文": "并行任务必须声明窗口身份、写入范围、禁止范围、回收文件和验收口径；不得覆盖其他窗口产物，不得回滚未知来源改动。",
            "必须证据": ["任务身份", "限定写入目录", "回收报告", "验收结果", "未触碰禁止范围声明"],
            "阻断条件": ["写入未授权目录", "修改他人任务文件", "回滚未知改动", "缺少固定回收报告"],
            "默认动作": "暂停扩展写入，只在授权范围内补齐本任务产物。",
            "风险等级": "高",
        },
        {
            "规则ID": "EVO-CARD-D-004",
            "规则名": "影子、灰度、真实动作分层边界",
            "适用系统": ["01股票系统", "02企业微信助手", "02内容处理", "03知识库", "00总管"],
            "触发条件": ["dry-run", "shadow", "灰度", "真实发送", "真实写库", "正式派工"],
            "规则正文": "影子验证只读或写本地候选，不产生外部副作用；灰度只允许白名单、限量、可回滚动作；真实动作必须有单独明确授权、审计日志和停止条件。",
            "必须证据": ["动作等级", "白名单或授权", "限量阈值", "回滚/停止条件", "审计记录"],
            "阻断条件": ["影子阶段触发外部动作", "灰度无白名单", "真实动作无明确授权", "用一次授权扩面到其他动作"],
            "默认动作": "降级为影子验证或阻断真实动作。",
            "风险等级": "极高",
        },
        {
            "规则ID": "EVO-CARD-D-005",
            "规则名": "真实发送、n8n 与正式库隔离",
            "适用系统": ["02企业微信助手", "02内容处理", "03知识库", "00总管"],
            "触发条件": ["企业微信真实发送", "n8n 工作流", "正式库写入", "外部发布"],
            "规则正文": "n8n、企业微信真实发送、外部发布和正式库写入均为独立高风险动作；本地评审、规则沉淀和样本生成不得触发这些动作，也不得把禁用声明解释为授权。",
            "必须证据": ["n8n 未触发", "真实发送未触发", "正式库未写入", "外部发布未执行"],
            "阻断条件": ["真实发送开关开启", "n8n 触发器启用", "写入正式库", "把候选内容直接发布"],
            "默认动作": "阻断外部副作用，仅输出本地候选和评审报告。",
            "风险等级": "极高",
        },
    ]


def review_samples() -> list[dict[str, Any]]:
    return [
        {
            "样本ID": "D-SAMPLE-001",
            "系统": "股票",
            "场景": "股票复盘候选规则准备进入正式交付闭环",
            "输入摘要": "已有候选规则和 _最新 文件，但缺少交易禁用声明与回滚口径。",
            "命中规则": ["EVO-CARD-D-001", "EVO-CARD-D-002"],
            "评审结果": "阻断",
            "阻断项": ["缺少回滚口径", "自动交易禁用证据不足"],
            "允许动作": ["补齐验收记录", "影子回测", "人工复核"],
            "禁止动作": ["自动交易", "券商接口调用", "写入实盘执行链路"],
        },
        {
            "样本ID": "D-SAMPLE-002",
            "系统": "企业微信助手",
            "场景": "把日报候选内容发送到企业微信群",
            "输入摘要": "内容已生成，但没有白名单、限量阈值和真实发送授权。",
            "命中规则": ["EVO-CARD-D-004", "EVO-CARD-D-005"],
            "评审结果": "阻断",
            "阻断项": ["真实发送无明确授权", "灰度白名单缺失"],
            "允许动作": ["生成本地预览", "写入候选报告", "等待人工确认"],
            "禁止动作": ["企业微信真实发送", "触发 n8n", "扩面群发"],
        },
        {
            "样本ID": "D-SAMPLE-003",
            "系统": "知识库",
            "场景": "把本轮规则卡接入正式知识库",
            "输入摘要": "规则卡已结构化，但尚未经过正式接入口径审批。",
            "命中规则": ["EVO-CARD-D-003", "EVO-CARD-D-005"],
            "评审结果": "需人工复核",
            "阻断项": ["正式库写入授权缺失"],
            "允许动作": ["写入 03 本地候选", "输出接入口径", "提交总管回收"],
            "禁止动作": ["直接写正式库", "覆盖现有知识库条目"],
        },
        {
            "样本ID": "D-SAMPLE-004",
            "系统": "内容处理/视频",
            "场景": "视频脚本候选准备外部发布或自动分发",
            "输入摘要": "视频文案可用于样片，但没有发布授权、停止条件和审计记录。",
            "命中规则": ["EVO-CARD-D-004", "EVO-CARD-D-005"],
            "评审结果": "阻断",
            "阻断项": ["外部发布无明确授权", "审计记录缺失"],
            "允许动作": ["本地样片生成", "人工审稿", "影子质检"],
            "禁止动作": ["外部发布", "n8n 自动分发", "写正式素材库"],
        },
        {
            "样本ID": "D-SAMPLE-005",
            "系统": "总管派工",
            "场景": "多个窗口同时回收 01/02/03 系统小任务",
            "输入摘要": "任务有并行回收路径，但需要确认每个窗口的写入边界和固定回收报告。",
            "命中规则": ["EVO-CARD-D-003", "EVO-CARD-D-004"],
            "评审结果": "通过但限界",
            "阻断项": [],
            "允许动作": ["只写本窗口回收报告", "读取其他系统验收摘要", "标注剩余风险"],
            "禁止动作": ["覆盖其他窗口产物", "回滚未知改动", "替其他系统写正式结果"],
        },
    ]


def build_payload() -> dict[str, Any]:
    cards = rule_cards()
    samples = review_samples()
    blockers = [item for sample in samples for item in sample["阻断项"]]
    return {
        "生成时间": now_text(),
        "任务": "03杰哥进化系统规则固化与跨系统评审应用预案",
        "规则卡数量": len(cards),
        "评审样本数量": len(samples),
        "阻断项数量": len(blockers),
        "规则卡": cards,
        "跨系统评审小样本": samples,
        "后续正式接入口径": {
            "接入前置": ["只接入结构化规则卡和评审结果", "先入候选区或影子区", "由总管或人工授权后再进入正式库"],
            "接入步骤": [
                "03 进化系统保留 JSON/Markdown 双格式规则卡",
                "总管读取固定回收报告，只做派工汇总，不自动触发外部动作",
                "知识库正式接入前执行重复检查、版本标识和人工确认",
                "股票、企业微信、n8n、正式库写入分别走独立授权",
            ],
            "不接入口径": ["不接券商接口", "不接自动交易", "不接企业微信真实发送", "不触发 n8n", "不写正式库"],
        },
        "安全边界": {
            "自动交易启用": False,
            "券商接口调用": False,
            "n8n触发": False,
            "企业微信真实发送": False,
            "正式库写入": False,
            "外部发布": False,
            "只写授权目录": True,
            "正式动作默认": "禁用",
        },
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 03 进化系统跨系统规则卡与评审应用预案",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 规则卡数量：{payload['规则卡数量']}",
        f"- 评审样本数量：{payload['评审样本数量']}",
        f"- 阻断项数量：{payload['阻断项数量']}",
        "- 安全边界：自动交易、券商接口、n8n、企业微信真实发送、正式库写入、外部发布均禁用",
        "",
        "## 规则卡",
        "",
    ]
    for card in payload["规则卡"]:
        lines.extend(
            [
                f"### {card['规则ID']} {card['规则名']}",
                f"- 适用系统：{'、'.join(card['适用系统'])}",
                f"- 风险等级：{card['风险等级']}",
                f"- 规则正文：{card['规则正文']}",
                f"- 阻断条件：{'；'.join(card['阻断条件'])}",
                f"- 默认动作：{card['默认动作']}",
                "",
            ]
        )
    lines.extend(["## 跨系统评审小样本", ""])
    for sample in payload["跨系统评审小样本"]:
        blockers = "无" if not sample["阻断项"] else "；".join(sample["阻断项"])
        lines.extend(
            [
                f"### {sample['样本ID']} {sample['系统']}",
                f"- 场景：{sample['场景']}",
                f"- 命中规则：{'、'.join(sample['命中规则'])}",
                f"- 评审结果：{sample['评审结果']}",
                f"- 阻断项：{blockers}",
                f"- 允许动作：{'；'.join(sample['允许动作'])}",
                f"- 禁止动作：{'；'.join(sample['禁止动作'])}",
                "",
            ]
        )
    lines.extend(
        [
            "## 后续正式接入口径",
            "",
            "### 接入前置",
            *[f"- {item}" for item in payload["后续正式接入口径"]["接入前置"]],
            "",
            "### 接入步骤",
            *[f"- {item}" for item in payload["后续正式接入口径"]["接入步骤"]],
            "",
            "### 不接入口径",
            *[f"- {item}" for item in payload["后续正式接入口径"]["不接入口径"]],
            "",
        ]
    )
    return "\n".join(lines)


def build_recovery_report(payload: dict[str, Any], files: dict[str, str]) -> str:
    blocked_samples = [s for s in payload["跨系统评审小样本"] if s["阻断项"]]
    return "\n".join(
        [
            "# 03进化系统_本轮小任务D回收报告_最新",
            "",
            f"- 生成时间：{payload['生成时间']}",
            "- 任务：03杰哥进化系统规则固化与跨系统评审应用预案",
            f"- 规则卡数量：{payload['规则卡数量']}",
            f"- 评审样本数量：{payload['评审样本数量']}",
            f"- 阻断项数量：{payload['阻断项数量']}",
            f"- 存在阻断样本：{len(blocked_samples)}",
            "- 验收状态：等待验证脚本最终写入验收报告；生成脚本已完成本地候选产物。",
            "",
            "## 新增/刷新文件",
            "",
            *[f"- {name}：{path}" for name, path in files.items()],
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未写正式库。",
            "- 未修改 01/02 系统业务脚本或股票核心脚本。",
            "",
            "## 后续口径",
            "",
            "- 正式接入前只允许进入候选区/影子区。",
            "- 股票、企业微信、n8n、正式库写入必须分开授权。",
            "- 总管只读取本回收报告做并行汇总，不据此自动触发真实动作。",
            "",
        ]
    )


def main() -> int:
    root = system_root()
    data_dir = root / "03数据" / "23跨系统规则卡与评审应用预案"
    doc_dir = root / "07文档"
    recovery_path = repo_root() / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_本轮小任务D回收报告_最新.md"
    payload = build_payload()
    tag = stamp()

    json_name = f"{PACKAGE_NAME}_{tag}.json"
    md_name = f"{PACKAGE_NAME}_{tag}.md"
    latest_json = data_dir / f"{PACKAGE_NAME}_最新.json"
    latest_md = data_dir / f"{PACKAGE_NAME}_最新.md"
    version_json = data_dir / json_name
    version_md = data_dir / md_name
    doc_path = doc_dir / "跨系统规则卡正式接入口径_最新.md"

    write_json(version_json, payload)
    write_json(latest_json, payload)
    markdown = build_markdown(payload)
    write_text(version_md, markdown)
    write_text(latest_md, markdown)
    write_text(doc_path, "\n".join(markdown.splitlines()[markdown.splitlines().index("## 后续正式接入口径") :]))

    files = {
        "规则卡与评审 JSON": str(latest_json),
        "规则卡与评审 Markdown": str(latest_md),
        "正式接入口径文档": str(doc_path),
        "版本化 JSON": str(version_json),
        "版本化 Markdown": str(version_md),
    }
    write_text(recovery_path, build_recovery_report(payload, files))

    print(json.dumps({"通过": True, "规则卡数量": payload["规则卡数量"], "评审样本数量": payload["评审样本数量"], "阻断项数量": payload["阻断项数量"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
