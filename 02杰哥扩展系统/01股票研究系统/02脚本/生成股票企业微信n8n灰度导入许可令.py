# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信n8n灰度导入许可令.py
作用：生成股票企业微信n8n适配器工作流进入人工确认导入评审前的许可令。
触发方式：python 生成股票企业微信n8n灰度导入许可令.py
依赖：Python标准库；股票企业微信n8n灰度导入许可规则.json；n8n适配器工作流草案包；n8n适配器禁用态验收；n8n适配器工作流草案验收。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地许可令；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不调用OpenClaw；不真实发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信n8n灰度导入许可令生成脚本。
标识：stock-wework-n8n-import-permit-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check_item(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def build_markdown(report: dict[str, Any]) -> str:
    evidence = "\n".join(f"- {item['名称']}：{'通过' if item['通过'] else '未通过'}。{item['详情']}" for item in report["证据检查"])
    blocked = "\n".join(f"- {item}" for item in report["禁止动作"])
    confirm = "\n".join(f"- {item}" for item in report["人工确认后才允许的动作"])
    return f"""# 股票企业微信n8n灰度导入许可令

生成时间：{report['生成时间']}

结论：{report['结论']}

定位：本许可令只证明“可以提交人工确认导入评审”，不代表已经导入n8n。

## 一、证据检查

{evidence}

## 二、禁止动作

{blocked}

## 三、人工确认后才允许的动作

{confirm}

## 四、实际动作

- 调用n8n API：false
- 导入n8n：false
- 启用Webhook：false
- 触发n8n：false
- 真实发送企业微信：false
- 调用券商接口或自动交易：false
"""


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信n8n灰度导入许可规则.json"
    rules = load_json(rule_path, {})
    adapter_verify = load_json(root / "04日志" / "n8n适配器禁用态" / "stock-wework-n8n-adapter-dryrun-verify-最新.json", {})
    workflow_verify = load_json(root / "04日志" / "n8n适配器工作流草案" / "stock-wework-n8n-adapter-workflow-draft-verify-最新.json", {})
    workflow_package_path = root / "03数据" / "28n8n适配器工作流草案" / "股票企业微信n8n适配器工作流草案包_最新.json"
    workflow_package = load_json(workflow_package_path, {})
    workflow = workflow_package.get("工作流工件", {})
    nodes = workflow.get("nodes", [])
    safety = workflow_package.get("安全检查", {})
    checks = [
        check_item("许可规则存在", rules.get("模式") == "import_permit_only", str(rule_path)),
        check_item("n8n适配器禁用态验收通过", adapter_verify.get("失败") == 0, adapter_verify.get("结论", "")),
        check_item("n8n适配器工作流草案验收通过", workflow_verify.get("失败") == 0, workflow_verify.get("结论", "")),
        check_item("工作流草案active=false", workflow.get("active") is False, workflow.get("active")),
        check_item("工作流草案不包含凭据", not any("credentials" in node for node in nodes), "credentials"),
        check_item("未调用n8n API或导入", safety.get("是否调用n8nAPI") is False and safety.get("是否执行导入") is False, safety),
        check_item("真实发送与交易关闭", safety.get("是否发送企业微信") is False and safety.get("是否调用券商接口") is False and safety.get("是否自动交易") is False, safety),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "import_permit_only",
        "通过": passed,
        "失败": failed,
        "证据检查": checks,
        "结论": "具备提交人工确认导入评审的条件，但尚未导入n8n。" if failed == 0 else "暂不具备提交人工确认导入评审的条件。",
        "禁止动作": rules.get("禁止动作", []),
        "人工确认后才允许的动作": rules.get("人工确认后才允许的动作", []),
        "实际动作": {
            "调用n8nAPI": False,
            "导入n8n": False,
            "启用Webhook": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "29n8n灰度导入许可"
    log_dir = root / "04日志" / "n8n灰度导入许可"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "股票企业微信n8n灰度导入许可令_最新.json"
    latest_json = output_dir / "股票企业微信n8n灰度导入许可令_最新.json"
    md_path = output_dir / "股票企业微信n8n灰度导入许可令_最新.md"
    latest_md = output_dir / "股票企业微信n8n灰度导入许可令_最新.md"
    log_path = log_dir / "stock-wework-n8n-import-permit-generate-最新.json"
    write_json(json_path, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
