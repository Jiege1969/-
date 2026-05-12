"""
名称：验证股票研究底座.py
作用：验证 v3 股票研究系统第一阶段配置、股票池模板、数据源、研究计划和报告脚本是否可用。
触发方式：python 验证股票研究底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 股票研究配置和本地快照，只运行只读脚本；不抓行情、不调用券商、不执行交易。
创建/修改记录：2026-04-26 创建第一阶段股票研究底座验证脚本。
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


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "01股票研究系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "股票研究验收"
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
    root = module_root()
    config = load_json(root / "01配置" / "股票研究配置.json")
    pool = load_json(root / "01配置" / "股票池模板.json")
    sources = load_json(root / "01配置" / "股票数据源注册表.json")
    template = load_json(root / "01配置" / "股票报告模板.json")
    snapshot = load_json(root / "03数据" / "04数据快照" / "股票数据快照模板.json")
    plan_script = root / "02脚本" / "生成股票研究计划.py"
    report_script = root / "02脚本" / "生成股票研究报告.py"
    risk_script = root / "02脚本" / "生成股票风险摘要.py"
    plan_result = subprocess.run(
        [sys.executable, str(plan_script)],
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
    risk_result = subprocess.run(
        [sys.executable, str(risk_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest = root / "03数据" / "02研究计划" / "股票研究计划_最新.json"
    latest_data = load_json(latest) if latest.exists() else {}
    latest_report = root / "03数据" / "03研究报告" / "股票研究报告_最新.md"
    report_text = latest_report.read_text(encoding="utf-8") if latest_report.exists() else ""
    latest_risk = root / "03数据" / "03研究报告" / "股票风险摘要_最新.json"
    risk_data = load_json(latest_risk) if latest_risk.exists() else {}

    checks = [
        check("股票研究配置", "默认研究维度" in config and "输出规则" in config, config.get("说明")),
        check("股票池模板", "股票池" in pool and isinstance(pool.get("股票池"), list), pool.get("说明")),
        check("数据源注册表", "数据源" in sources and "禁止事项" in sources, sources.get("说明")),
        check("报告模板", "章节" in template and "固定声明" in template, template.get("说明")),
        check("数据快照模板", "股票" in snapshot and isinstance(snapshot.get("股票"), list), snapshot.get("说明")),
        check("计划脚本执行", plan_result.returncode == 0, (plan_result.stdout or "").strip() or (plan_result.stderr or "").strip()),
        check("最新研究计划", latest.exists(), str(latest)),
        check("研究计划结构", "任务列表" in latest_data and "安全边界" in latest_data, latest_data.get("股票数量")),
        check("报告脚本执行", report_result.returncode == 0, (report_result.stdout or "").strip() or (report_result.stderr or "").strip()),
        check("最新研究报告", latest_report.exists(), str(latest_report)),
        check("研究报告声明", "不构成投资建议" in report_text and "不作为买卖指令" in report_text, "risk disclaimer"),
        check("风险摘要脚本执行", risk_result.returncode == 0, (risk_result.stdout or "").strip() or (risk_result.stderr or "").strip()),
        check("最新风险摘要", latest_risk.exists(), str(latest_risk)),
        check("风险摘要结构", "风险条目" in risk_data and "固定提示" in risk_data, risk_data.get("风险条目数量")),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"stock-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "stock-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
