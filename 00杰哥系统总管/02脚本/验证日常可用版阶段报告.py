"""
名称：验证日常可用版阶段报告.py
作用：生成并验证日常可用版阶段报告，确认入口、队列、确认、放行、旧系统保护和总体验收均闭环。
触发方式：python 验证日常可用版阶段报告.py
依赖：Python 标准库；生成日常可用版阶段报告.py。
所属系统：00杰哥系统总管
安全边界：只读日志并写入验收报告；不触发n8n、不发送企业微信、不写旧系统、不恢复税收业务。
创建/修改记录：2026-04-27 创建日常可用版阶段报告验收脚本。
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
    script = root / "00杰哥系统总管" / "02脚本" / "生成日常可用版阶段报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "00杰哥系统总管" / "03数据" / "阶段判定" / "日常可用版阶段报告_最新.json"
    md_path = root / "00杰哥系统总管" / "03数据" / "阶段判定" / "日常可用版阶段报告_最新.md"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("阶段报告脚本执行成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("阶段报告json存在", report_path.exists(), str(report_path)),
        check("阶段报告markdown存在", md_path.exists(), str(md_path)),
        check("日常可用版完成判定通过", report.get("完成判定") == "日常可用版入口与任务缓冲层已完成", report.get("完成判定")),
        check("能力闭环全部通过", all(item.get("通过") is True for item in report.get("能力闭环", [])), report.get("能力闭环", [])),
        check("安全边界保持关闭", report.get("安全边界", {}).get("税收业务") == "继续暂停施工" and report.get("安全边界", {}).get("企业微信真实发送") == "未触发", report.get("安全边界", {})),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-usable-stage-report-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-usable-stage-report-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
