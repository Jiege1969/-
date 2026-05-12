"""
名称：生成知识库人工确认队列.py
作用：汇总知识库索引清单、入库批次报告和向量化前复核清单，生成人工确认队列、阻断清单和下一阶段候选清单。
触发方式：python 生成知识库人工确认队列.py
依赖：Python 标准库；需先生成知识库索引、批次报告和向量化前复核清单。
所属系统：01杰哥智能系统/知识库
安全边界：只读取知识库本地报告，只写入知识库索引清单目录；不写入Qdrant、不写入PostgreSQL、不读取旧系统资料。
创建/修改记录：2026-04-27 创建知识库人工确认队列脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_report(script_name: str, latest_path: Path) -> Path:
    if latest_path.exists():
        return latest_path
    script = Path(__file__).resolve().parent / script_name
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest_path


def as_doc_key(item: dict[str, Any]) -> str:
    return str(item.get("路径") or item.get("文档路径") or item.get("文件路径") or item.get("文件名") or item.get("文档标题") or "")


def build_manual_queue() -> dict[str, Any]:
    root = system_root()
    config = load_json(root / "01配置" / "知识库配置.json")
    rules = load_json(root / "01配置" / "知识库人工确认规则.json")
    index_dir = Path(config["数据目录"]["索引清单"])
    index_dir.mkdir(parents=True, exist_ok=True)

    index_path = ensure_report("生成知识库索引清单.py", index_dir / "知识库索引清单_最新.json")
    batch_path = ensure_report("生成知识库入库批次报告.py", index_dir / "知识库入库批次报告_最新.json")
    vector_path = ensure_report("生成知识库向量化前复核清单.py", index_dir / "知识库向量化前复核清单_最新.json")
    index_data = load_json(index_path)
    batch_data = load_json(batch_path)
    vector_data = load_json(vector_path)

    batch_by_key = {as_doc_key(item): item for item in batch_data.get("文档", [])}
    vector_candidates = {as_doc_key(item): item for item in vector_data.get("候选点位", [])}
    vector_blocked = {as_doc_key(item): item for item in vector_data.get("阻断点位", [])}

    queue = []
    blocked = []
    metadata_todo = []
    next_candidates = []
    for doc in index_data.get("文档", []):
        key = as_doc_key(doc)
        batch_item = batch_by_key.get(key, {})
        block_reasons: list[str] = []
        metadata_status = doc.get("元数据状态") or batch_item.get("元数据状态") or "待核实"
        secrecy = doc.get("保密等级") or batch_item.get("保密等级") or "待核实"
        parse_status = batch_item.get("解析状态") or doc.get("解析状态") or "待核实"

        if metadata_status in {"缺失", "异常", "待核实", ""}:
            block_reasons.append("元数据缺失或待核实")
            metadata_todo.append({"文档": key, "补充事项": rules.get("确认要求", [])})
        if secrecy in {"敏感", "禁止入库"}:
            block_reasons.append(f"保密等级需人工处理：{secrecy}")
        if parse_status not in {"已解析", "正常", "待核实"}:
            block_reasons.append(f"解析状态异常：{parse_status}")
        if key in vector_blocked:
            block_reasons.extend(vector_blocked[key].get("阻断原因", ["向量化前复核阻断"]))

        item = {
            "文档": key,
            "文档标题": doc.get("文档标题") or doc.get("文件名") or Path(key).name,
            "文档类型": doc.get("文档类型", "待核实"),
            "元数据状态": metadata_status,
            "保密等级": secrecy,
            "解析状态": parse_status,
            "确认状态": "待人工确认",
            "允许自动写入正式知识库": False,
            "允许自动写入Qdrant": False,
            "允许自动写入PostgreSQL": False,
            "阻断原因": block_reasons,
            "需人工确认事项": rules.get("确认要求", []),
        }
        queue.append(item)
        if block_reasons:
            blocked.append(item)
        elif key in vector_candidates:
            next_candidates.append({**item, "下一阶段": "向量化候选复核"})
        else:
            next_candidates.append({**item, "下一阶段": "全文检索候选复核"})

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则来源": str(root / "01配置" / "知识库人工确认规则.json"),
        "索引来源": str(index_path),
        "批次报告来源": str(batch_path),
        "向量化复核来源": str(vector_path),
        "人工确认队列": queue,
        "阻断清单": blocked,
        "元数据补充清单": metadata_todo,
        "下一阶段候选清单": next_candidates,
        "统计": {
            "队列数量": len(queue),
            "阻断数量": len(blocked),
            "元数据补充数量": len(metadata_todo),
            "下一阶段候选数量": len(next_candidates),
        },
        "是否写入Qdrant": False,
        "是否写入PostgreSQL": False,
        "是否读取旧系统资料": False,
        "安全说明": "本队列只用于人工确认，不自动改变知识库正式状态。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = index_dir / f"知识库人工确认队列_{timestamp}.json"
    latest = index_dir / "知识库人工确认队列_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"queue_count": len(queue), "blocked_count": len(blocked), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_manual_queue()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
