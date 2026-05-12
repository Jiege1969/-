# -*- coding: utf-8 -*-
"""
名称：验证日常可用版攻坚状态报告.py
作用：生成并验证日常可用版攻坚状态报告，确认进度、执行器、调度适配、n8n草案和真实动作关闭状态可追踪。
触发方式：python 验证日常可用版攻坚状态报告.py
依赖：Python 标准库；生成日常可用版攻坚状态报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证状态报告；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建日常可用版攻坚状态报告验证脚本。
标识：daily-usable-assault-status-report-verify
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成日常可用版攻坚状态报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "阶段判定" / "日常可用版攻坚状态报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("攻坚状态报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("攻坚状态报告文件存在", report_path.exists(), str(report_path)),
        check("总体验收无失败", report.get("总体验收", {}).get("汇总", {}).get("failed") == 0, report.get("总体验收", {})),
        check("首批执行器三个就绪但冻结", report.get("首批执行器", {}).get("就绪但冻结数量") == 3, report.get("首批执行器", {})),
        check("调度适配未触发n8n", report.get("调度适配", {}).get("n8n触发数量") == 0, report.get("调度适配", {})),
        check("n8n草案未激活", report.get("n8n禁用工作流草案", {}).get("激活数量") == 0, report.get("n8n禁用工作流草案", {})),
        check("最终闸口未开放", report.get("最终闸口", {}).get("是否允许真实动作") is False, report.get("最终闸口", {})),
        check("税收业务仍未开放", "税收业务" in report.get("仍未开放", []), report.get("仍未开放", [])),
        check("旧系统写入仍未开放", "旧系统写入" in report.get("仍未开放", []), report.get("仍未开放", [])),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-usable-assault-status-report-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "阶段判定"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-usable-assault-status-report-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
