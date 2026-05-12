# -*- coding: utf-8 -*-
"""
名称：验证股票统一消息出口禁用态回复包.py
作用：验证股票统一消息出口禁用态回复包已生成，且复用00公共组件统一消息出口并保持真实发送关闭。
触发方式：python 验证股票统一消息出口禁用态回复包.py
依赖：Python标准库；生成股票统一消息出口禁用态回复包.py；统一消息出口.py；股票统一消息出口禁用态规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地回复包验收；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建股票统一消息出口禁用态回复包验收脚本。
标识：stock-unified-message-outlet-disabled-package-verify
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
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票统一消息出口禁用态回复包.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "34统一消息出口禁用态" / "股票统一消息出口禁用态回复包_最新.json"
    latest_md = root / "03数据" / "34统一消息出口禁用态" / "股票统一消息出口禁用态回复包_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    queue_file = Path(report.get("队列文件", ""))
    merged_file = Path(report.get("合并预览文件", ""))
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and bool(report.get("content")), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票统一消息出口禁用态回复包" in text, str(latest_md))
    add_check(checks, "复用统一消息出口", "00公共组件" in report.get("统一消息出口脚本", ""), report.get("统一消息出口脚本"))
    add_check(checks, "本地队列存在", queue_file.exists(), str(queue_file))
    add_check(checks, "合并预览存在", merged_file.exists() and report.get("合并预览", {}).get("真实发送") is False, str(merged_file))
    add_check(checks, "真实动作全部关闭", all(report.get(key) is False for key in ["real_send", "trigger_n8n", "call_openclaw", "write_official_db", "write_old_system", "trade"]), "安全字段")
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票统一消息出口禁用态回复包可用。" if failed == 0 else "股票统一消息出口禁用态回复包存在失败项。",
    }
    output_dir = root / "04日志" / "统一消息出口禁用态"
    output = output_dir / f"stock-unified-message-outlet-disabled-package-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-unified-message-outlet-disabled-package-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
