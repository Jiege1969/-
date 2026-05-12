# -*- coding: utf-8 -*-
"""
名称：验证股票助手交付前只读总状态面板.py
作用：验证股票助手交付前只读总状态面板是否汇总核心状态、保持未确认未执行和真实动作关闭。
触发方式：python 验证股票助手交付前只读总状态面板.py
依赖：Python标准库；生成股票助手交付前只读总状态面板.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地文件并写入04日志；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付前只读总状态面板验收脚本。
标识：stock-assistant-delivery-readonly-dashboard-verify
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


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": ok, "说明": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手交付前只读总状态面板.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "48交付前只读总状态面板" / "股票助手交付前只读总状态面板_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    readiness = report.get("关键判定", {})
    checks: list[dict[str, Any]] = []

    add_check(checks, "最新状态面板存在", latest.exists(), str(latest))
    add_check(checks, "面板结论通过", report.get("是否适合继续低风险施工") is True, str(report.get("当前结论", "")))
    add_check(checks, "核心状态完整", len(report.get("核心状态", [])) >= 6 and all(item.get("存在") is True for item in report.get("核心状态", [])), str(report.get("核心状态", [])))
    add_check(checks, "关键判定全部通过", all(readiness.values()), str(readiness))
    add_check(checks, "股票进度口径存在", bool(report.get("股票系统进度", {}).get("当前进度")), str(report.get("股票系统进度", {})))
    add_check(checks, "仍未放行动作完整", len(report.get("仍未放行动作", [])) >= 9 and "自动交易" in report.get("仍未放行动作", []), str(report.get("仍未放行动作", [])))
    add_check(checks, "不触发真实动作", all(actions.get(key) is True for key in [
        "不删除文件",
        "不覆盖配置",
        "不重启服务",
        "不调用n8n API",
        "不触发n8n",
        "不调用OpenClaw",
        "不发送企业微信",
        "不写正式库",
        "不写旧系统",
        "不调用券商接口",
        "不自动交易",
    ]), str(actions))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = root / "04日志" / "交付前只读总状态面板"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-delivery-readonly-dashboard-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-delivery-readonly-dashboard-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
