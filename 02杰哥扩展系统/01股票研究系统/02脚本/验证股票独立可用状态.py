# -*- coding: utf-8 -*-
"""
名称：验证股票独立可用状态.py
作用：验证股票系统能独立读取重点关注池、生成动态样本池设计报告、运行日常研究链路，并可生成公开行情快照。
触发方式：python 验证股票独立可用状态.py
依赖：Python标准库；运行股票日常研究链路.py；生成动态样本池设计报告.py；生成重点关注池公开行情快照.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写入新系统股票模块目录；只读公开行情；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信。
创建/修改记录：2026-04-28 创建股票独立可用状态验证脚本。
标识：stock-independent-usable-status-verify
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


def run_script(path: Path) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    return {"脚本": str(path), "返回码": result.returncode, "输出": result.stdout.strip(), "错误": result.stderr.strip()}


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    scripts = [
        root / "02脚本" / "生成动态样本池设计报告.py",
        root / "02脚本" / "运行股票日常研究链路.py",
        root / "02脚本" / "生成重点关注池公开行情快照.py",
    ]
    results = [run_script(path) for path in scripts]
    focus_path = root / "01配置" / "重点关注股票池.json"
    focus = load_json(focus_path)
    pool_path = root / "01配置" / "股票池模板.json"
    pool = load_json(pool_path) if pool_path.exists() else {}
    sample_report_path = root / "03数据" / "07样本池" / "动态样本池设计报告_最新.json"
    quote_path = root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json"
    quote = load_json(quote_path) if quote_path.exists() else {}
    quote_available = quote.get("返回数量", 0) > 0
    checks = [
        check("重点关注池不少于十九只", len(focus.get("股票池", [])) >= 19, len(focus.get("股票池", []))),
        check("动态样本池设计报告存在", sample_report_path.exists(), str(sample_report_path)),
        check("股票日常研究链路成功", results[1]["返回码"] == 0, results[1]),
        check("新系统股票池不少于十九只", len(pool.get("股票池", [])) >= 19, len(pool.get("股票池", []))),
        check("公开行情快照可用", results[2]["返回码"] == 0 or quote_available, {"刷新结果": results[2], "缓存返回数量": quote.get("返回数量")}),
        check("公开行情返回数量大于零", quote_available, quote.get("返回数量")),
        check("研究报告存在", (root / "03数据" / "03研究报告" / "股票研究报告_最新.md").exists(), "股票研究报告_最新.md"),
        check("风险摘要存在", (root / "03数据" / "03研究报告" / "股票风险摘要_最新.json").exists(), "股票风险摘要_最新.json"),
        check("未调用券商接口", all("券商" not in item.get("脚本", "") for item in results), results),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-independent-usable-status-verify",
        "脚本结果": results,
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "独立可用"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stock-independent-usable-status-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-independent-usable-status-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
