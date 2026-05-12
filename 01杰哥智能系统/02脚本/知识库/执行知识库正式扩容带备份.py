# -*- coding: utf-8 -*-
"""
名称：执行知识库正式扩容带备份.py
作用：在先备份的前提下，把已确认候选资料复制进知识库原始文档批次目录，并重建全文索引。
触发方式：python 执行知识库正式扩容带备份.py
依赖：Python标准库；知识库正式扩容候选与备份方案_最新.json；生成知识库全文索引.py。
所属系统：01杰哥智能系统/知识库
安全边界：只复制候选资料到01智能系统知识库原始文档批次目录；先备份原始文档、清洗文本、索引清单、问答预演；不读取私密配置；不触发n8n；不发送企业微信；不写正式向量库；不调用模型；不修改股票脚本、总管进度标准文件或进化系统规则固化代码。
创建/修改记录：2026-05-05 创建知识库正式扩容带备份执行器。
标识：knowledge-formal-expansion-with-backup-execute
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
KB_ROOT = SMART_ROOT / "03数据" / "知识库"
RAW_DIR = KB_ROOT / "01原始文档"
CLEAN_DIR = KB_ROOT / "02清洗文本"
INDEX_DIR = KB_ROOT / "03索引清单"
QA_DIR = KB_ROOT / "06问答预演"
PLAN_PATH = KB_ROOT / "10正式扩容候选" / "知识库正式扩容候选与备份方案_最新.json"
OUTPUT_DIR = KB_ROOT / "11正式扩容执行"
BACKUP_ROOT = SMART_ROOT / "05备份" / "知识库正式扩容"


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(text: str) -> str:
    text = re.sub(r'[<>:"/\\|?*\s]+', "_", text.strip())
    return text[:120] or "unnamed"


def backup_dir(source: Path, target_root: Path) -> dict[str, Any]:
    target = target_root / source.name
    if source.exists():
        shutil.copytree(source, target)
        file_count = sum(1 for item in target.rglob("*") if item.is_file())
        byte_count = sum(item.stat().st_size for item in target.rglob("*") if item.is_file())
        return {"源目录": str(source), "备份目录": str(target), "文件数量": file_count, "字节数": byte_count, "状态": "已备份"}
    target.mkdir(parents=True, exist_ok=True)
    return {"源目录": str(source), "备份目录": str(target), "文件数量": 0, "字节数": 0, "状态": "源目录不存在，已建空备份占位"}


def run_index_generator() -> dict[str, Any]:
    script = SMART_ROOT / "02脚本" / "知识库" / "生成知识库全文索引.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    return {"脚本": str(script), "返回码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def find_existing_expansion_copy(source_sha: str, source_name: str) -> Path | None:
    if not RAW_DIR.exists():
        return None
    safe_source_name = safe_name(source_name)
    for path in sorted(RAW_DIR.rglob("*")):
        if not path.is_file():
            continue
        if "正式扩容批次_" not in str(path.parent):
            continue
        if safe_source_name not in path.name:
            continue
        try:
            if sha256_file(path) == source_sha:
                return path
        except OSError:
            continue
    return None


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库正式扩容带备份执行报告",
        "",
        f"- 执行时间：{report['执行时间']}",
        f"- 状态：{report['汇总']['状态']}",
        f"- 复制候选：{report['汇总']['复制候选数量']}",
        f"- 重建后文档数：{report['汇总']['重建后文档数量']}",
        f"- 重建后分块数：{report['汇总']['重建后分块数量']}",
        "",
        "## 备份",
        "",
    ]
    for item in report["备份记录"]:
        lines.append(f"- {item['状态']}：{item['源目录']} -> {item['备份目录']}；文件 {item['文件数量']}；字节 {item['字节数']}")
    lines.extend(["", "## 复制记录", ""])
    for item in report["复制记录"]:
        lines.append(f"- {item['状态']}：{item['源文件']} -> {item['目标文件']}")
    lines.extend(["", "## 回滚方式", ""])
    lines.append(report["回滚方式"])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    plan = load_json(PLAN_PATH, {})
    candidates = [item for item in plan.get("候选文件", []) if item.get("存在") is True]
    if not candidates:
        print(json.dumps({"状态": "failed", "原因": "没有可执行候选文件", "方案": str(PLAN_PATH)}, ensure_ascii=False))
        return 1

    backup_root = BACKUP_ROOT / timestamp
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_records = [backup_dir(path, backup_root) for path in [RAW_DIR, CLEAN_DIR, INDEX_DIR, QA_DIR]]

    batch_dir = RAW_DIR / f"正式扩容批次_{timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    copy_records: list[dict[str, Any]] = []
    for index, item in enumerate(candidates, start=1):
        source = Path(item["路径"])
        current_source_sha = sha256_file(source)
        existing = find_existing_expansion_copy(current_source_sha, source.name)
        category = safe_name(str(item.get("分类", "未分类")))
        priority = safe_name(str(item.get("优先级", "P")))
        target_name = f"{index:02d}_{priority}_{category}_{safe_name(source.name)}"
        target = existing or (batch_dir / target_name)
        if existing is None:
            shutil.copy2(source, target)
        target_sha = sha256_file(target)
        copy_records.append(
            {
                "源文件": str(source),
                "目标文件": str(target),
                "方案sha256": item.get("sha256", ""),
                "源sha256": current_source_sha,
                "目标sha256": target_sha,
                "状态": "已存在" if existing is not None and target_sha == current_source_sha else ("已复制" if target_sha == current_source_sha else "sha256不一致"),
            }
        )

    index_run = run_index_generator()
    latest_index_path = INDEX_DIR / "知识库全文索引_最新.json"
    latest_index = load_json(latest_index_path, {})
    copied_ok = all(item["状态"] in {"已复制", "已存在"} for item in copy_records)
    index_ok = index_run["返回码"] == 0 and latest_index.get("文档数量", 0) >= len(candidates)
    status = "pass" if copied_ok and index_ok else "attention_required"
    report = {
        "执行时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-formal-expansion-with-backup-execution",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "状态": status,
            "复制候选数量": len(copy_records),
            "复制成功数量": sum(1 for item in copy_records if item["状态"] in {"已复制", "已存在"}),
            "重建后文档数量": latest_index.get("文档数量", 0),
            "重建后分块数量": latest_index.get("分块数量", 0),
            "是否已备份": True,
            "是否重建全文索引": index_run["返回码"] == 0,
            "是否写正式向量库": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
        "方案文件": str(PLAN_PATH),
        "备份根目录": str(backup_root),
        "扩容批次目录": str(batch_dir),
        "备份记录": backup_records,
        "复制记录": copy_records,
        "索引重建": index_run,
        "最新索引文件": str(latest_index_path),
        "回滚方式": f"如需回滚，将当前 {KB_ROOT} 中 01原始文档、02清洗文本、03索引清单、06问答预演 替换为备份目录 {backup_root} 下对应目录；或仅删除扩容批次目录 {batch_dir} 后重新运行全文索引生成脚本。",
        "安全边界": {
            "修改股票研究系统脚本": False,
            "修改总管进度标准文件": False,
            "修改进化系统规则固化代码": False,
            "读取私密配置": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "触发n8n": False,
            "企业微信真实发送": False,
        },
    }
    output_json = OUTPUT_DIR / f"知识库正式扩容带备份执行报告_{timestamp}.json"
    latest_json = OUTPUT_DIR / "知识库正式扩容带备份执行报告_最新.json"
    output_md = OUTPUT_DIR / f"知识库正式扩容带备份执行报告_{timestamp}.md"
    latest_md = OUTPUT_DIR / "知识库正式扩容带备份执行报告_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "复制候选数量": len(copy_records), "文档数量": latest_index.get("文档数量", 0), "分块数量": latest_index.get("分块数量", 0), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
