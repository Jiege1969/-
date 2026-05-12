"""
名称：生成股票风险摘要.py
作用：根据最新股票研究报告生成规则化风险摘要。
触发方式：python 生成股票风险摘要.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本模块最新研究报告，只写入本模块研究报告目录；不联网、不交易、不调用券商接口。
创建/修改记录：2026-04-26 创建第一阶段股票风险摘要脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = module_root()
    report_path = root / "03数据" / "03研究报告" / "股票研究报告_最新.md"
    output_dir = root / "03数据" / "03研究报告"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not report_path.exists():
        raise FileNotFoundError(f"latest report not found: {report_path}")

    report = report_path.read_text(encoding="utf-8")
    risk_lines = []
    capture = False
    for line in report.splitlines():
        stripped = line.strip()
        if stripped == "### 风险":
            capture = True
            continue
        if capture and stripped.startswith("### "):
            capture = False
        if capture and stripped.startswith("-"):
            risk_lines.append(stripped)

    summary = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源报告": str(report_path),
        "风险条目数量": len(risk_lines),
        "风险条目": risk_lines,
        "固定提示": "投资有风险。本摘要仅基于本地研究报告提取，不构成投资建议，不作为买卖指令。",
    }
    output = output_dir / f"股票风险摘要_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    latest = output_dir / "股票风险摘要_最新.json"
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"风险条目数量": len(risk_lines), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
