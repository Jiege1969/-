# -*- coding: utf-8 -*-
"""
名称：生成知识库正式扩容候选与备份方案.py
作用：为知识库从测试文档扩容到可交付资料库生成候选清单、备份范围、验收门槛和阻塞项。
触发方式：python 生成知识库正式扩容候选与备份方案.py
依赖：Python标准库；既有系统文档。
所属系统：01杰哥智能系统/知识库
安全边界：只读扫描候选资料并写入扩容候选方案；不复制、不覆盖、不移动正式知识库文件；不重建索引；不写正式向量库；不触发n8n；不发送企业微信。
创建/修改记录：2026-05-05 创建知识库正式扩容候选与备份方案。
标识：knowledge-formal-expansion-candidate-plan-generate
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
OUTPUT_DIR = SMART_ROOT / "03数据" / "知识库" / "10正式扩容候选"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def candidate(path: str, category: str, reason: str, priority: str) -> dict[str, Any]:
    file_path = Path(path)
    exists = file_path.exists()
    return {
        "路径": str(file_path),
        "存在": exists,
        "文件名": file_path.name,
        "分类": category,
        "入库理由": reason,
        "优先级": priority,
        "大小字节": file_path.stat().st_size if exists else 0,
        "sha256": sha256_file(file_path) if exists and file_path.is_file() else "",
        "建议动作": "先复制到知识库原始文档候选区并生成元数据，再重建索引预演；不直接覆盖现有正式知识库。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库正式扩容候选与备份方案",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 候选文件：{report['汇总']['候选数量']}",
        f"- 存在文件：{report['汇总']['存在数量']}",
        f"- 状态：{report['汇总']['状态']}",
        "",
        "## 候选清单",
        "",
    ]
    for item in report["候选文件"]:
        state = "存在" if item["存在"] else "缺失"
        lines.append(f"- {state}：{item['文件名']}；分类：{item['分类']}；优先级：{item['优先级']}")
        lines.append(f"  - 路径：{item['路径']}")
        lines.append(f"  - 理由：{item['入库理由']}")
    lines.extend(["", "## 备份和验收门槛", ""])
    for item in report["备份与验收门槛"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 阻塞项", ""])
    for item in report["阻塞项"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    candidates = [
        candidate(
            "D:/杰哥智能化系统/杰哥智能化系统全盘架构说明_20260504.md",
            "系统架构",
            "全盘架构、四大系统边界、强制同步规则和当前实施进度，是系统问答的核心来源。",
            "P0",
        ),
        candidate(
            "D:/杰哥智能化系统/00杰哥系统总管/03数据/开工上下文/一键接续施工包_最新.md",
            "接续上下文",
            "包含当前主线、关键进度、关闭项、下一步任务，是回答施工状态和边界的直接依据。",
            "P0",
        ),
        candidate(
            "D:/杰哥智能化系统/01杰哥智能系统/07文档/设计纲领/智能系统设计纲领与施工计划v3.1.md",
            "智能系统设计",
            "定义01智能系统自身设计、计划和边界，适合作为知识库助手回答智能系统问题的来源。",
            "P0",
        ),
        candidate(
            "D:/杰哥智能化系统/01杰哥智能系统/07文档/知识库设计.md",
            "知识库设计",
            "定义知识库结构和目标，是回答知识库能力、入库流程、限制的来源。",
            "P0",
        ),
        candidate(
            "D:/杰哥智能化系统/01杰哥智能系统/07文档/知识库入库规范.md",
            "知识库规范",
            "定义入库规范、元数据和保密边界，是可追溯问答验收的制度来源。",
            "P1",
        ),
        candidate(
            "D:/杰哥智能化系统/02杰哥扩展系统/06企业微信助手系统/07文档/企业微信机器人终端分工与输入输出机制.md",
            "多助手路由",
            "定义企业微信终端分工和输入输出机制，是多助手路由问答的来源。",
            "P1",
        ),
        candidate(
            "D:/杰哥智能化系统/02杰哥扩展系统/06企业微信助手系统/01配置/企业微信机器人终端分工总表.json",
            "多助手路由",
            "机器可读终端分工总表，可用于追溯助手职责和启用状态。",
            "P1",
        ),
    ]
    existing = [item for item in candidates if item["存在"]]
    missing = [item for item in candidates if not item["存在"]]
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-formal-expansion-candidate-plan",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": "ready_for_backup_and_shadow_index" if len(existing) >= 5 else "attention_required",
            "候选数量": len(candidates),
            "存在数量": len(existing),
            "缺失数量": len(missing),
            "是否复制文件": False,
            "是否覆盖正式知识库": False,
            "是否重建索引": False,
            "是否写正式向量库": False,
        },
        "候选文件": candidates,
        "备份与验收门槛": [
            "执行扩容前，先备份03数据/知识库/01原始文档、02清洗文本、03索引清单和06问答预演。",
            "候选文件先进入候选区或带批次号的原始文档副本，不直接覆盖同名正式知识库文件。",
            "扩容后先生成影子全文索引，对比旧索引文档数、分块数、sha256和安全边界。",
            "影子索引验收通过后，才允许把扩容结果提升为正式最新索引。",
            "任何敏感、密钥、私密配置文件不得进入全文索引；配置类文件只允许公开配置和职责表。",
            "向量生成和正式向量库写入继续单独门禁，不随全文索引扩容自动启用。",
        ],
        "阻塞项": [
            "当前仅生成候选与备份方案，尚未执行真实扩容。",
            "若纳入全盘架构说明，文件较大，需要分块验收和摘要去噪，避免问答命中旧过时规则。",
            "私密配置文件不得入库；企业微信私密配置只可引用路径，不可读取内容。",
        ],
        "安全边界": {
            "复制文件": False,
            "覆盖正式知识库": False,
            "重建索引": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "修改股票研究系统脚本": False,
            "修改总管进度标准文件": False,
            "修改进化系统规则固化代码": False,
        },
    }
    output_json = OUTPUT_DIR / f"知识库正式扩容候选与备份方案_{timestamp}.json"
    latest_json = OUTPUT_DIR / "知识库正式扩容候选与备份方案_最新.json"
    output_md = OUTPUT_DIR / f"知识库正式扩容候选与备份方案_{timestamp}.md"
    latest_md = OUTPUT_DIR / "知识库正式扩容候选与备份方案_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": report["汇总"]["状态"], "候选数量": len(candidates), "存在数量": len(existing), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if report["汇总"]["状态"] == "ready_for_backup_and_shadow_index" else 1


if __name__ == "__main__":
    raise SystemExit(main())
