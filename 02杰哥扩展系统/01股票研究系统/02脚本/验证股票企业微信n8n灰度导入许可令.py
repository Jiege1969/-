# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信n8n灰度导入许可令.py
作用：验证股票企业微信n8n灰度导入许可令已生成，且未执行n8n导入、启用或触发。
触发方式：python 验证股票企业微信n8n灰度导入许可令.py
依赖：Python标准库；生成股票企业微信n8n灰度导入许可令.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地许可令验收；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不调用OpenClaw；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信n8n灰度导入许可令验收脚本。
标识：stock-wework-n8n-import-permit-verify
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
    generator = root / "02脚本" / "生成股票企业微信n8n灰度导入许可令.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "29n8n灰度导入许可" / "股票企业微信n8n灰度导入许可令_最新.json"
    latest_md = root / "03数据" / "29n8n灰度导入许可" / "股票企业微信n8n灰度导入许可令_最新.md"
    permit = load_json(latest_json)
    actions = permit.get("实际动作", {})
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    checks: list[dict[str, Any]] = []
    add_check(checks, "许可令生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "许可令生成成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON许可令存在", latest_json.exists() and permit.get("模式") == "import_permit_only", str(latest_json))
    add_check(checks, "最新Markdown许可令存在", latest_md.exists() and "股票企业微信n8n灰度导入许可令" in text, str(latest_md))
    add_check(checks, "证据检查全部通过", permit.get("失败") == 0, permit.get("证据检查", []))
    add_check(checks, "未执行高风险动作", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票企业微信n8n灰度导入许可令可用，尚未导入n8n。" if failed == 0 else "股票企业微信n8n灰度导入许可令存在失败项。",
    }
    output_dir = root / "04日志" / "n8n灰度导入许可"
    output = output_dir / f"stock-wework-n8n-import-permit-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-n8n-import-permit-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
