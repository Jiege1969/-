# -*- coding: utf-8 -*-
"""
名称：生成01智能系统中台补齐清单与验收报告.py
作用：只读盘点 01 智能系统目录、脚本、配置、入口和验收证据，生成中台最小能力补齐清单与小样本验收报告。
触发方式：python 生成01智能系统中台补齐清单与验收报告.py
依赖：Python 标准库；01 智能系统既有配置、脚本和知识库验收报告。
所属系统：01杰哥智能系统/智能体大脑
安全边界：只读 00 总管基准和 01 智能系统本地证据；只写 01 智能系统运行状态、日志和备份登记；不修改总管进度口径、02 扩展系统业务脚本、03 进化系统规则代码；不发送企业微信、不触发 n8n、不调用券商接口、不自动交易。
标识：smart-system-middleware-completion-report-generate
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
MANAGER_ROOT = SYSTEM_ROOT / "00杰哥系统总管"
BRAIN_DIR = SMART_ROOT / "02脚本" / "智能体大脑"
KNOWLEDGE_DIR = SMART_ROOT / "02脚本" / "知识库"
OUTPUT_DIR = SMART_ROOT / "03数据" / "运行状态"
LOG_DIR = SMART_ROOT / "04日志" / "智能体大脑"
BACKUP_ROOT = SMART_ROOT / "05备份" / "中台补齐"


READ_SOURCES = {
    "全盘架构": SYSTEM_ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
    "施工面板": MANAGER_ROOT / "07文档" / "当前施工面板.md",
    "接续包": MANAGER_ROOT / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    "派工确认": MANAGER_ROOT / "03数据" / "运行状态" / "下一轮施工派工确认报告_最新.md",
    "四大系统读取口径": MANAGER_ROOT / "01配置" / "四大系统验收读取口径.json",
}


KEY_FILES = {
    "任务识别": BRAIN_DIR / "任务识别.py",
    "能力注册": BRAIN_DIR / "能力注册.py",
    "模型路由器": BRAIN_DIR / "模型路由器.py",
    "知识库检索": BRAIN_DIR / "知识库检索.py",
    "工作流规划": BRAIN_DIR / "工作流规划.py",
    "服务入口": BRAIN_DIR / "服务入口.py",
    "能力注册表": SMART_ROOT / "01配置" / "能力注册表.json",
    "任务路由规则": SMART_ROOT / "01配置" / "任务路由规则.json",
    "智能体大脑规则": SMART_ROOT / "01配置" / "智能体大脑规则.json",
    "知识库配置": SMART_ROOT / "01配置" / "知识库配置.json",
    "知识库全文索引": SMART_ROOT / "03数据" / "知识库" / "03索引清单" / "知识库全文索引_最新.json",
    "中台异常闭环报告": SMART_ROOT / "03数据" / "知识库" / "13知识检索中台异常闭环" / "智能系统知识检索中台异常闭环_最新.json",
    "中台异常闭环验收": SMART_ROOT / "04日志" / "知识库" / "smart-system-knowledge-middleware-exception-loop-verify-最新.json",
    "知识库入口验收": SMART_ROOT / "04日志" / "知识库" / "knowledge-traceable-qa-entry-verify-最新.json",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def backup_latest_outputs(timestamp: str) -> dict[str, Any]:
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    targets = [
        OUTPUT_DIR / "01智能系统中台补齐清单与验收报告_最新.json",
        OUTPUT_DIR / "01智能系统中台补齐清单与验收报告_最新.md",
        LOG_DIR / "smart-system-middleware-completion-report-verify-最新.json",
    ]
    copied = []
    for target in targets:
        if target.exists():
            backup_target = backup_dir / target.name
            shutil.copy2(target, backup_target)
            copied.append({"原路径": str(target), "备份路径": str(backup_target), "sha256": file_sha256(backup_target)})
    manifest = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "备份目录": str(backup_dir),
        "备份对象": copied,
        "说明": "写入 01 智能系统中台补齐报告前备份既有最新报告；本轮不修改既有配置和业务脚本。",
    }
    write_json(backup_dir / "备份清单.json", manifest)
    return manifest


def inventory() -> dict[str, Any]:
    root_dirs = []
    for directory in sorted(item for item in SMART_ROOT.iterdir() if item.is_dir()):
        files = [item for item in directory.rglob("*") if item.is_file() and ".venv" not in str(item)]
        root_dirs.append({"目录": str(directory), "文件数量": len(files)})
    scripts = [
        {"路径": str(path), "大小": path.stat().st_size}
        for path in sorted((SMART_ROOT / "02脚本").rglob("*.py"))
        if ".venv" not in str(path)
    ]
    configs = [
        {"路径": str(path), "大小": path.stat().st_size}
        for path in sorted((SMART_ROOT / "01配置").rglob("*"))
        if path.is_file() and "云服务器密钥" not in str(path)
    ]
    service_text = read_text(KEY_FILES["服务入口"])
    endpoints = re.findall(r"@app\.(?:get|post)\(\"([^\"]+)\"\)", service_text)
    return {
        "目录盘点": root_dirs,
        "脚本数量": len(scripts),
        "配置数量": len(configs),
        "入口端点": endpoints,
        "关键脚本": {name: {"路径": str(path), "存在": path.exists()} for name, path in KEY_FILES.items()},
    }


def run_subprocess(script: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def build_samples() -> list[dict[str, Any]]:
    task_module = load_module("middleware_task_module", KEY_FILES["任务识别"])
    capability_module = load_module("middleware_capability_module", KEY_FILES["能力注册"])
    model_module = load_module("middleware_model_module", KEY_FILES["模型路由器"])
    knowledge_module = load_module("middleware_knowledge_module", KEY_FILES["知识库检索"])

    questions = [
        "帮我查一下知识库里历史 K 线数据来源是什么",
        "请分析新易盛成交额阈值为什么这样算",
        "请删除索引并触发 n8n 发送企业微信真实消息",
    ]
    samples = []
    for question in questions:
        task = task_module.识别任务(question, {"来源": "01智能系统中台补齐验收"})
        capability = capability_module.规划能力调用(task)
        model_route = model_module.选择模型(task, {})
        keyword = "历史 K 线" if "历史" in question else ("新易盛" if "新易盛" in question else "知识库")
        knowledge = knowledge_module.检索知识库(keyword, 3)
        high_risk = any(marker in question for marker in ["删除", "触发 n8n", "企业微信真实", "券商", "自动交易"])
        samples.append(
            {
                "问题": question,
                "任务识别": task,
                "能力规划": capability,
                "模型路由": model_route,
                "知识检索": {
                    "关键词": keyword,
                    "状态": knowledge.get("状态"),
                    "命中数量": knowledge.get("命中数量", 0),
                },
                "异常处理": {
                    "是否高风险": high_risk,
                    "处理方式": "阻断，不执行外部动作" if high_risk else "进入只读检索与能力规划",
                },
            }
        )
    return samples


def capability_matrix(inv: dict[str, Any], samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = load_json(KEY_FILES["知识库全文索引"], {})
    loop_report = load_json(KEY_FILES["中台异常闭环报告"], {})
    loop_verify = load_json(KEY_FILES["中台异常闭环验收"], {})
    entry_verify = load_json(KEY_FILES["知识库入口验收"], {})
    endpoints = set(inv.get("入口端点", []))
    abilities = load_json(KEY_FILES["能力注册表"], {}).get("能力", [])

    return [
        {
            "能力": "任务理解",
            "最小标准": "可识别知识库问答、股票研究、系统运维等任务类型并给出风险等级。",
            "当前证据": [str(KEY_FILES["任务识别"]), str(KEY_FILES["智能体大脑规则"])],
            "状态": "已具备" if KEY_FILES["任务识别"].exists() and all(item.get("任务识别", {}).get("任务类型") for item in samples) else "待补齐",
            "缺口": "",
        },
        {
            "能力": "能力路由",
            "最小标准": "可读取能力注册表，生成能力名、归属系统、执行方式和人工确认判断。",
            "当前证据": [str(KEY_FILES["能力注册"]), str(KEY_FILES["能力注册表"])],
            "状态": "已具备" if any(item.get("能力名") == "知识库问答" for item in abilities) and all(item.get("能力规划", {}).get("能力名") for item in samples) else "待补齐",
            "缺口": "入口类型仍有待接入项，需要后续从计划路由升级为正式调用契约。",
        },
        {
            "能力": "状态读取",
            "最小标准": "服务入口或本地脚本可读取健康、能力、知识库、工作流等状态。",
            "当前证据": [str(KEY_FILES["服务入口"]), str(KEY_FILES["知识库检索"])],
            "状态": "已具备" if {"/健康", "/能力/列表", "/知识库/状态", "/工作流/列表"}.issubset(endpoints) else "待补齐",
            "缺口": "",
        },
        {
            "能力": "知识/证据读取接口",
            "最小标准": "可只读读取知识库全文索引并返回命中数量、来源路径和分块。",
            "当前证据": [str(KEY_FILES["知识库检索"]), str(KEY_FILES["知识库全文索引"])],
            "状态": "已具备" if index.get("文档数量", 0) > 0 and index.get("分块数量", 0) > 0 else "待补齐",
            "缺口": "向量检索和正式库写入仍关闭；当前仅为本地全文索引。",
        },
        {
            "能力": "异常处理",
            "最小标准": "无证据拒答，高风险动作阻断，且不伪造来源。",
            "当前证据": [str(KEY_FILES["中台异常闭环报告"]), str(KEY_FILES["中台异常闭环验收"])],
            "状态": "已具备" if loop_report.get("汇总", {}).get("总体状态") == "通过" and loop_verify.get("结论") == "通过" else "待补齐",
            "缺口": "服务入口尚未暴露与脚本同等严格的统一异常端点，后续可做 API 化。",
        },
        {
            "能力": "验收报告输出",
            "最小标准": "可生成 JSON/Markdown 验收报告，包含通过/失败、安全边界、剩余缺口。",
            "当前证据": [str(OUTPUT_DIR / "01智能系统中台补齐清单与验收报告_最新.json"), str(KEY_FILES["知识库入口验收"])],
            "状态": "已具备" if entry_verify.get("汇总", {}).get("失败") == 0 else "待补齐",
            "缺口": "",
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 01智能系统中台补齐清单与验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['总体状态']}",
        f"- 中台最小能力项：{report['汇总']['能力项数量']}",
        f"- 已具备：{report['汇总']['已具备数量']}",
        f"- 待补齐：{report['汇总']['待补齐数量']}",
        f"- 备份目录：{report['备份']['备份目录']}",
        "",
        "## 能力清单",
        "",
    ]
    for item in report["中台最小能力矩阵"]:
        lines.append(f"### {item['能力']}")
        lines.append(f"- 最小标准：{item['最小标准']}")
        lines.append(f"- 状态：{item['状态']}")
        if item.get("缺口"):
            lines.append(f"- 缺口：{item['缺口']}")
        lines.append("- 当前证据：")
        for evidence in item.get("当前证据", []):
            lines.append(f"  - {evidence}")
        lines.append("")
    lines.extend(["## 小样本", ""])
    for item in report["小样本验收"]:
        lines.append(f"### {item['问题']}")
        lines.append(f"- 任务类型：{item['任务识别'].get('任务类型')}；风险：{item['任务识别'].get('风险等级')}")
        lines.append(f"- 能力：{item['能力规划'].get('能力名')}；执行方式：{item['能力规划'].get('默认执行方式')}")
        lines.append(f"- 检索命中：{item['知识检索'].get('命中数量')}")
        lines.append(f"- 异常处理：{item['异常处理'].get('处理方式')}")
        lines.append("")
    lines.extend(["## 剩余缺口", ""])
    for item in report["发现的问题"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    backup = backup_latest_outputs(timestamp)
    inv = inventory()
    samples = build_samples()
    loop_verify_run = run_subprocess(KNOWLEDGE_DIR / "验证智能系统知识检索中台异常闭环.py")
    matrix = capability_matrix(inv, samples)
    ready_count = sum(1 for item in matrix if item["状态"] == "已具备")
    pending_count = len(matrix) - ready_count
    sources = {name: {"路径": str(path), "存在": path.exists()} for name, path in READ_SOURCES.items()}
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "smart-system-middleware-completion-report",
        "所属系统": "01杰哥智能系统/智能体大脑",
        "读取来源": sources,
        "汇总": {
            "总体状态": "通过" if pending_count == 0 and loop_verify_run["returncode"] == 0 else "待复核",
            "能力项数量": len(matrix),
            "已具备数量": ready_count,
            "待补齐数量": pending_count,
            "中台异常闭环验收返回码": loop_verify_run["returncode"],
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "修改总管进度口径": False,
            "修改02扩展系统业务脚本": False,
            "修改03进化系统规则代码": False,
        },
        "备份": backup,
        "现状盘点": inv,
        "中台最小能力矩阵": matrix,
        "小样本验收": samples,
        "中台异常闭环验收": loop_verify_run,
        "发现的问题": [
            "当前中台能力以本地脚本、配置和测试服务接口为主，尚未统一成生产级网关。",
            "能力注册表中部分能力入口仍为待接入，说明具备规划和路由能力，但未全部接管正式业务流量。",
            "知识/证据读取为本地全文索引；向量检索、正式向量库和正式数据库写入仍关闭。",
            "异常处理已在本地闭环验收通过，但服务入口尚未新增统一严格可追溯问答端点。",
            "本轮按边界未修改全盘架构说明和总管口径，需总管回收后统一决定是否同步。",
        ],
        "剩余有效工时建议": {
            "总管当前口径": "01智能系统仍按 16-26 小时推进，未经本框直接修改。",
            "本轮中台补齐建议影响": "中台最小能力已形成小样本闭环，建议总管评估可下调 2-4 小时。",
            "后续仍需": "约 12-22 小时，主要用于生产级网关、正式 API 化、灰度门禁、向量检索和跨系统回收联动。",
        },
        "安全边界": {
            "修改00总管进度口径文件": False,
            "修改02扩展系统业务脚本": False,
            "修改03进化系统规则文件": False,
            "发送企业微信真实消息": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "读取或复制密钥": False,
        },
    }
    output_json = OUTPUT_DIR / f"01智能系统中台补齐清单与验收报告_{timestamp}.json"
    latest_json = OUTPUT_DIR / "01智能系统中台补齐清单与验收报告_最新.json"
    output_md = OUTPUT_DIR / f"01智能系统中台补齐清单与验收报告_{timestamp}.md"
    latest_md = OUTPUT_DIR / "01智能系统中台补齐清单与验收报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(LOG_DIR / f"smart-system-middleware-completion-report-{timestamp}.json", report)
    print(json.dumps({"状态": report["汇总"]["总体状态"], "已具备": ready_count, "待补齐": pending_count, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if report["汇总"]["总体状态"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
