"""
名称：验证工作流底座.py
作用：验证 v3 工作流注册表、n8n 接口契约和 n8n 工作流草案生成脚本是否可用。
触发方式：python 验证工作流底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 工作流配置，只生成本地草案；不调用 n8n API，不创建 webhook，不触发外部动作。
创建/修改记录：2026-04-26 创建工作流底座验证脚本。
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
    target = v3_root() / "00杰哥系统总管" / "04日志" / "工作流验收"
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
    draft_dir = root / "01杰哥智能系统" / "03数据" / "工作流草案"
    script = root / "01杰哥智能系统" / "02脚本" / "工作流" / "生成n8n工作流草案.py"
    registry = load_json(config_dir / "工作流注册表.json")
    contract = load_json(config_dir / "n8n接口契约.json")

    run_result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    latest = draft_dir / "n8n工作流草案清单_最新.json"
    latest_data = load_json(latest) if latest.exists() else {}
    workflows = registry.get("工作流", [])
    drafts = latest_data.get("工作流草案", [])

    checks = [
        check("工作流注册表", len(workflows) >= 1 and "n8n" in registry, registry.get("说明")),
        check("n8n接口契约", "入口契约" in contract and "出口契约" in contract, contract.get("说明")),
        check("n8n接管状态", contract.get("n8n基础信息", {}).get("接管状态") == "未接管", contract.get("n8n基础信息", {})),
        check("自动触发关闭", contract.get("n8n基础信息", {}).get("是否允许自动触发") is False, contract.get("n8n基础信息", {})),
        check("草案脚本执行", run_result.returncode == 0, (run_result.stdout or "").strip() or (run_result.stderr or "").strip()),
        check("最新草案清单", latest.exists(), str(latest)),
        check("草案数量匹配", latest_data.get("工作流数量") == len(workflows), {"注册": len(workflows), "草案": latest_data.get("工作流数量")}),
        check("草案未调用n8n", latest_data.get("是否调用n8n") is False, latest_data.get("是否调用n8n")),
        check("草案自动触发关闭", all(item.get("是否允许自动触发") is False for item in drafts), len(drafts)),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "workflow-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"workflow-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "workflow-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
