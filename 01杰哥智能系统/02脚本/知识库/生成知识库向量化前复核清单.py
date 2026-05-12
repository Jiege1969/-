"""
名称：生成知识库向量化前复核清单.py
作用：读取知识库全文索引和入库批次报告，生成 Qdrant 写入前的人工复核清单与向量点位草案。
触发方式：python 生成知识库向量化前复核清单.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只生成本地复核清单和 Qdrant 点位草案；不调用 embedding 模型，不连接 Qdrant，不写入向量数据库。
创建/修改记录：2026-04-26 创建知识库向量化前复核清单脚本。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_path() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置" / "知识库配置.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    return load_json(config_path())


def index_dir(config: dict[str, Any]) -> Path:
    return Path(config["数据目录"]["索引清单"])


def stable_point_id(document_id: str, chunk_index: int) -> str:
    raw = f"{document_id}:{chunk_index}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def document_review_map(batch_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in batch_report.get("文档", []):
        result[item.get("路径", "")] = item
    return result


def build_vector_review() -> dict[str, Any]:
    config = load_config()
    qdrant = config.get("Qdrant写入草案", {})
    fulltext = load_json(index_dir(config) / "知识库全文索引_最新.json")
    batch = load_json(index_dir(config) / "知识库入库批次报告_最新.json")
    review_by_path = document_review_map(batch)

    candidates = []
    blocked = []
    for chunk in fulltext.get("分块", []):
        doc_path = chunk.get("路径", "")
        review = review_by_path.get(doc_path, {})
        allowed = review.get("允许进入向量化候选") is True
        item = {
            "点位ID": stable_point_id(chunk.get("文档ID", ""), int(chunk.get("分块序号", 0))),
            "集合名": qdrant.get("集合名"),
            "文档ID": chunk.get("文档ID"),
            "分块序号": chunk.get("分块序号"),
            "文件名": chunk.get("文件名"),
            "路径": doc_path,
            "清洗文本路径": chunk.get("清洗文本路径"),
            "字符数": chunk.get("字符数"),
            "文档类型": review.get("文档类型", "待分类"),
            "保密等级": review.get("保密等级", "待补充"),
            "入库批次": review.get("入库批次", "待补充"),
            "允许进入向量化候选": allowed,
            "需要人工复核": True,
            "真实写入Qdrant": False,
        }
        if allowed:
            candidates.append(item)
        else:
            item["阻断原因"] = review.get("提醒") or review.get("缺失字段") or ["未通过入库批次检查"]
            blocked.append(item)

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "向量化前复核清单",
        "Qdrant写入草案": qdrant,
        "是否调用Embedding模型": False,
        "是否连接Qdrant": False,
        "是否写入Qdrant": False,
        "候选点位数量": len(candidates),
        "阻断点位数量": len(blocked),
        "候选点位": candidates,
        "阻断点位": blocked,
        "结论": "仅生成复核清单，真实写入必须人工确认。",
    }
    output = index_dir(config) / f"知识库向量化前复核清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = index_dir(config) / "知识库向量化前复核清单_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"候选点位数量": len(candidates), "阻断点位数量": len(blocked), "输出": str(output)}, ensure_ascii=False))
    return report


def main() -> int:
    build_vector_review()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
