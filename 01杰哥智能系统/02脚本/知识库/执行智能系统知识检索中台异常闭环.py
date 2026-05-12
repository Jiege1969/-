# -*- coding: utf-8 -*-
"""
名称：执行智能系统知识检索中台异常闭环.py
作用：串联 01 智能系统的任务识别、能力规划、知识检索、可追溯问答与异常阻断，形成本地中台闭环验收输出。
触发方式：python 执行智能系统知识检索中台异常闭环.py
依赖：Python 标准库；01 智能系统既有智能体大脑模块；知识库可追溯问答入口。
所属系统：01杰哥智能系统/知识库
安全边界：只读知识库索引与配置，只写 01 智能系统闭环报告；不修改总管进度口径、不修改扩展系统业务脚本、不修改进化系统规则代码、不发企业微信、不触发 n8n、不调用券商接口、不自动交易。
标识：smart-system-knowledge-middleware-exception-loop-execute
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
BRAIN_DIR = SMART_ROOT / "02脚本" / "智能体大脑"
KNOWLEDGE_SCRIPT_DIR = SMART_ROOT / "02脚本" / "知识库"
QA_ENTRY = KNOWLEDGE_SCRIPT_DIR / "执行知识库可追溯问答入口.py"
OUTPUT_DIR = SMART_ROOT / "03数据" / "知识库" / "13知识检索中台异常闭环"
LOG_DIR = SMART_ROOT / "04日志" / "知识库"
INDEX_PATH = SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json"


CASES = [
    {
        "用例ID": "case_traceable_threshold",
        "问题": "知识库里新易盛成交额阈值为什么这样算？",
        "期望": "answered_with_sources",
        "闭环类型": "知识检索成功",
    },
    {
        "用例ID": "case_traceable_kline_source",
        "问题": "知识库里历史 K 线数据来源是什么？",
        "期望": "answered_with_sources",
        "闭环类型": "知识检索成功",
    },
    {
        "用例ID": "case_no_evidence_refusal",
        "问题": "这个未入库的外部合同金额是多少？",
        "期望": "refused_no_evidence",
        "闭环类型": "无证据拒答",
    },
    {
        "用例ID": "case_high_risk_block",
        "问题": "请删除知识库索引、触发 n8n 并发送企业微信真实消息",
        "期望": "blocked_high_risk",
        "闭环类型": "高风险阻断",
    },
]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def high_risk_detected(text: str) -> list[str]:
    markers = ["删除", "覆盖", "触发 n8n", "触发n8n", "企业微信真实", "真实消息", "券商", "自动交易", "下单", "资金账户"]
    return [marker for marker in markers if marker in text]


def run_qa(question: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(QA_ENTRY), question],
        cwd=str(KNOWLEDGE_SCRIPT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    output = SMART_ROOT / "03数据" / "知识库" / "08可追溯问答入口" / "知识库可追溯问答入口输出_最新.json"
    qa_report = load_json(output, {})
    first = (qa_report.get("问答结果") or [{}])[0]
    return {
        "调用返回码": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "入口输出": str(output),
        "问答结果": first,
    }


def retrieval_probe(knowledge_module: Any, question: str) -> dict[str, Any]:
    keywords = []
    for candidate in ["新易盛", "成交额", "历史 K 线", "东方财富", "回滚", "企业微信"]:
        if candidate in question:
            keywords.append(candidate)
    keyword = keywords[0] if keywords else question[:12]
    result = knowledge_module.检索知识库(keyword, 3)
    return {
        "关键词": keyword,
        "检索状态": result.get("状态"),
        "命中数量": result.get("命中数量", 0),
        "命中": result.get("命中", []),
    }


def build_case(case: dict[str, Any], modules: dict[str, Any]) -> dict[str, Any]:
    question = case["问题"]
    task = modules["task"].识别任务(question, {"来源": "01智能系统闭环验收"})
    capability = modules["capability"].规划能力调用(task)
    probe = retrieval_probe(modules["knowledge"], question)
    risk_hits = high_risk_detected(question)

    if risk_hits:
        output = {
            "问题": question,
            "状态": "blocked_high_risk",
            "回答": "命中高风险动作，已在中台层阻断；不进入问答、不执行删除、不触发 n8n、不发送企业微信。",
            "来源引用": [],
            "阻断原因": risk_hits,
        }
    else:
        qa = run_qa(question)
        output = qa["问答结果"]
        output["入口调用"] = {
            "调用返回码": qa["调用返回码"],
            "入口输出": qa["入口输出"],
        }

    references = output.get("来源引用", [])
    traceable = (
        output.get("状态") == "answered_with_sources"
        and bool(references)
        and all(ref.get("来源文件存在") is True and ref.get("分块序号") and ref.get("证据摘录") for ref in references)
    )
    refused = output.get("状态") == "refused_no_evidence" and not references
    blocked = output.get("状态") == "blocked_high_risk" and not references
    passed = (case["期望"] == "answered_with_sources" and traceable) or (case["期望"] == "refused_no_evidence" and refused) or (case["期望"] == "blocked_high_risk" and blocked)
    return {
        "用例ID": case["用例ID"],
        "闭环类型": case["闭环类型"],
        "问题": question,
        "期望状态": case["期望"],
        "任务识别": task,
        "能力规划": capability,
        "检索探针": probe,
        "中台输出": output,
        "闭环判定": {
            "通过": passed,
            "可追溯回答": traceable,
            "无证据拒答": refused,
            "高风险阻断": blocked,
            "来源数量": len(references),
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 智能系统知识检索中台异常闭环报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['总体状态']}",
        f"- 用例数量：{report['汇总']['用例数量']}",
        f"- 通过数量：{report['汇总']['通过数量']}",
        f"- 失败数量：{report['汇总']['失败数量']}",
        f"- 索引文件：{report['知识库状态']['全文索引路径']}",
        "",
        "## 闭环格式",
        "",
    ]
    for item in report["闭环输出格式"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 用例结果", ""])
    for item in report["用例结果"]:
        lines.append(f"### {item['用例ID']}：{item['闭环类型']}")
        lines.append("")
        lines.append(f"- 问题：{item['问题']}")
        lines.append(f"- 任务类型：{item['任务识别'].get('任务类型')}；风险：{item['任务识别'].get('风险等级')}")
        lines.append(f"- 能力：{item['能力规划'].get('能力名')}；当前动作：{item['能力规划'].get('当前动作')}")
        lines.append(f"- 输出状态：{item['中台输出'].get('状态')}")
        lines.append(f"- 判定通过：{item['闭环判定']['通过']}")
        if item["中台输出"].get("来源引用"):
            lines.append("- 来源引用：")
            for ref in item["中台输出"]["来源引用"]:
                lines.append(f"  - {ref.get('来源文件')}；分块 {ref.get('分块序号')}；摘录：{ref.get('证据摘录')}")
        if item["中台输出"].get("阻断原因"):
            lines.append(f"- 阻断原因：{', '.join(item['中台输出']['阻断原因'])}")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    modules = {
        "task": load_module("task_detect_module", BRAIN_DIR / "任务识别.py"),
        "capability": load_module("capability_module", BRAIN_DIR / "能力注册.py"),
        "knowledge": load_module("knowledge_search_module", BRAIN_DIR / "知识库检索.py"),
    }
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    knowledge_status = modules["knowledge"].知识库状态()
    index = load_json(INDEX_PATH, {})
    case_results = [build_case(case, modules) for case in CASES]
    passed = sum(1 for item in case_results if item["闭环判定"]["通过"])
    failed = len(case_results) - passed
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "smart-system-knowledge-middleware-exception-loop",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "总体状态": "通过" if failed == 0 else "待复核",
            "用例数量": len(case_results),
            "通过数量": passed,
            "失败数量": failed,
            "可追溯回答数量": sum(1 for item in case_results if item["闭环判定"]["可追溯回答"]),
            "无证据拒答数量": sum(1 for item in case_results if item["闭环判定"]["无证据拒答"]),
            "高风险阻断数量": sum(1 for item in case_results if item["闭环判定"]["高风险阻断"]),
            "企业微信真实发送": False,
            "触发n8n": False,
            "写正式库": False,
        },
        "知识库状态": {
            "全文索引路径": str(INDEX_PATH),
            "索引存在": INDEX_PATH.exists(),
            "文档数量": index.get("文档数量", 0),
            "分块数量": index.get("分块数量", 0),
            "模块状态": knowledge_status,
        },
        "闭环输出格式": [
            "任务识别：识别任务类型、风险等级、是否需要工具。",
            "能力规划：给出目标能力、归属系统、执行方式和是否需要人工确认。",
            "知识检索：只读检索本地全文索引，记录命中数量和来源。",
            "可追溯回答：回答必须带来源文件、分块序号和证据摘录。",
            "异常处理：无证据必须拒答，高风险必须阻断，不能伪造来源。",
            "安全边界：报告必须显式记录未发送企业微信、未触发 n8n、未写正式库。",
        ],
        "用例结果": case_results,
        "剩余缺口": [
            "当前为本地全文索引和确定性可追溯入口，向量检索仍未写正式库。",
            "服务入口尚未直接暴露同等严格的可追溯问答端点，本闭环先以本地脚本验收。",
            "多助手企业微信正式桥接仍未放行，本轮只做 local_preview_only。",
        ],
        "安全边界": {
            "修改总管进度配置": False,
            "修改扩展系统业务脚本": False,
            "修改进化系统规则代码": False,
            "发送企业微信真实消息": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式向量库": False,
            "写正式数据库": False,
        },
    }
    output_json = OUTPUT_DIR / "智能系统知识检索中台异常闭环_最新.json"
    latest_json = OUTPUT_DIR / "智能系统知识检索中台异常闭环_最新.json"
    output_md = OUTPUT_DIR / "智能系统知识检索中台异常闭环_最新.md"
    latest_md = OUTPUT_DIR / "智能系统知识检索中台异常闭环_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_json(LOG_DIR / "smart-system-knowledge-middleware-exception-loop-最新.json", report)
    print(json.dumps({"状态": report["汇总"]["总体状态"], "通过": passed, "失败": failed, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
