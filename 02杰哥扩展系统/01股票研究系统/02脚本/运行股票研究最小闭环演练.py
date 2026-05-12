# -*- coding: utf-8 -*-
"""
名称：运行股票研究最小闭环演练.py
作用：串联股票研究分析、观察、验证、提炼、优化建议的本地最小闭环，作为旧系统退役前置验收。
触发方式：python 运行股票研究最小闭环演练.py
依赖：Python标准库；股票研究最小闭环演练规则.json；股票研究系统本地脚本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行新股票系统本地脚本；不导入n8n；不激活工作流；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-30 创建股票研究最小闭环演练总控脚本。
标识：stock-minimal-review-loop-run
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_script(path: Path, timeout: int = 240) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "脚本": str(path),
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def file_state(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() and path.is_file() else 0,
    }


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票研究最小闭环演练规则.json"
    rules = load_json(rule_path)
    scripts = [
        ("生成闭环蓝图", root / "02脚本" / "生成研究决策复盘闭环蓝图.py", 120),
        ("运行日常研究", root / "02脚本" / "运行股票日常研究链路.py", 180),
        ("验证技术指标", root / "02脚本" / "验证技术指标计算链路.py", 240),
        ("生成候选池", root / "02脚本" / "生成重点关注池候选池.py", 180),
        ("运行L5复盘联动", root / "02脚本" / "运行L5日报复盘联动链路.py", 240),
        ("验证四本账", root / "02脚本" / "验证复盘账本可运行.py", 240),
        ("生成n8n未激活草案", root / "02脚本" / "生成股票研究闭环n8n未激活工作流草案.py", 120),
    ]
    results = []
    for name, path, timeout in scripts:
        item = run_script(path, timeout=timeout)
        item["名称"] = name
        results.append(item)
    acceptance = [
        file_state(root, relative)
        for relative in rules.get("验收文件", {}).values()
    ]
    checks = [
        {
            "名称": "所有闭环脚本执行成功",
            "通过": all(item["返回码"] == 0 for item in results),
            "详情": [{"名称": item["名称"], "返回码": item["返回码"]} for item in results],
        },
        {
            "名称": "闭环验收文件全部生成",
            "通过": all(item["存在"] and item["大小"] > 0 for item in acceptance),
            "详情": acceptance,
        },
        {
            "名称": "高风险动作保持关闭",
            "通过": all(value is False for value in rules.get("安全边界", {}).values()),
            "详情": rules.get("安全边界", {}),
        },
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "阶段": rules.get("闭环阶段", []),
        "执行结果": results,
        "验收文件": acceptance,
        "检查项": checks,
        "通过": passed,
        "失败": failed,
        "结论": "股票研究最小闭环本地演练通过，可作为旧系统退役前置条件之一。" if failed == 0 else "股票研究最小闭环本地演练仍有失败项。",
        "安全边界": rules.get("安全边界", {}),
    }
    output_dir = root / "04日志" / "股票研究最小闭环演练"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"stock-minimal-review-loop-run-{timestamp}.json"
    latest = output_dir / "stock-minimal-review-loop-run-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
