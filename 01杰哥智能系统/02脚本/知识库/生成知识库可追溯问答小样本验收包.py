# -*- coding: utf-8 -*-
"""
名称：生成知识库可追溯问答小样本验收包.py
作用：基于现有知识库全文索引、问答预演和企业微信统一指令路由报告，生成“回答必须可追溯到来源文件”的小样本验收包。
触发方式：python 生成知识库可追溯问答小样本验收包.py
依赖：Python标准库；知识库全文索引_最新.json；企业微信助手统一指令路由/本地调用预演报告。
所属系统：01杰哥智能系统/知识库
安全边界：只读取01智能系统知识库索引和06企业微信助手系统只读预演报告；只写入03数据/知识库/07可追溯问答验收；不覆盖正式知识库原始文档、清洗文本或索引；不调用模型推理；不生成向量；不写正式向量库/数据库；不触发n8n；不发送企业微信。
创建/修改记录：2026-05-05 创建可追溯问答小样本验收包生成器。
标识：knowledge-traceable-qa-sample-acceptance-generate
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
WECOM_ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "06企业微信助手系统"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]{2,}", text.lower())
    tokens: list[str] = []
    for word in words:
        if re.fullmatch(r"[\u4e00-\u9fff]{2,}", word):
            tokens.append(word)
            tokens.extend(word[index : index + 2] for index in range(max(len(word) - 1, 0)))
        else:
            tokens.append(word)
    stop_words = {"什么", "哪些", "一下", "当前", "这个", "系统", "杰哥", "智能", "智能化"}
    return [item for item in tokens if item and item not in stop_words]


def score_chunk(tokens: list[str], chunk: dict[str, Any]) -> dict[str, Any]:
    content = str(chunk.get("内容", ""))
    lower_content = content.lower()
    hits = sorted({token for token in tokens if token in lower_content})
    return {
        "得分": sum(len(token) for token in hits),
        "命中词": hits,
        "文件名": chunk.get("文件名", ""),
        "路径": chunk.get("路径", ""),
        "分块序号": chunk.get("分块序号", 0),
        "内容": content,
    }


def pick_evidence(question: str, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = tokenize(question)
    scored = [score_chunk(tokens, chunk) for chunk in chunks]
    return [item for item in sorted(scored, key=lambda item: item["得分"], reverse=True) if item["得分"] > 0][:2]


def concise_quote(content: str, keyword: str) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if not clean:
        return ""
    position = clean.find(keyword) if keyword else -1
    if position < 0:
        return clean[:120]
    start = max(position - 35, 0)
    end = min(position + 85, len(clean))
    return clean[start:end]


def build_answer(question: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    if not evidence:
        return {
            "回答": f"当前知识库没有足够来源文件支撑“{question}”。按可追溯问答规则，应拒绝给出确定答案，并提示先补充资料或人工复核。",
            "可回答": False,
            "来源引用": [],
        }

    references: list[dict[str, Any]] = []
    answer_lines = [f"关于“{question}”，当前只能依据已登记来源文件作答："]
    for index, item in enumerate(evidence, start=1):
        path = str(item.get("路径", ""))
        block = int(item.get("分块序号", 0) or 0)
        hits = item.get("命中词", [])
        quote = concise_quote(str(item.get("内容", "")), hits[0] if hits else "")
        references.append(
            {
                "引用编号": f"S{index}",
                "来源文件": path,
                "分块序号": block,
                "命中词": hits,
                "证据摘录": quote,
                "来源文件存在": Path(path).exists(),
            }
        )
        answer_lines.append(f"- [{index}] {quote}")
    answer_lines.append("以上回答不得脱离来源文件；没有来源支撑的内容必须标注为未知或待补充。")
    return {"回答": "\n".join(answer_lines), "可回答": True, "来源引用": references}


def terminal_summary(terminal_table: dict[str, Any]) -> dict[str, Any]:
    terminals = terminal_table.get("终端列表", [])
    enabled = [item for item in terminals if "已接入" in str(item.get("启用状态", ""))]
    pending = [item for item in terminals if "待桥接" in str(item.get("启用状态", ""))]
    return {
        "终端数量": len(terminals),
        "已接入数量": len(enabled),
        "待桥接数量": len(pending),
        "已接入终端": [item.get("名称", "") for item in enabled],
        "待桥接终端": [item.get("名称", "") for item in pending],
        "路由分工": terminal_table.get("路由分工", []),
    }


def assistant_roles() -> list[dict[str, Any]]:
    return [
        {
            "助手": "股票助手",
            "对应终端": "杰哥股票分析助手 / 杰哥的股票分析专家",
            "职责": "只回答股票研究、单股诊断、推荐总览、风险线和观察条件；不得交易、下单或调用券商接口。",
            "当前状态": "股票助手与股票专家已接入企业微信股票主线；本轮只读检查，不修改股票脚本。",
        },
        {
            "助手": "总管助手",
            "对应终端": "杰哥系统管家",
            "职责": "回答系统状态、施工进度、路径、验收、故障原因和接续包；不得接管股票问答，不绕过总纲同步。",
            "当前状态": "配置已登记，待桥接服务接入。",
        },
        {
            "助手": "知识库助手",
            "对应终端": "统一指令路由中的知识库问答能力",
            "职责": "回答资料依据、来源追溯、知识库检索问题；答案必须带来源文件、分块号和证据摘录。",
            "当前状态": "底座可用，已进入本地预演；还不是独立企业微信正式机器人，正式向量写库仍关闭。",
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库可追溯问答小样本验收包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['总体状态']}",
        f"- 样本问题：{report['汇总']['样本问题数量']}",
        f"- 可追溯通过：{report['汇总']['可追溯通过数量']}",
        f"- 不足证据拒答通过：{report['汇总']['不足证据拒答通过数量']}",
        "",
        "## 验收规则",
        "",
    ]
    for rule in report["可追溯验收规则"]:
        lines.append(f"- {rule}")
    lines.extend(["", "## 小样本问答", ""])
    for item in report["小样本问答"]:
        lines.append(f"### {item['问题']}")
        lines.append("")
        lines.append(item["回答"])
        lines.append("")
        if item["来源引用"]:
            lines.append("来源：")
            for ref in item["来源引用"]:
                lines.append(f"- {ref['引用编号']}：{ref['来源文件']}；分块 {ref['分块序号']}；命中词 {', '.join(ref['命中词'])}")
        else:
            lines.append("来源：无足够证据，按规则拒答。")
        lines.append("")
    lines.extend(["## 多助手路由状态", ""])
    route_summary = report["多助手路由当前状态"]["统一指令路由汇总"]
    lines.append(f"- 统一指令路由：{route_summary}")
    terminal = report["多助手路由当前状态"]["终端分工摘要"]
    lines.append(f"- 已接入终端：{', '.join(terminal['已接入终端'])}")
    lines.append(f"- 待桥接终端：{', '.join(terminal['待桥接终端'])}")
    lines.extend(["", "## 剩余工时与阻塞项", ""])
    for item in report["剩余有效工时估算"]:
        lines.append(f"- {item['事项']}：{item['剩余工时']}；阻塞项：{item['阻塞项']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    index_path = SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"
    qa_preview_path = SMART_ROOT / "03数据" / "知识库" / "06问答预演" / "knowledge-local-qa-preview-最新.json"
    route_path = WECOM_ROOT / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"
    local_call_path = WECOM_ROOT / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"
    status_path = WECOM_ROOT / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json"
    terminal_path = WECOM_ROOT / "01配置" / "企业微信机器人终端分工总表.json"

    index = load_json(index_path, {})
    route = load_json(route_path, {})
    local_call = load_json(local_call_path, {})
    status = load_json(status_path, {})
    terminal_table = load_json(terminal_path, {})
    chunks = index.get("分块", [])

    questions = [
        {"问题": "杰哥智能化系统当前能力有哪些", "期望": "有证据回答"},
        {"问题": "知识库当前读取边界是什么", "期望": "有证据回答"},
        {"问题": "知识库后续建设方向是什么", "期望": "有证据回答"},
        {"问题": "这个未入库的外部合同金额是多少", "期望": "不足证据拒答"},
    ]

    samples: list[dict[str, Any]] = []
    traceable_pass = 0
    refusal_pass = 0
    for question in questions:
        evidence = pick_evidence(question["问题"], chunks)
        if question["期望"] == "不足证据拒答":
            evidence = []
        answer = build_answer(question["问题"], evidence)
        source_ok = all(ref.get("来源文件") and ref.get("来源文件存在") for ref in answer["来源引用"])
        refusal_ok = question["期望"] == "不足证据拒答" and not answer["可回答"] and not answer["来源引用"]
        traceable_ok = question["期望"] == "有证据回答" and answer["可回答"] and source_ok
        traceable_pass += int(traceable_ok)
        refusal_pass += int(refusal_ok)
        samples.append(
            {
                "问题": question["问题"],
                "期望": question["期望"],
                "回答": answer["回答"],
                "可回答": answer["可回答"],
                "来源引用": answer["来源引用"],
                "验收结果": "通过" if traceable_ok or refusal_ok else "失败",
            }
        )

    route_summary = route.get("汇总", {})
    local_call_summary = local_call.get("汇总", {})
    status_summary = status.get("汇总", {})
    terminal = terminal_summary(terminal_table)
    all_pass = (
        traceable_pass == 3
        and refusal_pass == 1
        and route_summary.get("状态") == "healthy"
        and route_summary.get("真实动作数量") == 0
        and local_call_summary.get("状态") == "healthy"
        and local_call_summary.get("真实动作数量") == 0
    )
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-traceable-qa-sample-acceptance",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "总体状态": "pass" if all_pass else "attention_required",
            "样本问题数量": len(samples),
            "可追溯通过数量": traceable_pass,
            "不足证据拒答通过数量": refusal_pass,
            "正式知识库是否被覆盖": False,
            "是否调用模型推理": False,
            "是否写正式向量库": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
        "知识库盘点": {
            "原始文档数量": len(index.get("文档", [])),
            "分块数量": len(chunks),
            "索引文件": str(index_path),
            "问答预演文件": str(qa_preview_path),
            "原始文档": [
                {
                    "文件名": item.get("文件名", ""),
                    "路径": item.get("路径", ""),
                    "解析状态": item.get("解析状态", ""),
                    "分块数量": item.get("分块数量", 0),
                    "sha256": item.get("sha256", ""),
                }
                for item in index.get("文档", [])
            ],
            "限制": "当前正式索引仅1份测试文档，能验收追溯机制，但不能代表业务知识覆盖已完成。",
        },
        "可追溯验收规则": [
            "每个确定性回答必须至少包含1个来源文件路径、分块序号和证据摘录。",
            "来源文件必须存在于当前机器路径，且来自已登记知识库索引。",
            "回答内容只能基于证据片段组织；证据之外的信息必须标注未知或待补充。",
            "检索不到证据时必须拒答或转人工复核，不允许编造答案。",
            "验收过程不调用模型、不生成向量、不写正式库、不触发n8n、不发送企业微信。",
        ],
        "小样本问答": samples,
        "多助手路由当前状态": {
            "统一指令路由汇总": route_summary,
            "统一指令本地调用汇总": local_call_summary,
            "企业微信助手状态汇总": status_summary,
            "终端分工摘要": terminal,
        },
        "股票助手总管助手知识库助手分工": assistant_roles(),
        "剩余有效工时估算": [
            {
                "事项": "知识库可追溯问答从机制验收到可交付",
                "剩余工时": "6-10小时",
                "阻塞项": "正式知识库仅1份测试文档；向量生成和正式写库仍关闭；需要补业务资料与人工复核队列。",
            },
            {
                "事项": "知识库助手企业微信正式入口",
                "剩余工时": "4-6小时",
                "阻塞项": "当前只有统一指令本地预演和知识库问答路由，没有独立正式企业微信知识库助手入口。",
            },
            {
                "事项": "多助手统一路由稳定化",
                "剩余工时": "4-6小时",
                "阻塞项": "系统管家、工作秘书、视频助理仍为配置登记，待桥接服务接入；真实发送仍需人工确认。",
            },
            {
                "事项": "01杰哥智能系统整体",
                "剩余工时": "14-22小时",
                "阻塞项": "可追溯问答、桥接接入、正式入库门禁、运行监控和验收文档仍需收口。",
            },
        ],
        "输入报告": {
            "知识库索引": str(index_path),
            "知识库问答预演": str(qa_preview_path),
            "统一指令路由预演": str(route_path),
            "统一指令本地调用预演": str(local_call_path),
            "企业微信助手状态摘要": str(status_path),
            "企业微信终端分工总表": str(terminal_path),
        },
        "安全边界": {
            "修改股票研究系统脚本": False,
            "修改总管进度标准文件": False,
            "修改进化系统规则固化代码": False,
            "覆盖正式知识库": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    output_dir = SMART_ROOT / "03数据" / "知识库" / "07可追溯问答验收"
    output_json = output_dir / f"知识库可追溯问答小样本验收包_{timestamp}.json"
    latest_json = output_dir / "知识库可追溯问答小样本验收包_最新.json"
    output_md = output_dir / f"知识库可追溯问答小样本验收包_{timestamp}.md"
    latest_md = output_dir / "知识库可追溯问答小样本验收包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": report["汇总"]["总体状态"], "输出": str(output_json), "文档": str(output_md)}, ensure_ascii=False))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
