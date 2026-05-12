# -*- coding: utf-8 -*-
"""
名称：验证股票主动推送灰度链路一键只读巡检包.py
作用：验证257股票主动推送灰度链路一键只读巡检包。
触发方式：python 验证股票主动推送灰度链路一键只读巡检包.py
依赖：Python标准库；执行股票主动推送灰度链路一键只读巡检.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地巡检包并写验收日志；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易。
创建/修改记录：2026-05-09 创建股票主动推送灰度链路一键只读巡检包验收脚本。
标识：stock-active-push-gray-chain-one-click-readonly-patrol-verify
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送灰度链路一键只读巡检包验收",
        "",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 总体状态：{result['总体状态']}",
        f"- 通过：{result['通过']}",
        f"- 失败：{result['失败']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    runner = root / "02脚本" / "执行股票主动推送灰度链路一键只读巡检.py"
    completed = subprocess.run(
        [sys.executable, str(runner)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = root / "03数据" / "257主动推送灰度链路一键只读巡检包" / "股票主动推送灰度链路一键只读巡检_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous_keys = ["调用企业微信API", "真实发送企业微信", "启用n8n", "触发n8n", "重载19310", "重载19302", "调用券商接口", "自动交易", "写正式规则库", "修改总管面板", "修改一键接续包"]
    dangerous = [key for key in dangerous_keys if actions.get(key) is not False]
    checks = [
        check("巡检脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr.strip()}),
        check("257巡检包存在", latest.exists(), str(latest)),
        check("巡检总体通过", report.get("总体状态") == "pass", report.get("总体状态")),
        check("巡检项数量充足", len(report.get("巡检结果", [])) >= 12, len(report.get("巡检结果", []))),
        check("巡检失败数为0", report.get("失败") == 0, report.get("失败")),
        check("仍有真实发送阻断项", any("真实" in str(item) or "闸口" in str(item) for item in report.get("当前阻断项", [])), report.get("当前阻断项", [])),
        check("危险动作全部关闭", not dangerous, dangerous),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "巡检包": str(latest),
    }
    log_dir = root / "04日志" / "主动推送灰度链路一键只读巡检包"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = log_dir / f"stock-active-push-gray-chain-one-click-readonly-patrol-verify-{stamp}.json"
    latest_json = log_dir / "stock-active-push-gray-chain-one-click-readonly-patrol-verify-最新.json"
    output_md = log_dir / f"stock-active-push-gray-chain-one-click-readonly-patrol-verify-{stamp}.md"
    latest_md = log_dir / "stock-active-push-gray-chain-one-click-readonly-patrol-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
