"""
名称：验证OpenClaw边缘网关.py
作用：验证 v3 OpenClaw 边缘网关契约、本地回环测试和统一消息出口衔接是否可用。
触发方式：python 验证OpenClaw边缘网关.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只运行本地回环测试，不连接企业微信，不调用 n8n，不发送真实消息。
创建/修改记录：2026-04-26 创建 OpenClaw 边缘网关验证脚本。
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


def component_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "00公共组件"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "OpenClaw验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = component_root()
    contract = load_json(root / "01配置" / "OpenClaw边缘网关契约.json")
    script = root / "02脚本" / "OpenClaw本地回环测试.py"
    result = subprocess.run(
        [sys.executable, str(script), "--self-test"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    stdout = (result.stdout or "").strip()
    self_test = json.loads(stdout.splitlines()[-1]) if stdout else {}
    latest = root / "03数据" / "03OpenClaw回环测试" / "OpenClaw回环测试_最新.json"
    latest_data = load_json(latest) if latest.exists() else {}
    duties = contract.get("网关职责", {})
    strategy = contract.get("测试策略", {})

    checks = [
        check("OpenClaw契约", "网关职责" in contract and "测试策略" in contract, contract.get("说明")),
        check("只做边缘网关", duties.get("转换为标准请求") is True and duties.get("交给统一消息出口") is True, duties),
        check("禁止业务判断", duties.get("禁止业务判断") is True, duties),
        check("禁止直接发送企微", duties.get("禁止直接发送企微") is True, duties),
        check("测试不连接企业微信", strategy.get("是否连接企业微信") is False and self_test.get("是否连接企业微信") is False, strategy),
        check("测试不调用n8n", strategy.get("是否调用n8n") is False and self_test.get("是否调用n8n") is False, strategy),
        check("测试不真实发送", strategy.get("是否真实发送") is False and self_test.get("是否真实发送") is False, strategy),
        check("回环脚本执行", result.returncode == 0, stdout or result.stderr),
        check("回环报告存在", latest.exists(), str(latest)),
        check("回环报告结构", "标准请求" in latest_data and "模拟响应" in latest_data and "入队消息ID" in latest_data, latest_data.get("测试模式")),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "openclaw-gateway-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"openclaw-gateway-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "openclaw-gateway-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
