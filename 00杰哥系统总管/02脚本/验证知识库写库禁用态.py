"""
名称：验证知识库写库禁用态.py
作用：执行并验证知识库写库禁用态检查，确认正式知识库、Qdrant、PostgreSQL、旧系统读取、原文覆盖、n8n触发和资料外发均关闭。
触发方式：python 验证知识库写库禁用态.py
依赖：Python 标准库；执行知识库写库禁用态检查.py。
所属系统：00杰哥系统总管
安全边界：只执行禁用态检查；不写入正式知识库；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料。
创建/修改记录：2026-04-27 创建知识库写库禁用态验收脚本。
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
    script = root / "02脚本" / "知识库" / "执行知识库写库禁用态检查.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "知识库" / "06入库前复核" / "知识库写库禁用态检查_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("禁用态检查生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("禁用态检查报告存在", report_path.exists(), str(report_path)),
        check("执行器为禁用态", report.get("执行器状态") == "禁用态", report.get("执行器状态")),
        check("正式知识库写入关闭", report.get("是否写入正式知识库") is False, report.get("是否写入正式知识库")),
        check("Qdrant写入关闭", report.get("是否写入Qdrant") is False, report.get("是否写入Qdrant")),
        check("PostgreSQL写入关闭", report.get("是否写入PostgreSQL") is False, report.get("是否写入PostgreSQL")),
        check("旧系统读取关闭", report.get("是否读取旧系统资料") is False, report.get("是否读取旧系统资料")),
        check("原始文档覆盖关闭", report.get("是否覆盖原始文档") is False, report.get("是否覆盖原始文档")),
        check("n8n触发关闭", report.get("是否触发n8n") is False, report.get("是否触发n8n")),
        check("资料外发关闭", report.get("是否外发资料") is False, report.get("是否外发资料")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "knowledge-write-disabled-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "知识库入库前复核"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"knowledge-write-disabled-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "knowledge-write-disabled-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
