"""
名称：验证知识库底座.py
作用：验证 v3 知识库配置、入库规则、元数据模板、索引清单脚本、全文索引脚本、批次入库报告脚本、向量化前复核清单和人工确认队列是否可用。
触发方式：python 验证知识库底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 知识库配置，只运行本地索引脚本，不读取旧系统资料，不写入数据库。
创建/修改记录：2026-04-26 创建第一阶段知识库底座验证脚本；增加全文索引、批次入库报告和向量化前复核清单验证。2026-04-27 增加人工确认队列验收。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "知识库验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = v3_root()
    config_dir = root / "01杰哥智能系统" / "01配置"
    script = root / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库索引清单.py"
    fulltext_script = root / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库全文索引.py"
    batch_script = root / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库入库批次报告.py"
    vector_review_script = root / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库向量化前复核清单.py"
    manual_queue_script = root / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库人工确认队列.py"
    config = load_json(config_dir / "知识库配置.json")
    rules = load_json(config_dir / "知识库入库规则.json")
    manual_rules = load_json(config_dir / "知识库人工确认规则.json")
    metadata_template = load_json(config_dir / "知识库元数据模板.json")

    run_result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    fulltext_result = subprocess.run(
        [sys.executable, str(fulltext_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    batch_result = subprocess.run(
        [sys.executable, str(batch_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    vector_review_result = subprocess.run(
        [sys.executable, str(vector_review_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    manual_queue_result = subprocess.run(
        [sys.executable, str(manual_queue_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    index_latest = Path(config["数据目录"]["索引清单"]) / "知识库索引清单_最新.json"
    fulltext_latest = Path(config["数据目录"]["索引清单"]) / "知识库全文索引_最新.json"
    batch_latest = Path(config["数据目录"]["索引清单"]) / "知识库入库批次报告_最新.json"
    vector_review_latest = Path(config["数据目录"]["索引清单"]) / "知识库向量化前复核清单_最新.json"
    manual_queue_latest = Path(config["数据目录"]["索引清单"]) / "知识库人工确认队列_最新.json"
    latest_data = load_json(index_latest) if index_latest.exists() else {}
    fulltext_data = load_json(fulltext_latest) if fulltext_latest.exists() else {}
    batch_data = load_json(batch_latest) if batch_latest.exists() else {}
    vector_review_data = load_json(vector_review_latest) if vector_review_latest.exists() else {}
    manual_queue_data = load_json(manual_queue_latest) if manual_queue_latest.exists() else {}

    checks = [
        check("知识库配置", "数据目录" in config and "支持扩展名" in config, config.get("说明")),
        check("全文解析策略", "全文解析策略" in config and "直接解析扩展名" in config.get("全文解析策略", {}), config.get("全文解析策略")),
        check("元数据伴随规则", "元数据伴随文件规则" in config and "文件名格式" in config.get("元数据伴随文件规则", {}), config.get("元数据伴随文件规则")),
        check("Qdrant写入草案", "Qdrant写入草案" in config and config.get("Qdrant写入草案", {}).get("是否允许真实写入") is False, config.get("Qdrant写入草案")),
        check("入库规则", "允许来源" in rules and "禁止来源" in rules, rules.get("说明")),
        check("人工确认规则", "入库闸门" in manual_rules and "确认要求" in manual_rules, manual_rules.get("阶段")),
        check("元数据模板", "文档标题" in metadata_template and "保密等级" in metadata_template, metadata_template),
        check("索引脚本执行", run_result.returncode == 0, (run_result.stdout or "").strip() or (run_result.stderr or "").strip()),
        check("全文索引脚本执行", fulltext_result.returncode == 0, (fulltext_result.stdout or "").strip() or (fulltext_result.stderr or "").strip()),
        check("批次报告脚本执行", batch_result.returncode == 0, (batch_result.stdout or "").strip() or (batch_result.stderr or "").strip()),
        check("向量化前复核脚本执行", vector_review_result.returncode == 0, (vector_review_result.stdout or "").strip() or (vector_review_result.stderr or "").strip()),
        check("人工确认队列脚本执行", manual_queue_result.returncode == 0, (manual_queue_result.stdout or "").strip() or (manual_queue_result.stderr or "").strip()),
        check("最新索引清单", index_latest.exists(), str(index_latest)),
        check("索引清单结构", "文档数量" in latest_data and "文档" in latest_data, latest_data.get("文档数量")),
        check("最新全文索引", fulltext_latest.exists(), str(fulltext_latest)),
        check("全文索引结构", "分块数量" in fulltext_data and "分块" in fulltext_data, fulltext_data.get("分块数量")),
        check("最新批次报告", batch_latest.exists(), str(batch_latest)),
        check("批次报告结构", "向量化候选数量" in batch_data and "文档" in batch_data, batch_data.get("向量化候选数量")),
        check("最新向量化前复核清单", vector_review_latest.exists(), str(vector_review_latest)),
        check(
            "向量化前复核结构",
            "候选点位" in vector_review_data and vector_review_data.get("是否写入Qdrant") is False,
            {"候选": vector_review_data.get("候选点位数量"), "阻断": vector_review_data.get("阻断点位数量")},
        ),
        check("最新人工确认队列", manual_queue_latest.exists(), str(manual_queue_latest)),
        check(
            "人工确认队列结构",
            "人工确认队列" in manual_queue_data
            and "阻断清单" in manual_queue_data
            and manual_queue_data.get("是否写入Qdrant") is False
            and manual_queue_data.get("是否写入PostgreSQL") is False,
            manual_queue_data.get("统计"),
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "knowledge-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"knowledge-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir() / "knowledge-base-verify-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
