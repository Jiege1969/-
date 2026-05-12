# -*- coding: utf-8 -*-
"""
名称：验证R02知识库本地入库预演器.py
作用：生成并验证R02知识库本地入库预演器联检报告，确认预演器就绪但冻结。
触发方式：python 验证R02知识库本地入库预演器.py
依赖：Python 标准库；执行R02知识库本地入库预演器.py。
所属系统：01杰哥智能系统/知识库
安全边界：只生成和验证local_ingest_dry_run报告；不写正式向量库；不联网；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建R02知识库本地入库预演器验证脚本。
标识：r02-knowledge-local-ingest-executor-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "知识库" / "执行R02知识库本地入库预演器.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "知识库" / "06入库前复核" / "R02知识库本地入库预演器联检_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks_data = report.get("联检结果", {})
    checks = [
        check("预演器联检生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("预演器联检文件存在", report_path.exists(), str(report_path)),
        check("执行器状态为就绪但冻结", report.get("执行器状态") == "就绪但冻结", report.get("执行器状态")),
        check("未写入正式向量库", report.get("是否写入正式向量库") is False, report.get("是否写入正式向量库")),
        check("未允许进入正式入库", report.get("是否允许进入正式入库") is False, report.get("是否允许进入正式入库")),
        check("正式向量库写入关闭", checks_data.get("正式向量库写入关闭") is True, checks_data),
        check("最终闸口未放行", checks_data.get("最终闸口未放行") is True, checks_data),
        check("R02窗口未开放", checks_data.get("R02窗口未开放") is True, checks_data),
        check("R02许可令未签发", checks_data.get("R02许可令未签发") is True, checks_data),
        check("旧系统写入关闭", checks_data.get("旧系统写入关闭") is True, checks_data),
        check("税收业务关闭", checks_data.get("税收业务关闭") is True, checks_data),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "r02-knowledge-local-ingest-executor-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "知识库"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "r02-knowledge-local-ingest-executor-verify-最新.json"
    latest = output
    write_json(latest, verify)
    manager_output_dir = system_root() / "00杰哥系统总管" / "04日志" / "知识库入库前复核"
    manager_output_dir.mkdir(parents=True, exist_ok=True)
    manager_output = manager_output_dir / "r02-knowledge-local-ingest-executor-verify-最新.json"
    manager_latest = manager_output
    write_json(manager_latest, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
