# -*- coding: utf-8 -*-
"""
名称：验证首批执行器n8n禁用工作流草案.py
作用：生成并验证首批执行器n8n禁用工作流草案，确认inactive、节点禁用且不包含命令执行或webhook节点。
触发方式：python 验证首批执行器n8n禁用工作流草案.py
依赖：Python 标准库；生成首批执行器n8n禁用工作流草案.py。
所属系统：01杰哥智能系统/工作流
安全边界：只生成和验证inactive工作流草案；不导入n8n；不触发n8n；不创建系统计划任务；不联网；不写库；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批执行器n8n禁用工作流草案验证脚本。
标识：first-batch-n8n-disabled-workflow-draft-verify
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


def workflow_safe(path: Path) -> bool:
    workflow = load_json(path)
    text = json.dumps(workflow, ensure_ascii=False).lower()
    nodes = workflow.get("nodes", [])
    return (
        workflow.get("active") is False
        and all(node.get("disabled") is True for node in nodes)
        and "executecommand" not in text
        and "webhook" not in text
        and "credential" not in text
        and "税收业务系统" not in text
    )


def main() -> int:
    root = module_root()
    v3 = system_root()
    script = root / "02脚本" / "工作流" / "生成首批执行器n8n禁用工作流草案.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    summary_path = root / "03数据" / "工作流草案" / "首批执行器禁用工作流" / "首批执行器n8n禁用工作流草案汇总_最新.json"
    summary = load_json(summary_path) if summary_path.exists() else {}
    workflow_files = [Path(item.get("工作流文件", "")) for item in summary.get("工作流草案", [])]
    checks = [
        check("禁用工作流草案生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("汇总文件存在", summary_path.exists(), str(summary_path)),
        check("草案数量为三个", summary.get("汇总", {}).get("草案数量") == 3, summary.get("汇总", {})),
        check("激活数量为零", summary.get("汇总", {}).get("激活数量") == 0, summary.get("汇总", {})),
        check("所有草案文件存在", all(path.exists() for path in workflow_files), [str(path) for path in workflow_files]),
        check("所有草案安全禁用", all(workflow_safe(path) for path in workflow_files if path.exists()), [str(path) for path in workflow_files]),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "first-batch-n8n-disabled-workflow-draft-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "工作流"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output = output_dir / f"first-batch-n8n-disabled-workflow-draft-verify-{timestamp}.json"
    latest = output_dir / "first-batch-n8n-disabled-workflow-draft-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    manager_output_dir = v3 / "00杰哥系统总管" / "04日志" / "工作流验收"
    manager_output_dir.mkdir(parents=True, exist_ok=True)
    manager_output = manager_output_dir / f"first-batch-n8n-disabled-workflow-draft-verify-{timestamp}.json"
    manager_latest = manager_output_dir / "first-batch-n8n-disabled-workflow-draft-verify-最新.json"
    write_json(manager_output, verify)
    write_json(manager_latest, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
