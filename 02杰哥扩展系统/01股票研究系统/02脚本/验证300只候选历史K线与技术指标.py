# -*- coding: utf-8 -*-
"""
名称：验证300只候选历史K线与技术指标.py
作用：验证300只候选历史K线与技术指标链路是否可运行、字段是否完整、安全边界是否保持。
触发方式：python 验证300只候选历史K线与技术指标.py
依赖：Python标准库；生成300只候选历史K线与技术指标.py；300只候选历史K线技术指标规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读候选历史K线和技术指标结果并写入验收日志；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选历史K线与技术指标验收脚本。
标识：stock-trial-pool-300-candidate-kline-indicator-verify
"""

from __future__ import annotations

import json
import os
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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成300只候选历史K线与技术指标.py"
    rule_path = root / "01配置" / "300只候选历史K线技术指标规则.json"
    checks: list[dict[str, Any]] = [
        check("脚本存在", script.exists(), str(script)),
        check("规则存在", rule_path.exists(), str(rule_path)),
    ]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=360,
    )
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))

    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    history_latest = output_dir / rule["输出"]["历史K线最新文件"]
    indicator_latest = output_dir / rule["输出"]["技术指标最新文件"]
    report_latest = output_dir / rule["输出"]["报告最新文件"]
    checks.append(check("历史K线最新文件存在", history_latest.exists(), str(history_latest)))
    checks.append(check("技术指标最新文件存在", indicator_latest.exists(), str(indicator_latest)))
    checks.append(check("Markdown报告存在", report_latest.exists(), str(report_latest)))

    history = load_json(history_latest) if history_latest.exists() else {}
    indicators = load_json(indicator_latest) if indicator_latest.exists() else {}
    history_rows = history.get("历史K线", [])
    indicator_rows = indicators.get("技术指标", [])
    checks.append(check("候选数量一致", history.get("候选数量") == indicators.get("候选数量") == len(history_rows) == len(indicator_rows), {
        "history_count": history.get("候选数量"),
        "indicator_count": indicators.get("候选数量"),
        "history_rows": len(history_rows),
        "indicator_rows": len(indicator_rows),
    }))
    checks.append(check("历史K线成功数量大于0", history.get("成功数量", 0) > 0, history.get("成功数量", 0)))
    checks.append(check("技术指标成功数量大于0", indicators.get("成功数量", 0) > 0, indicators.get("成功数量", 0)))

    required_indicator = {"代码", "名称", "状态", "K线数量", "最新日期", "最新收盘", "均线", "RSI14", "MACD", "成交量MA20", "量比5日", "技术观察"}
    missing = [
        item.get("代码") or item.get("名称") or "未知"
        for item in indicator_rows
        if not required_indicator.issubset(set(item))
    ]
    checks.append(check("指标字段完整", not missing, "缺失：" + "、".join(missing) if missing else "完整"))
    contains_core_indicator = any(
        item.get("均线", {}).get("MA60") is not None
        and item.get("RSI14") is not None
        and item.get("MACD", {}).get("MACD") is not None
        for item in indicator_rows
    )
    checks.append(check("包含核心指标", contains_core_indicator, "MA60、RSI14、MACD至少一只候选完整"))

    forbidden = {}
    forbidden.update(history.get("安全边界", {}))
    forbidden.update(indicators.get("安全边界", {}))
    safe = all(value is False for value in forbidden.values())
    checks.append(check("高风险动作未触发", safe, json.dumps(forbidden, ensure_ascii=False)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": {
            "历史K线": str(history_latest),
            "技术指标": str(indicator_latest),
            "报告": str(report_latest),
        },
    }
    output_dir = root / "04日志" / "候选历史K线技术指标"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-candidate-kline-indicator-verify-{stamp}.json"
    latest = output_dir / "trial-pool-300-candidate-kline-indicator-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
