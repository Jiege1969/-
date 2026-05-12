"""
名称：验证稳定中台异常诊断预案.py
作用：验证稳定中台异常诊断预案可生成，且所有自动修复和真实动作开关保持关闭。
触发方式：python 验证稳定中台异常诊断预案.py
依赖：Python 标准库；生成稳定中台心跳快照.py；生成稳定中台异常诊断预案.py。
所属系统：00杰哥系统总管
安全边界：只生成诊断预案并写入验收日志；不自动修复、不重启服务、不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台异常诊断预案验收脚本。
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


def run_script(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    heartbeat_result = run_script(root / "00杰哥系统总管" / "02脚本" / "生成稳定中台心跳快照.py")
    diagnosis_result = run_script(root / "00杰哥系统总管" / "02脚本" / "生成稳定中台异常诊断预案.py")
    latest = root / "00杰哥系统总管" / "04日志" / "稳定中台" / "stable-hub-diagnosis-plan-最新.json"
    data = load_json(latest) if latest.exists() else {}
    switches = data.get("执行开关", {})
    checks = [
        check("心跳快照生成成功", heartbeat_result.returncode == 0, heartbeat_result.stdout.strip() or heartbeat_result.stderr.strip()),
        check("诊断预案生成成功", diagnosis_result.returncode == 0, diagnosis_result.stdout.strip() or diagnosis_result.stderr.strip()),
        check("诊断预案存在", latest.exists(), str(latest)),
        check("诊断预案数量大于零", len(data.get("诊断预案", [])) > 0, len(data.get("诊断预案", []))),
        check("所有执行开关关闭", all(value is False for value in switches.values()), switches),
        check("每个预案包含禁止动作", all(item.get("禁止动作") for item in data.get("诊断预案", [])), data.get("诊断预案", [])),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-diagnosis-plan-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stable-hub-diagnosis-plan-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
