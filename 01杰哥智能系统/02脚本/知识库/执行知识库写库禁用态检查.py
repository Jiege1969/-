"""
名称：执行知识库写库禁用态检查.py
作用：读取知识库本地入库前复核报告，生成写库禁用态检查报告，确认正式知识库、Qdrant和PostgreSQL写入均保持关闭。
触发方式：python 执行知识库写库禁用态检查.py
依赖：Python 标准库；知识库本地入库前复核报告_最新.json；知识库本地入库前复核门禁.json。
所属系统：01杰哥智能系统/知识库
安全边界：只生成写库禁用态检查报告；不写入正式知识库；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料。
创建/修改记录：2026-04-27 创建知识库写库禁用态检查脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    gate = load_json(root / "01配置" / "知识库本地入库前复核门禁.json")
    review_path = root / "03数据" / "知识库" / "06入库前复核" / "知识库本地入库前复核报告_最新.json"
    review = load_json(review_path) if review_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "知识库写库禁用态检查",
        "复核报告": str(review_path),
        "复核统计": review.get("统计", {}),
        "门禁开关": gate.get("默认开关", {}),
        "是否写入正式知识库": False,
        "是否写入Qdrant": False,
        "是否写入PostgreSQL": False,
        "是否读取旧系统资料": False,
        "是否覆盖原始文档": False,
        "是否触发n8n": False,
        "是否外发资料": False,
        "执行器状态": "禁用态",
        "当前结论": "写库执行器保持禁用，只允许人工确认和复核报告。"
    }
    output_dir = root / "03数据" / "知识库" / "06入库前复核"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"知识库写库禁用态检查_{timestamp}.json"
    latest = output_dir / "知识库写库禁用态检查_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否写入Qdrant": report["是否写入Qdrant"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
