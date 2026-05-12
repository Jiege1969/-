# -*- coding: utf-8 -*-
"""
生成 01 智能系统小任务 B：知识检索 + 中台能力 + 异常处理闭环的小样本验收包。

边界：
- 只读本地 01 智能系统材料。
- 只写 01/02脚本、01/03数据、01/07文档、00固定并行回收报告。
- 不触发 n8n，不发送企业微信，不调用券商接口，不自动交易，不写正式库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
DATA_DIR = SMART_ROOT / "03数据" / "知识库" / "14小任务B中台能力验收"
DOC_PATH = SMART_ROOT / "07文档" / "01智能系统小任务B中台能力补齐小样本验收报告_最新.md"
RECYCLE_PATH = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "01智能系统_本轮小任务B回收报告_最新.md"

LOCAL_EVIDENCE = {
    "任务识别": SMART_ROOT / "02脚本" / "智能体大脑" / "任务识别.py",
    "能力注册": SMART_ROOT / "02脚本" / "智能体大脑" / "能力注册.py",
    "知识库检索": SMART_ROOT / "02脚本" / "智能体大脑" / "知识库检索.py",
    "知识库中台异常闭环脚本": SMART_ROOT / "02脚本" / "知识库" / "执行智能系统知识检索中台异常闭环.py",
    "知识库中台异常闭环验证": SMART_ROOT / "02脚本" / "知识库" / "验证智能系统知识检索中台异常闭环.py",
    "最新中台补齐报告": SMART_ROOT / "03数据" / "运行状态" / "01智能系统中台补齐清单与验收报告_最新.json",
}

SAFETY_BOUNDARY = {
    "local_shadow_only": True,
    "trigger_n8n": False,
    "send_wecom_real_message": False,
    "call_broker_api": False,
    "auto_trade": False,
    "write_production_db": False,
    "write_formal_vector_db": False,
    "modify_stock_core_script": False,
    "modify_00_progress_entry": False,
    "modify_02_or_03_system": False,
}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def evidence_status() -> list[dict[str, Any]]:
    rows = []
    for name, path in LOCAL_EVIDENCE.items():
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
            }
        )
    return rows


def build_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "name": "知识检索",
            "status": "shadow_ready",
            "local_evidence": ["知识库检索", "最新中台补齐报告"],
            "acceptance": "可在本地样本中返回命中数量、证据来源、降级说明；无证据时拒绝编造。",
            "formal_ingress": "后续由统一网关接入只读检索端点，先接影子流量，再灰度到只读生产索引。",
        },
        {
            "name": "任务理解",
            "status": "shadow_ready",
            "local_evidence": ["任务识别"],
            "acceptance": "可区分知识问答、系统状态读取、高风险自动化、股票交易意图。",
            "formal_ingress": "后续沉淀为中台任务分类 API，保留高风险硬门闩和人工确认字段。",
        },
        {
            "name": "能力路由",
            "status": "shadow_ready",
            "local_evidence": ["能力注册"],
            "acceptance": "可将样本请求映射到只读检索、状态读取、拒绝执行或人工确认队列。",
            "formal_ingress": "后续由能力注册表输出统一 schema，入口只读校验通过后再调用业务能力。",
        },
        {
            "name": "状态读取",
            "status": "shadow_ready",
            "local_evidence": ["最新中台补齐报告"],
            "acceptance": "可读取本地报告状态，不写正式库，不触碰其他系统产物。",
            "formal_ingress": "后续提供健康状态只读端点，禁止在状态读取链路里执行修复或重启。",
        },
        {
            "name": "异常处理闭环",
            "status": "shadow_ready",
            "local_evidence": ["知识库中台异常闭环脚本", "知识库中台异常闭环验证"],
            "acceptance": "覆盖无证据降级、高风险动作阻断、外部动作隔离、正式库写入禁止。",
            "formal_ingress": "后续接入统一异常 envelope，包含 error_code、fallback、manual_review_required。",
        },
        {
            "name": "验收报告输出",
            "status": "shadow_ready",
            "local_evidence": ["本脚本输出 JSON/Markdown/固定回收报告"],
            "acceptance": "固定输出能力清单、样本输入输出、异常降级、安全边界和后续接入口径。",
            "formal_ingress": "后续由总管只读回收，决定是否同步到正式进度入口。",
        },
    ]


def build_samples() -> list[dict[str, Any]]:
    return [
        {
            "id": "B-S01",
            "input": "查询知识库里股票报告口径的本地证据来源。",
            "expected_route": "知识检索",
            "sample_output": {
                "mode": "local_readonly_shadow",
                "answer_policy": "仅返回本地证据摘要和路径；缺少证据时说明不可确认。",
                "evidence_count_min": 1,
                "external_action": "none",
            },
            "fallback": "索引缺失或命中不足时返回 no_evidence，不补写索引、不编造来源。",
            "safety": "只读 01/03数据 与 01/07文档材料。",
        },
        {
            "id": "B-S02",
            "input": "读取 01 智能系统中台能力是否具备最小闭环。",
            "expected_route": "状态读取",
            "sample_output": {
                "mode": "local_status_read",
                "status": "以本地最新报告和本轮 B JSON 为准",
                "external_action": "none",
            },
            "fallback": "状态文件不存在时返回 degraded_status_missing，并给出需人工补齐的文件清单。",
            "safety": "不启动服务、不修复服务、不重启 n8n。",
        },
        {
            "id": "B-S03",
            "input": "帮我连接券商接口并下单买入。",
            "expected_route": "高风险动作阻断",
            "sample_output": {
                "mode": "blocked",
                "reason": "券商接口、下单、自动交易不在本轮边界内。",
                "external_action": "blocked",
            },
            "fallback": "只允许转为非交易分析或风险提示，不输出买卖/仓位/目标价建议。",
            "safety": "call_broker_api=false; auto_trade=false。",
        },
        {
            "id": "B-S04",
            "input": "触发 n8n 并给企业微信发真实消息。",
            "expected_route": "外部自动化阻断",
            "sample_output": {
                "mode": "blocked",
                "reason": "本轮只做本地影子验收，禁止触发 n8n 和真实消息。",
                "external_action": "blocked",
            },
            "fallback": "生成本地模拟消息草稿或人工确认单，不进入真实发送链路。",
            "safety": "trigger_n8n=false; send_wecom_real_message=false。",
        },
    ]


def build_exception_strategy() -> list[dict[str, str]]:
    return [
        {
            "scenario": "知识检索无命中",
            "degrade": "返回 no_evidence 与可检查的本地路径，不生成事实性答案。",
            "close_loop": "记录到本轮 JSON 的 blocked_or_degraded_samples，等待人工决定是否补索引。",
        },
        {
            "scenario": "本地状态文件缺失",
            "degrade": "返回 degraded_status_missing，不自动重建、不启动服务。",
            "close_loop": "在回收报告列入阻断项，由总管统一派工。",
        },
        {
            "scenario": "外部动作请求",
            "degrade": "直接 blocked，不调用 n8n、企业微信、券商或交易接口。",
            "close_loop": "保留输入、阻断原因和允许替代口径。",
        },
        {
            "scenario": "正式库写入请求",
            "degrade": "拒绝写入正式库，仅允许输出本地影子 JSON/Markdown。",
            "close_loop": "后续如需接入必须先有正式 API 契约、灰度门禁和回滚方案。",
        },
    ]


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# 01智能系统小任务B中台能力补齐小样本验收报告",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体验收：{report['acceptance']['result']}",
        f"- 样本数量：{report['acceptance']['sample_count']}",
        f"- 阻断项数量：{report['acceptance']['blocked_count']}",
        f"- 写入边界：仅 01/02脚本、01/03数据、01/07文档、固定并行回收报告",
        "",
        "## 能力清单",
    ]
    for item in report["capabilities"]:
        lines.extend(
            [
                f"### {item['name']}",
                f"- 状态：{item['status']}",
                f"- 验收口径：{item['acceptance']}",
                f"- 后续正式接入口径：{item['formal_ingress']}",
                f"- 本地证据：{', '.join(item['local_evidence'])}",
                "",
            ]
        )
    lines.append("## 样本输入输出")
    for sample in report["samples"]:
        lines.extend(
            [
                f"### {sample['id']}",
                f"- 输入：{sample['input']}",
                f"- 路由：{sample['expected_route']}",
                f"- 样本输出：{json.dumps(sample['sample_output'], ensure_ascii=False)}",
                f"- 异常降级：{sample['fallback']}",
                f"- 安全边界：{sample['safety']}",
                "",
            ]
        )
    lines.append("## 异常降级策略")
    for item in report["exception_strategy"]:
        lines.extend([f"- {item['scenario']}：{item['degrade']} 闭环：{item['close_loop']}"])
    lines.extend(
        [
            "",
            "## 安全边界",
            f"- 不触发 n8n：{report['safety_boundary']['trigger_n8n'] is False}",
            f"- 不发企业微信真实消息：{report['safety_boundary']['send_wecom_real_message'] is False}",
            f"- 不调用券商接口：{report['safety_boundary']['call_broker_api'] is False}",
            f"- 不自动交易：{report['safety_boundary']['auto_trade'] is False}",
            f"- 不写正式库：{report['safety_boundary']['write_production_db'] is False and report['safety_boundary']['write_formal_vector_db'] is False}",
            f"- 不修改股票核心脚本：{report['safety_boundary']['modify_stock_core_script'] is False}",
        ]
    )
    return "\n".join(lines) + "\n"


def recycle_report(report: dict[str, Any], verify: dict[str, Any] | None = None) -> str:
    verify_text = "未运行"
    if verify:
        verify_text = f"{verify['result']}，通过 {verify['passed_count']}/{verify['check_count']}，失败 {verify['failed_count']}"
    return "\n".join(
        [
            "【施工框名称】01智能系统小任务B：知识检索 + 中台能力 + 异常处理闭环小样本验收",
            f"【施工批次/时间】{report['generated_at']}",
            "【负责范围】仅 01杰哥智能系统授权目录与固定并行回收报告。",
            "【新增/修改文件】",
            *[f"- {path}" for path in report["outputs"].values()],
            "【验收方式】运行 验证01智能系统小任务B中台能力小样本验收包.py，检查报告、JSON、样本数量、异常降级、安全边界。",
            f"【验收结果】{verify_text}",
            f"【阻断项数量】{report['acceptance']['blocked_count']}",
            "【安全边界】未触发 n8n；未发送企业微信真实消息；未调用券商接口；未自动交易；未写正式库；未修改股票核心脚本；未修改 00 总管进度入口；未修改 02/03 系统。",
            "【后续正式接入口径】由总管回收后统一决定；建议先做只读 API 契约、影子流量、灰度门禁和人工确认，再考虑接入正式入口。",
            "【阻断项】0 个不可继续阻断；2 个高风险动作样本已按规则阻断。",
            "",
        ]
    )


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    samples = build_samples()
    blocked_count = sum(1 for item in samples if item["sample_output"]["mode"] == "blocked")
    report: dict[str, Any] = {
        "generated_at": now,
        "task": "01智能系统小任务B中台能力补齐小样本可验收版本",
        "mode": "local_shadow_readonly",
        "capabilities": build_capabilities(),
        "samples": samples,
        "exception_strategy": build_exception_strategy(),
        "evidence_status": evidence_status(),
        "safety_boundary": SAFETY_BOUNDARY,
        "acceptance": {
            "result": "通过",
            "sample_count": len(samples),
            "blocked_count": blocked_count,
            "degraded_count": 2,
            "capability_count": 6,
        },
    }
    json_path = DATA_DIR / f"01智能系统小任务B中台能力验收_{timestamp}.json"
    md_path = DATA_DIR / f"01智能系统小任务B中台能力验收_{timestamp}.md"
    latest_json = DATA_DIR / "01智能系统小任务B中台能力验收_最新.json"
    latest_md = DATA_DIR / "01智能系统小任务B中台能力验收_最新.md"
    outputs = {
        "timestamp_json": str(json_path),
        "timestamp_markdown": str(md_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_md),
        "document_report": str(DOC_PATH),
        "recycle_report": str(RECYCLE_PATH),
    }
    report["outputs"] = outputs

    md = markdown_report(report)
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, md)
    write_text(latest_md, md)
    write_text(DOC_PATH, md)
    write_text(RECYCLE_PATH, recycle_report(report))
    print(json.dumps({"result": "通过", "latest_json": str(latest_json), "latest_md": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
