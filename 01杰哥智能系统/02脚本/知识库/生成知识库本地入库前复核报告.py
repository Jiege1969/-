"""
名称：生成知识库本地入库前复核报告.py
作用：执行知识库人工确认队列生成，并根据本地入库前复核门禁生成复核报告。
触发方式：python 生成知识库本地入库前复核报告.py
依赖：Python 标准库；知识库本地入库前复核门禁.json；生成知识库人工确认队列.py。
所属系统：01杰哥智能系统/知识库
安全边界：只生成本地复核报告；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料。
创建/修改记录：2026-04-27 创建知识库本地入库前复核报告脚本。
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    script = root / "02脚本" / "知识库" / "生成知识库人工确认队列.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    gate = load_json(root / "01配置" / "知识库本地入库前复核门禁.json")
    queue_path = root / "03数据" / "知识库" / "03索引清单" / "知识库人工确认队列_最新.json"
    queue = load_json(queue_path) if queue_path.exists() else {}
    switches = gate.get("默认开关", {})
    stats = queue.get("统计", {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "知识库本地文档入库前复核",
        "队列脚本执行": {"退出码": result.returncode, "输出": result.stdout.strip() or result.stderr.strip()},
        "人工确认队列": str(queue_path),
        "统计": stats,
        "默认开关": switches,
        "复核要求": gate.get("复核要求", []),
        "结论": "只允许本地复核和人工确认，不允许自动进入正式知识库。",
        "下一步": [
            "补齐待确认资料的来源、保密等级和用途范围",
            "人工确认后再进入全文检索候选",
            "向量化前再次生成复核清单",
            "任何敏感或禁止入库资料直接阻断"
        ],
    }
    output_dir = root / "03数据" / "知识库" / "06入库前复核"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"知识库本地入库前复核报告_{timestamp}.json"
    latest = output_dir / "知识库本地入库前复核报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"队列数量": stats.get("队列数量"), "阻断数量": stats.get("阻断数量"), "输出": str(output)}, ensure_ascii=False))
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
