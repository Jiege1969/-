# -*- coding: utf-8 -*-
"""
名称：验证股票日常研究链路.py
作用：运行并验证股票研究系统日常链路，确认能读取重点关注池并生成股票池、样例快照、研究计划、研究报告和风险摘要。
触发方式：python 验证股票日常研究链路.py
依赖：Python标准库；运行股票日常研究链路.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成和验证新系统股票模块文件；不联网；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信。
创建/修改记录：2026-04-28 创建股票日常研究链路验证脚本。
标识：stock-daily-research-pipeline-verify
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
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "运行股票日常研究链路.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    run_report_path = root / "04日志" / "日常运行" / "stock-daily-research-pipeline-run-最新.json"
    run_report = load_json(run_report_path) if run_report_path.exists() else {}
    safety = run_report.get("安全边界", {})
    output_files = run_report.get("输出文件", {})
    checks = [
        check("日常研究链路运行成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("运行报告存在", run_report_path.exists(), str(run_report_path)),
        check("重点关注池数量为十九个", run_report.get("重点关注池数量") == 19, run_report.get("重点关注池数量")),
        check("导入股票数量不少于十九个", run_report.get("导入股票数量", 0) >= 19, run_report.get("导入股票数量")),
        check("研究计划存在", Path(output_files.get("最新研究计划", "")).exists(), output_files.get("最新研究计划")),
        check("研究报告存在", Path(output_files.get("最新研究报告", "")).exists(), output_files.get("最新研究报告")),
        check("风险摘要存在", Path(output_files.get("最新风险摘要", "")).exists(), output_files.get("最新风险摘要")),
        check("未真实联网", safety.get("是否真实联网") is False, safety),
        check("未调用券商接口", safety.get("是否调用券商接口") is False, safety),
        check("未自动交易", safety.get("是否自动交易") is False, safety),
        check("未写旧系统", safety.get("是否写旧系统") is False, safety),
        check("未触发n8n", safety.get("是否触发n8n") is False, safety),
        check("未企业微信真实发送", safety.get("是否企业微信真实发送") is False, safety),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-daily-research-pipeline-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "日常运行"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"stock-daily-research-pipeline-verify-{timestamp}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    manager_output_dir = system_root() / "00杰哥系统总管" / "04日志" / "股票日常运行"
    manager_output_dir.mkdir(parents=True, exist_ok=True)
    manager_output = manager_output_dir / f"stock-daily-research-pipeline-verify-{timestamp}.json"
    manager_output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
