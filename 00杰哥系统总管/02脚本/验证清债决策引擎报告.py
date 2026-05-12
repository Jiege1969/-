# -*- coding: utf-8 -*-
"""
名称：验证清债决策引擎报告.py
作用：验证清债决策引擎规则、进化规则卡和最新决策报告是否形成闭环。
触发方式：python 验证清债决策引擎报告.py
依赖：Python 标准库；生成清债决策引擎报告.py。
所属系统：00杰哥系统总管
安全边界：只读验证并写验收日志；不删除文件；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建清债方法论能力化验收脚本。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
EVOLUTION = ROOT / "03杰哥进化系统"
REPORT_JSON = MANAGER / "03数据" / "运行状态" / "清债决策引擎报告_最新.json"
REPORT_MD = MANAGER / "03数据" / "运行状态" / "清债决策引擎报告_最新.md"
RULE_JSON = MANAGER / "01配置" / "清债决策引擎规则.json"
ANTI_REDEBT_RULE = MANAGER / "01配置" / "清债防复发管理规则.json"
PRE_RULE = MANAGER / "01配置" / "新模块开工前置规则.json"
EVOLUTION_RULE = EVOLUTION / "03数据" / "35清债方法论能力化" / "清债方法论能力化规则_最新.md"
LOG_DIR = MANAGER / "04日志" / "清债决策引擎"
VERIFY_JSON = LOG_DIR / "debt-decision-engine-verify-最新.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_generator() -> dict[str, Any]:
    script = MANAGER / "02脚本" / "生成清债决策引擎报告.py"
    completed = subprocess.run(
        ["python", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=90,
    )
    return {
        "返回码": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    run_result = run_generator()
    report = load_json(REPORT_JSON) if REPORT_JSON.exists() else {}
    anti_rule_text = ANTI_REDEBT_RULE.read_text(encoding="utf-8-sig") if ANTI_REDEBT_RULE.exists() else ""
    pre_rule_text = PRE_RULE.read_text(encoding="utf-8-sig") if PRE_RULE.exists() else ""
    evolution_text = EVOLUTION_RULE.read_text(encoding="utf-8-sig") if EVOLUTION_RULE.exists() else ""
    categories = {item.get("分类") for item in report.get("分类汇总", [])}
    allowed_categories = {"可收口旧流水", "审计资产单独核实", "需补锚点再收口", "需人工审阅规则后分类", "已确认为保留资产"}

    checks = [
        check("生成脚本返回码为0", run_result.get("返回码") == 0, run_result),
        check("机器判定规则存在", RULE_JSON.exists(), str(RULE_JSON)),
        check("最新JSON报告存在", REPORT_JSON.exists() and report.get("旧文件总数") is not None, str(REPORT_JSON)),
        check("最新Markdown报告存在", REPORT_MD.exists() and "清债决策引擎报告" in REPORT_MD.read_text(encoding="utf-8-sig"), str(REPORT_MD)),
        check(
            "分类口径有效且允许普通旧债归零",
            categories.issubset(allowed_categories) and ("审计资产单独核实" in categories or report.get("待清债旧文件总数", 0) == 0),
            {"当前分类": sorted(categories), "允许分类": sorted(allowed_categories)},
        ),
        check("防复发规则已引用决策引擎", "清债决策引擎报告_最新.md" in anti_rule_text and "生成清债决策引擎报告.py" in anti_rule_text, str(ANTI_REDEBT_RULE)),
        check("新模块前置规则已纳入PRE-007", "PRE-007" in pre_rule_text and "清债决策引擎预检" in pre_rule_text, str(PRE_RULE)),
        check("进化规则卡存在方法闭环", "扫描" in evolution_text and "复验" in evolution_text and "系统能力化要求" in evolution_text, str(EVOLUTION_RULE)),
        check("安全边界未突破", all(report.get("安全边界", {}).get(key) is True for key in ["不触发n8n", "不发送企业微信", "不调用券商接口", "不自动交易", "不删除文件"]), report.get("安全边界", {})),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "清债决策引擎验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(failed) == 0,
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "报告摘要": {
            "旧文件总数": report.get("旧文件总数"),
            "旧文件总大小MB": report.get("旧文件总大小MB"),
            "扫描目录数": report.get("扫描目录数"),
        },
        "安全边界": {
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
            "未删除文件": True,
        },
    }
    write_json(VERIFY_JSON, result)
    print(json.dumps({"通过": result["通过"], "通过数量": result["通过数量"], "失败数量": result["失败数量"], "输出": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
