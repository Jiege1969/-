"""
名称：验证旧系统保护.py
作用：汇总验证旧系统保护规则和股票研究系统只读桥接规则，纳入新系统总体验收。
触发方式：python 验证旧系统保护.py
依赖：Python 标准库；检查旧系统保护状态.py；检查旧股票系统只读桥接.py。
所属系统：00杰哥系统总管
安全边界：只读验证和写入新系统验收日志；不修改、不停止、不迁移旧系统。
创建/修改记录：2026-04-27 创建旧系统保护总体验证脚本。
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
    return subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager_config_path = root / "00杰哥系统总管" / "01配置" / "旧系统保护规则.json"
    stock_config_path = root / "02杰哥扩展系统" / "01股票研究系统" / "01配置" / "旧股票系统只读桥接规则.json"
    manager_check_script = root / "00杰哥系统总管" / "02脚本" / "检查旧系统保护状态.py"
    stock_bridge_script = root / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "检查旧股票系统只读桥接.py"

    manager_result = run_script(manager_check_script)
    stock_result = run_script(stock_bridge_script)
    manager_config = load_json(manager_config_path)
    stock_config = load_json(stock_config_path)
    manager_latest = load_json(root / "00杰哥系统总管" / "04日志" / "旧系统保护" / "old-system-protection-status-最新.json")
    stock_latest = load_json(root / "02杰哥扩展系统" / "01股票研究系统" / "04日志" / "旧系统桥接" / "old-stock-readonly-bridge-最新.json")

    manager_false_flags = [
        "是否接管旧系统",
        "是否停止旧系统服务",
        "是否修改旧系统文件",
        "是否迁移旧系统数据",
        "是否删除旧系统文件",
        "是否占用旧系统端口",
    ]
    stock_false_flags = [
        "是否接管旧系统",
        "是否停止旧服务",
        "是否修改旧系统文件",
        "是否迁移旧数据",
        "是否删除旧文件",
        "是否触发旧工作流",
        "是否接入真实股票交易",
    ]
    checks = [
        check("旧系统保护配置存在", manager_config_path.exists(), str(manager_config_path)),
        check("股票只读桥接配置存在", stock_config_path.exists(), str(stock_config_path)),
        check("旧系统保护检查脚本通过", manager_result.returncode == 0, manager_result.stdout.strip() or manager_result.stderr.strip()),
        check("股票只读桥接检查脚本通过", stock_result.returncode == 0, stock_result.stdout.strip() or stock_result.stderr.strip()),
        check("旧系统保护开关全部关闭危险动作", all(manager_config.get(flag) is False for flag in manager_false_flags), {flag: manager_config.get(flag) for flag in manager_false_flags}),
        check("股票桥接开关全部关闭危险动作", all(stock_config.get(flag) is False for flag in stock_false_flags), {flag: stock_config.get(flag) for flag in stock_false_flags}),
        check("旧系统目录保护状态通过", manager_latest.get("保护状态通过") is True, manager_latest.get("结论")),
        check("股票系统只读桥接通过", stock_latest.get("只读桥接通过") is True, stock_latest.get("结论")),
        check("新旧系统路径隔离", manager_latest.get("新旧系统路径隔离") is True and stock_latest.get("新旧路径隔离") is True, {"总管": manager_latest.get("新旧系统路径隔离"), "股票": stock_latest.get("新旧路径隔离")}),
        check("未对旧系统执行写停迁删", not any([manager_latest.get("是否写入旧系统"), manager_latest.get("是否停止旧服务"), manager_latest.get("是否迁移旧数据"), manager_latest.get("是否删除旧文件"), stock_latest.get("是否写入旧系统"), stock_latest.get("是否停止旧服务"), stock_latest.get("是否触发旧工作流")]), "只读验证"),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "old-system-protection-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "旧系统保护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"old-system-protection-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "old-system-protection-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
