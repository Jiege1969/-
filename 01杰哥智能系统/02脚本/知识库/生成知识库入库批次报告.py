"""
名称：生成知识库入库批次报告.py
作用：检查 v3 知识库原始文档及其元数据伴随文件，生成批次入库质量报告。
触发方式：python 生成知识库入库批次报告.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 知识库原始文档和元数据伴随文件，只写入索引清单；不读取旧系统资料，不执行向量化。
创建/修改记录：2026-04-26 创建知识库批次入库质量报告脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config() -> dict[str, Any]:
    return load_json(config_dir() / "知识库配置.json")


def load_rules() -> dict[str, Any]:
    return load_json(config_dir() / "知识库入库规则.json")


def metadata_path_for(document: Path) -> Path:
    return document.with_name(f"{document.name}.元数据.json")


def evaluate_document(document: Path, required_fields: list[str], allowed_secret_levels: set[str]) -> dict[str, Any]:
    metadata_path = metadata_path_for(document)
    missing_fields: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, Any] = {}
    metadata_status = "缺失"

    if metadata_path.exists():
        try:
            metadata = load_json(metadata_path)
            metadata_status = "正常"
            missing_fields = [field for field in required_fields if not metadata.get(field)]
            secret_level = metadata.get("保密等级")
            if secret_level not in allowed_secret_levels:
                warnings.append("保密等级不在规则范围内")
            if secret_level == "敏感":
                warnings.append("敏感资料向量化前需人工确认")
            if secret_level == "禁止入库":
                warnings.append("禁止入库资料不得进入检索和向量化")
        except Exception as exc:
            metadata_status = "异常"
            warnings.append(f"元数据读取失败：{exc}")
    else:
        missing_fields = required_fields[:]
        warnings.append("缺少元数据伴随文件")

    can_vectorize = metadata_status == "正常" and not missing_fields and metadata.get("保密等级") not in {"敏感", "禁止入库"}
    return {
        "文件名": document.name,
        "路径": str(document),
        "元数据文件": str(metadata_path),
        "元数据状态": metadata_status,
        "缺失字段": missing_fields,
        "提醒": warnings,
        "文档类型": metadata.get("文档类型", "待分类"),
        "保密等级": metadata.get("保密等级", "待补充"),
        "入库批次": metadata.get("入库批次", "待补充"),
        "允许进入向量化候选": can_vectorize,
    }


def build_batch_report() -> dict[str, Any]:
    config = load_config()
    rules = load_rules()
    raw_dir = Path(config["数据目录"]["原始文档"])
    index_dir = Path(config["数据目录"]["索引清单"])
    index_dir.mkdir(parents=True, exist_ok=True)

    supported = {item.lower() for item in config.get("支持扩展名", [])}
    required_fields = list(rules.get("必填元数据", []))
    allowed_secret_levels = set(rules.get("保密等级", []))

    documents = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.endswith(".元数据.json"):
            continue
        if path.suffix.lower() not in supported:
            continue
        documents.append(evaluate_document(path, required_fields, allowed_secret_levels))

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "原始文档目录": str(raw_dir),
        "元数据规则": config.get("元数据伴随文件规则", {}),
        "文档数量": len(documents),
        "元数据正常数量": sum(1 for item in documents if item["元数据状态"] == "正常"),
        "缺失元数据数量": sum(1 for item in documents if item["元数据状态"] == "缺失"),
        "向量化候选数量": sum(1 for item in documents if item["允许进入向量化候选"]),
        "文档": documents,
        "说明": "本报告只做入库质量检查，不执行向量化、不迁移旧系统资料。",
    }
    output = index_dir / f"知识库入库批次报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = index_dir / "知识库入库批次报告_最新.json"
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"文档数量": len(documents), "向量化候选数量": report["向量化候选数量"], "输出": str(output)}, ensure_ascii=False))
    return report


def main() -> int:
    build_batch_report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
