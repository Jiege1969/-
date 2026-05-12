"""
名称：验证n8n导入前审查.py
作用：验证 v3 n8n 导入前审查规则、审查包生成、非税收候选包、演练清单、回滚方案和禁止真实导入状态是否可用。
触发方式：python 验证n8n导入前审查.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只生成本地审查包，不调用 n8n API，不导入工作流，不启用 webhook。
创建/修改记录：2026-04-26 创建 n8n 导入前审查验证脚本；2026-04-27 增加非税收导入候选包和演练清单验收。
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
    target = v3_root() / "00杰哥系统总管" / "04日志" / "n8n导入审查验收"
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
    review_dir = root / "01杰哥智能系统" / "03数据" / "工作流导入审查"
    rules = load_json(config_dir / "n8n导入前审查规则.json")
    non_tax_rules = load_json(config_dir / "n8n非税收导入候选规则.json")
    script = root / "01杰哥智能系统" / "02脚本" / "工作流" / "生成n8n导入前审查包.py"
    non_tax_script = root / "01杰哥智能系统" / "02脚本" / "工作流" / "生成n8n非税收导入候选包.py"
    rehearsal_script = root / "01杰哥智能系统" / "02脚本" / "工作流" / "生成n8n非税收导入演练清单.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    non_tax_result = subprocess.run(
        [sys.executable, str(non_tax_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    rehearsal_result = subprocess.run(
        [sys.executable, str(rehearsal_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest = review_dir / "n8n导入前审查包_最新.json"
    non_tax_latest = review_dir / "n8n非税收导入候选包_最新.json"
    rehearsal_latest = review_dir / "n8n非税收导入演练清单_最新.json"
    package = load_json(latest) if latest.exists() else {}
    non_tax_package = load_json(non_tax_latest) if non_tax_latest.exists() else {}
    rehearsal_package = load_json(rehearsal_latest) if rehearsal_latest.exists() else {}
    checks = [
        check("审查规则", "导入前必须满足" in rules and "回滚方案模板" in rules, rules.get("说明")),
        check("非税收候选规则", "明确排除" in non_tax_rules and "税收业务处理辅助" in non_tax_rules.get("明确排除", []), non_tax_rules.get("阶段")),
        check("禁止导入条件", len(rules.get("禁止导入条件", [])) >= 1, rules.get("禁止导入条件", [])),
        check("脚本执行", result.returncode == 0, (result.stdout or "").strip() or (result.stderr or "").strip()),
        check("非税收候选脚本执行", non_tax_result.returncode == 0, (non_tax_result.stdout or "").strip() or (non_tax_result.stderr or "").strip()),
        check("非税收演练清单脚本执行", rehearsal_result.returncode == 0, (rehearsal_result.stdout or "").strip() or (rehearsal_result.stderr or "").strip()),
        check("审查包存在", latest.exists(), str(latest)),
        check("非税收候选包存在", non_tax_latest.exists(), str(non_tax_latest)),
        check("非税收演练清单存在", rehearsal_latest.exists(), str(rehearsal_latest)),
        check("审查包不调用n8n", package.get("是否调用n8n") is False and package.get("是否导入n8n") is False, package.get("状态")),
        check("Webhook不启用", package.get("是否启用Webhook") is False, package.get("是否启用Webhook")),
        check(
            "非税收候选包边界",
            non_tax_package.get("是否导入n8n") is False
            and non_tax_package.get("是否启用Webhook") is False
            and non_tax_package.get("是否触发真实工作流") is False
            and non_tax_package.get("是否包含税收业务") is False,
            non_tax_package.get("统计"),
        ),
        check(
            "非税收演练清单边界",
            rehearsal_package.get("是否执行导入") is False
            and rehearsal_package.get("是否启用Webhook") is False
            and rehearsal_package.get("是否触发真实工作流") is False
            and rehearsal_package.get("是否包含税收业务") is False,
            rehearsal_package.get("统计"),
        ),
        check("回滚方案存在", "导入前备份" in package.get("回滚方案", {}) and "失败回滚" in package.get("回滚方案", {}), package.get("回滚方案", {})),
        check("工作流评估存在", len(package.get("工作流评估", [])) >= 1, len(package.get("工作流评估", []))),
        check("非税收候选存在", len(non_tax_package.get("候选工作流", [])) >= 1, non_tax_package.get("候选工作流", [])),
        check(
            "演练清单候选数匹配",
            len(rehearsal_package.get("审查清单", [])) == len(non_tax_package.get("候选工作流", []))
            and len(rehearsal_package.get("审查清单", [])) >= 1,
            rehearsal_package.get("统计"),
        ),
        check(
            "演练清单全部待人工审查",
            all(item.get("审查状态") == "待人工审查" for item in rehearsal_package.get("审查清单", [])),
            rehearsal_package.get("审查清单", []),
        ),
        check("第一批候选存在", len(package.get("第一批候选", [])) >= 1, package.get("第一批候选", [])),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "n8n-import-review-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"n8n-import-review-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "n8n-import-review-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
