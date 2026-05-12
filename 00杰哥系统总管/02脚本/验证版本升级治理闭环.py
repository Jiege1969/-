# -*- coding: utf-8 -*-
"""
名称：验证版本升级治理闭环.py
作用：验证版本升级治理 V1.1 的只读判断、窗口判定、预案生成、回滚盘点与台账草案是否齐全。
触发方式：python 验证版本升级治理闭环.py
依赖：版本治理 V1.1 配置、维护脚本和最新日志。
所属系统：00杰哥系统总管/版本升级治理
输出：标准输出 JSON 验收结果。
安全边界：只读验证；不下载、不安装、不升级、不停止容器、不触发 n8n、不发送企业微信。
创建/修改记录：2026-05-03 创建；2026-05-03 补齐标准标头。
标识：upgrade-governance-loop-verify
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
CONFIG = MANAGER / "01配置"
SCRIPTS = MANAGER / "02脚本"
MAINT = SCRIPTS / "维护"
LOG = MANAGER / "04日志" / "版本升级治理"

RULES = CONFIG / "upgrade_rules.json"
LEDGER = CONFIG / "version_ledger.json"
V10_CHECK_SCRIPT = MAINT / "version_check.py"
V11_SCRIPTS = [
    MAINT / "upgrade_governance_common.py",
    MAINT / "auto_version_snapshot.py",
    MAINT / "upgrade_window_check.py",
    MAINT / "version_intel.py",
    MAINT / "generate_n8n_shadow_plan.py",
    MAINT / "rollback_capability_inventory.py",
    MAINT / "ledger_update_draft.py",
]
REPORTS = [
    LOG / "upgrade_check_latest.json",
    LOG / "version_snapshot_latest.json",
    LOG / "upgrade_window_latest.json",
    LOG / "version_intel_latest.json",
    LOG / "n8n_shadow_plan_latest.json",
    LOG / "rollback_capability_latest.json",
    LOG / "version_ledger_update_draft_latest.json",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def all_safety_false(report: dict[str, Any]) -> bool:
    boundary = report.get("安全边界", {})
    return isinstance(boundary, dict) and boundary and all(value is False for value in boundary.values())


def script_has_no_dangerous_exec(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8-sig")
    if path.name == "generate_n8n_shadow_plan.py":
        execution_tokens = ["subprocess.", "os.system", "run_command(", "Popen("]
        return not any(token in text for token in execution_tokens)
    blocked = [
        "docker stop ",
        "docker rm ",
        "docker run ",
        "docker compose up",
        "pip install",
        "npm install",
        "ollama pull",
        "ollama run",
        "requests.post",
        "urllib.request.urlopen(\"http://127.0.0.1:28679/webhook",
    ]
    return not any(token in text for token in blocked)


def main() -> int:
    rules = load(RULES)
    ledger = load(LEDGER)
    reports = {path.name: load(path) for path in REPORTS}
    n8n_plan = reports.get("n8n_shadow_plan_latest.json", {})
    ledger_draft = reports.get("version_ledger_update_draft_latest.json", {})
    window_report = reports.get("upgrade_window_latest.json", {})
    snapshot_report = reports.get("version_snapshot_latest.json", {})
    intel_report = reports.get("version_intel_latest.json", {})

    checks: list[dict[str, object]] = [
        {"名称": "升级规则存在", "通过": RULES.exists()},
        {"名称": "版本台账存在", "通过": LEDGER.exists()},
        {"名称": "规则版本为V1.1", "通过": rules.get("版本") == "V1.1"},
        {"名称": "V1.1边界齐全", "通过": all(key in rules.get("V1.1边界", {}) for key in ["只读采集", "窗口判断", "规则判定", "预案生成"])},
        {"名称": "风险细分齐全", "通过": all(key in rules.get("风险细分", {}) for key in ["security_patch", "minor_release", "major_release", "breaking_change", "model_replacement", "driver_update"])},
        {"名称": "不用latest铁律存在", "通过": "不用latest标签" in rules.get("升级铁律", [])},
        {"名称": "禁止跨层升级", "通过": rules.get("升级前置条件", {}).get("cross_layer_upgrade") is False},
        {"名称": "正式切换需人工确认", "通过": rules.get("升级前置条件", {}).get("require_manual_confirmation_for_formal_switch") is True},
        {"名称": "n8n影子不挂正式数据原则存在", "通过": any("不得挂正式n8n数据目录" in item for item in rules.get("n8n影子试验原则", []))},
        {"名称": "ChromaDB标记为规划组件", "通过": "ChromaDB" in rules.get("规划组件", {})},
        {"名称": "V1.0只读评估脚本保留", "通过": V10_CHECK_SCRIPT.exists()},
        {"名称": "V1.1脚本齐全", "通过": all(path.exists() for path in V11_SCRIPTS)},
        {"名称": "V1.1脚本不含直接执行升级动作", "通过": all(script_has_no_dangerous_exec(path) for path in V11_SCRIPTS)},
        {"名称": "V1.1报告齐全", "通过": all(path.exists() for path in REPORTS)},
        {"名称": "快照报告只读边界有效", "通过": all_safety_false(snapshot_report)},
        {"名称": "窗口判断报告存在判断结果", "通过": "判断" in window_report and window_report.get("结论", "").startswith("只判断窗口")},
        {"名称": "候选版本情报不发升级建议", "通过": "不下载、不升级、不给立即升级建议" in intel_report.get("结论", "")},
        {"名称": "n8n影子预案未执行", "通过": "未创建容器" in n8n_plan.get("结论", "") and "人工确认后才可执行的命令清单" in n8n_plan},
        {"名称": "回滚能力清单只盘点", "通过": "只盘点回滚能力" in reports.get("rollback_capability_latest.json", {}).get("结论", "")},
        {"名称": "台账更新草案不写正式台账", "通过": "不写正式version_ledger.json" in ledger_draft.get("结论", "")},
        {"名称": "台账记录n8n容器", "通过": any(item.get("名称") == "jiege_v3_n8n" for item in ledger.get("核心容器", []))},
        {"名称": "台账记录Ollama容器", "通过": any(item.get("名称") == "jiege_v3_ollama" for item in ledger.get("核心容器", []))},
        {"名称": "台账记录Redis容器", "通过": any(item.get("名称") == "jiege_v3_redis" for item in ledger.get("核心容器", []))},
        {"名称": "评估报告无自动升级权限", "通过": all_safety_false(reports.get("upgrade_check_latest.json", {}))},
        {"名称": "评估报告无铁律违反项", "通过": reports.get("upgrade_check_latest.json", {}).get("违反铁律数量", 1) == 0},
    ]
    ok = all(item["通过"] for item in checks)
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：版本升级治理V1.1判断闭环成立" if ok else "未通过：版本升级治理V1.1存在缺口",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
