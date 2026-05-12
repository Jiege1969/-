# -*- coding: utf-8 -*-
"""
名称：验证无人值守守护权限分级.py
作用：生成并验证无人值守守护权限分级报告，确认L0/L1可自动、L2/L3默认阻断。
触发方式：python 验证无人值守守护权限分级.py
依赖：Python 标准库；生成无人值守守护权限分级报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证权限分级报告；不删除；不覆盖；不重启服务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建无人值守守护权限分级验证脚本。
标识：unattended-guardian-permission-tier-verify
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
    script = manager / "02脚本" / "生成无人值守守护权限分级报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守守护权限分级报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("默认开关", {})
    allow = report.get("自动允许等级", [])
    block = report.get("自动阻断等级", [])
    checks = [
        check("权限分级报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("权限分级报告文件存在", report_path.exists(), str(report_path)),
        check("L0自动允许", "L0只读巡检" in allow, allow),
        check("L1自动允许", "L1低风险修复" in allow, allow),
        check("L2自动阻断", "L2服务级操作" in block, block),
        check("L3自动阻断", "L3破坏性操作" in block, block),
        check("删除关闭", switches.get("允许删除") is False, switches),
        check("覆盖关闭", switches.get("允许覆盖") is False, switches),
        check("重启服务关闭", switches.get("允许重启服务") is False, switches),
        check("n8n触发关闭", switches.get("允许触发n8n") is False, switches),
        check("税收业务关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-guardian-permission-tier-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-guardian-permission-tier-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
