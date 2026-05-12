# -*- coding: utf-8 -*-
"""
名称：验证股票助手n8n未激活导入申请单.py
作用：验证股票助手n8n未激活导入申请单是否具备前置材料、申请字段、停止条件、回滚方案、验收方法和安全边界。
触发方式：python 验证股票助手n8n未激活导入申请单.py
依赖：Python标准库；生成股票助手n8n未激活导入申请单.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地文件并写入04日志；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手n8n未激活导入申请单验收脚本。
标识：stock-assistant-n8n-inactive-import-request-verify
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
    generator = root / "02脚本" / "生成股票助手n8n未激活导入申请单.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "63n8n未激活导入申请单" / "股票助手n8n未激活导入申请单_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []

    add_check(checks, "最新申请单存在", latest.exists(), str(latest))
    add_check(checks, "申请单结论通过", report.get("是否具备n8n未激活导入申请条件") is True, str(report.get("当前结论", "")))
    add_check(checks, "前置判定全部通过", all(report.get("前置判定", {}).values()), str(report.get("前置判定", {})))
    add_check(checks, "申请字段完整", len(report.get("申请字段", {})) >= 6, str(report.get("申请字段", {})))
    add_check(checks, "停止条件完整", len(report.get("停止条件", [])) >= 6, str(report.get("停止条件", [])))
    add_check(checks, "回滚方案完整", len(report.get("回滚方案", [])) >= 4, str(report.get("回滚方案", [])))
    add_check(checks, "验收方法完整", len(report.get("验收方法", [])) >= 5, str(report.get("验收方法", [])))
    add_check(checks, "仍禁止事项完整", len(report.get("仍禁止事项", [])) >= 8, str(report.get("仍禁止事项", [])))
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
    log_dir = root / "04日志" / "n8n未激活导入申请单"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-request-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-inactive-import-request-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
