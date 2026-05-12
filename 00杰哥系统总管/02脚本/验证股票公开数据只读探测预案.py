"""
名称：验证股票公开数据只读探测预案.py
作用：生成并验证股票公开数据只读探测预案，确认真实联网、券商接口、自动交易、n8n触发、企业微信发送和旧系统写入均保持关闭。
触发方式：python 验证股票公开数据只读探测预案.py
依赖：Python 标准库；生成股票公开数据只读探测预案.py；股票公开数据只读探测规则.json。
所属系统：00杰哥系统总管
安全边界：只运行预案生成和只读验证；不执行联网请求；不调用券商接口；不交易；不触发n8n；不发送企业微信；不写入旧系统；不接入税收。
创建/修改记录：2026-04-27 创建股票公开数据只读探测预案验收脚本。
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


def stock_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "01股票研究系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = stock_root()
    script = root / "02脚本" / "生成股票公开数据只读探测预案.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rules_path = root / "01配置" / "股票公开数据只读探测规则.json"
    plan_path = root / "03数据" / "06公开数据探测" / "股票公开数据只读探测预案_最新.json"
    rules = load_json(rules_path) if rules_path.exists() else {}
    plan = load_json(plan_path) if plan_path.exists() else {}
    switches = rules.get("默认开关", {})
    request_boundary = rules.get("请求边界", {})
    checks = [
        check("预案脚本执行成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("规则文件存在", rules_path.exists(), str(rules_path)),
        check("预案文件存在", plan_path.exists(), str(plan_path)),
        check("联网请求默认关闭", switches.get("允许联网请求") is False, switches.get("允许联网请求")),
        check("真实行情抓取默认关闭", switches.get("允许真实行情抓取") is False, switches.get("允许真实行情抓取")),
        check("券商接口关闭", switches.get("允许券商接口") is False, switches.get("允许券商接口")),
        check("自动交易关闭", switches.get("允许自动交易") is False, switches.get("允许自动交易")),
        check("旧系统写入关闭", switches.get("允许写入旧系统") is False, switches.get("允许写入旧系统")),
        check("n8n触发关闭", switches.get("允许触发n8n") is False, switches.get("允许触发n8n")),
        check("企业微信真实发送关闭", switches.get("允许企业微信真实发送") is False, switches.get("允许企业微信真实发送")),
        check("请求数上限受控", request_boundary.get("单轮最大请求数", 0) <= 3, request_boundary.get("单轮最大请求数")),
        check("预案包含放行条件", len(plan.get("放行条件", [])) >= 4, plan.get("放行条件", [])),
        check("预案禁止税收接入", any("税收" in item for item in plan.get("禁止事项", [])), plan.get("禁止事项", [])),
        check("预案明确只生成不抓取", "不执行联网抓取" in plan.get("安全结论", ""), plan.get("安全结论")),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-public-readonly-probe-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "股票公开数据探测"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stock-public-readonly-probe-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-public-readonly-probe-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
