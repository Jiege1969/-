"""
名称：验证进化系统底座.py
作用：验证 03杰哥进化系统的理念配置、经验分类、方法迁移、治理检查清单、样本生命周期、首批真实经验卡片、复盘报告和通用方法库是否可用。
触发方式：python 验证进化系统底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取进化系统配置并运行本地生成脚本；不修改其他系统配置，不自动固化规则。
创建/修改记录：2026-04-26 创建进化系统底座验证脚本；增加首批真实经验卡片、样本价值评估和通用方法库验收。
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


def evolution_root() -> Path:
    return v3_root() / "03杰哥进化系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "进化系统验收"
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
    root = evolution_root()
    config_dir = root / "01配置"
    script_dir = root / "02脚本"
    idea = load_json(config_dir / "系统理念配置.json")
    experience_rules = load_json(config_dir / "经验分类规则.json")
    migration_rules = load_json(config_dir / "方法迁移规则.json")
    governance = load_json(config_dir / "治理检查清单.json")
    lifecycle = load_json(config_dir / "样本生命周期规则.json")
    score_rules = load_json(config_dir / "经验价值评分规则.json")

    card_script = script_dir / "生成经验卡片.py"
    real_cards_script = script_dir / "生成首批真实经验卡片.py"
    report_script = script_dir / "生成进化复盘报告.py"
    value_report_script = script_dir / "生成样本价值评估报告.py"
    method_library_script = script_dir / "提炼通用方法库.py"
    card_result = subprocess.run(
        [sys.executable, str(card_script), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    real_cards_result = subprocess.run(
        [sys.executable, str(real_cards_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    report_result = subprocess.run(
        [sys.executable, str(report_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    value_report_result = subprocess.run(
        [sys.executable, str(value_report_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    method_library_result = subprocess.run(
        [sys.executable, str(method_library_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    latest_card = root / "03数据" / "01问题卡片" / "经验卡片_最新.json"
    latest_real_cards = root / "03数据" / "01问题卡片" / "首批真实经验卡片_最新.json"
    latest_report = root / "03数据" / "04通用方法" / "进化复盘报告_最新.json"
    latest_suggestion = root / "03数据" / "05进化建议" / "进化建议_最新.json"
    latest_value_report = root / "03数据" / "05进化建议" / "样本价值评估报告_最新.json"
    latest_method_library = root / "03数据" / "04通用方法" / "通用方法库_最新.json"
    card = load_json(latest_card) if latest_card.exists() else {}
    real_cards = load_json(latest_real_cards) if latest_real_cards.exists() else {}
    report = load_json(latest_report) if latest_report.exists() else {}
    suggestion = load_json(latest_suggestion) if latest_suggestion.exists() else {}
    value_report = load_json(latest_value_report) if latest_value_report.exists() else {}
    method_library = load_json(latest_method_library) if latest_method_library.exists() else {}

    checks = [
        check("系统理念配置", "四大系统分工" in idea and "治理原则" in idea, idea.get("说明")),
        check("通用认知循环", len(idea.get("通用认知循环", [])) >= 6, idea.get("通用认知循环", [])),
        check("经验分类规则", len(experience_rules.get("经验类型", [])) == 3, experience_rules.get("经验类型", [])),
        check("方法迁移规则", "迁移原则" in migration_rules and "可迁移方法" in migration_rules, migration_rules.get("说明")),
        check(
            "治理检查清单",
            "施工前检查" in governance and ("必须人工确认" in governance or "高风险硬阻断" in governance),
            governance.get("说明"),
        ),
        check("样本生命周期规则", "清理前置条件" in lifecycle and "样本状态" in lifecycle, lifecycle.get("核心原则")),
        check("经验价值评分规则", "评分项" in score_rules and "等级" in score_rules, score_rules.get("说明")),
        check("经验卡片脚本执行", card_result.returncode == 0, (card_result.stdout or "").strip() or (card_result.stderr or "").strip()),
        check("首批真实经验卡片脚本执行", real_cards_result.returncode == 0, (real_cards_result.stdout or "").strip() or (real_cards_result.stderr or "").strip()),
        check("进化复盘脚本执行", report_result.returncode == 0, (report_result.stdout or "").strip() or (report_result.stderr or "").strip()),
        check("样本价值评估脚本执行", value_report_result.returncode == 0, (value_report_result.stdout or "").strip() or (value_report_result.stderr or "").strip()),
        check("通用方法库脚本执行", method_library_result.returncode == 0, (method_library_result.stdout or "").strip() or (method_library_result.stderr or "").strip()),
        check("最新经验卡片", latest_card.exists() and "可复用逻辑" in card, str(latest_card)),
        check("首批真实经验卡片", latest_real_cards.exists() and real_cards.get("卡片数量", 0) >= 6, real_cards),
        check(
            "经验类型覆盖",
            all(item in report.get("经验类型统计", {}) for item in ["同类复用", "类似借鉴", "异类归纳"]),
            report.get("经验类型统计", {}),
        ),
        check("复盘报告结构", latest_report.exists() and "方法资产候选" in report, report.get("经验卡片数量")),
        check("进化建议结构", latest_suggestion.exists() and suggestion.get("安全边界"), suggestion.get("建议数量")),
        check("样本价值评估结构", latest_value_report.exists() and value_report.get("是否删除文件") is False, value_report.get("清理候选数量")),
        check(
            "通用方法库结构",
            latest_method_library.exists() and method_library.get("是否自动固化") is False and method_library.get("通用方法数量", 0) >= 4,
            method_library.get("通用方法数量"),
        ),
    ]

    output_report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "evolution-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"evolution-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir() / "evolution-base-verify-最新.json"
    text = json.dumps(output_report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps(output_report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if output_report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
