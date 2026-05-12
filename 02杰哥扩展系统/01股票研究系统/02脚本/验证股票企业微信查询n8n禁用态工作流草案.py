# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信查询n8n禁用态工作流草案.py
作用：验证股票企业微信查询n8n禁用态工作流草案已生成且未导入、未启用、未触发真实链路。
触发方式：python 验证股票企业微信查询n8n禁用态工作流草案.py
依赖：Python标准库；生成股票企业微信查询n8n禁用态工作流草案.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地草案验收；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信查询n8n禁用态工作流草案验收脚本。
标识：stock-wework-query-n8n-disabled-draft-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    v3_root = system_root()
    generator = root / "02脚本" / "生成股票企业微信查询n8n禁用态工作流草案.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    package_path = root / "03数据" / "20n8n禁用态工作流草案" / "股票企业微信查询_n8n禁用态工作流草案包_最新.json"
    workflow_path = root / "03数据" / "20n8n禁用态工作流草案" / "股票企业微信查询_n8n禁用态工作流草案_最新.json"
    manager_workflow_path = v3_root / "01杰哥智能系统" / "03数据" / "工作流导入工件" / "股票企业微信查询_n8n禁用态工作流草案_最新.json"
    package = load_json(package_path)
    workflow = load_json(workflow_path)
    manager_workflow = load_json(manager_workflow_path)
    nodes = workflow.get("nodes", [])
    checks: list[dict[str, Any]] = []
    add_check(checks, "草案生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "草案生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "工作流active为false", workflow.get("active") is False, workflow.get("active"))
    add_check(checks, "meta要求保持未激活", workflow.get("meta", {}).get("must_remain_inactive") is True, workflow.get("meta", {}))
    add_check(checks, "包含OpenClaw入口节点", any(node.get("name") == "OpenClaw消息入口禁用态" for node in nodes), [node.get("name") for node in nodes])
    add_check(checks, "包含本地股票助手草稿节点", any(node.get("name") == "请求本地股票助手草稿" for node in nodes), [node.get("name") for node in nodes])
    add_check(checks, "未包含凭据", not any("credentials" in node for node in nodes), "credentials")
    safety = package.get("安全检查", {})
    add_check(checks, "未调用n8n API", safety.get("是否调用n8nAPI") is False, safety)
    add_check(checks, "未执行导入", safety.get("是否执行导入") is False, safety)
    add_check(checks, "未启用Webhook", safety.get("是否启用Webhook") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("是否发送企业微信") is False, safety)
    add_check(checks, "交易能力关闭", safety.get("是否调用券商接口") is False and safety.get("是否自动交易") is False, safety)
    add_check(checks, "01系统工作流工件副本存在", manager_workflow_path.exists() and manager_workflow.get("active") is False, str(manager_workflow_path))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票企业微信查询n8n禁用态工作流草案已生成，真实链路未启用。" if failed == 0 else "股票企业微信查询n8n禁用态工作流草案存在失败项。",
    }
    output_dir = root / "04日志" / "n8n禁用态工作流草案"
    output = output_dir / f"stock-wework-query-n8n-disabled-draft-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-query-n8n-disabled-draft-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
