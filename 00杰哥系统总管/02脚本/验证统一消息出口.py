"""
名称：验证统一消息出口.py
作用：验证 v3 统一消息出口配置、本地队列、消息合并和真实发送关闭状态是否可用。
触发方式：python 验证统一消息出口.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只运行统一消息出口本地自检，不调用企业微信接口，不发送真实消息。
创建/修改记录：2026-04-26 创建统一消息出口验证脚本。
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
    target = v3_root() / "00杰哥系统总管" / "04日志" / "统一消息出口验收"
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
    config = load_json(root / "01配置" / "统一消息出口配置.json")
    script = root / "02脚本" / "统一消息出口.py"
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
    latest = root / "03数据" / "02合并消息" / "统一消息合并_最新.json"
    latest_data = load_json(latest) if latest.exists() else {}

    checks = [
        check("统一消息配置", config.get("出口策略", {}).get("唯一出口") is True, config.get("说明")),
        check("真实发送关闭", config.get("出口策略", {}).get("是否允许真实发送") is False, config.get("出口策略", {})),
        check("脚本自检执行", result.returncode == 0, stdout or result.stderr),
        check("自检不真实发送", self_test.get("真实发送") is False, self_test),
        check("队列文件存在", Path(self_test.get("队列文件", "")).exists(), self_test.get("队列文件")),
        check("合并消息存在", latest.exists(), str(latest)),
        check("合并消息结构", "合并文本" in latest_data and latest_data.get("真实发送") is False, latest_data.get("消息数量")),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "message-outlet-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"message-outlet-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "message-outlet-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
