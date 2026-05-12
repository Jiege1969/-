"""
名称：验证知识库本地入库前复核.py
作用：生成并验证知识库本地入库前复核报告，确认不会自动写入正式知识库、Qdrant、PostgreSQL或读取旧系统资料。
触发方式：python 验证知识库本地入库前复核.py
依赖：Python 标准库；生成知识库本地入库前复核报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证复核报告；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料。
创建/修改记录：2026-04-27 创建知识库本地入库前复核验收脚本。
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


def knowledge_root() -> Path:
    return v3_root() / "01杰哥智能系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = knowledge_root()
    script = root / "02脚本" / "知识库" / "生成知识库本地入库前复核报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "知识库" / "06入库前复核" / "知识库本地入库前复核报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("默认开关", {})
    checks = [
        check("复核报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("复核报告存在", report_path.exists(), str(report_path)),
        check("自动写入正式知识库关闭", switches.get("允许自动写入正式知识库") is False, switches.get("允许自动写入正式知识库")),
        check("自动写入Qdrant关闭", switches.get("允许自动写入Qdrant") is False, switches.get("允许自动写入Qdrant")),
        check("自动写入PostgreSQL关闭", switches.get("允许自动写入PostgreSQL") is False, switches.get("允许自动写入PostgreSQL")),
        check("读取旧系统资料关闭", switches.get("允许读取旧系统资料") is False, switches.get("允许读取旧系统资料")),
        check("覆盖原始文档关闭", switches.get("允许覆盖原始文档") is False, switches.get("允许覆盖原始文档")),
        check("外发资料关闭", switches.get("允许外发资料") is False, switches.get("允许外发资料")),
        check("n8n触发关闭", switches.get("允许触发n8n") is False, switches.get("允许触发n8n")),
        check("人工确认队列已生成", "人工确认队列" in report and Path(report.get("人工确认队列", "")).exists(), report.get("人工确认队列")),
        check("报告结论保持人工确认", "人工确认" in report.get("结论", ""), report.get("结论")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "knowledge-local-ingest-review-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "知识库入库前复核"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"knowledge-local-ingest-review-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "knowledge-local-ingest-review-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
