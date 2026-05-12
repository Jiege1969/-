# -*- coding: utf-8 -*-
"""
名称：验证股票主动推送真实灰度发送前最终只读总闸口.py
作用：验证股票主动推送真实灰度发送前最终只读总闸口是否正确阻断真实发送。
触发方式：python 验证股票主动推送真实灰度发送前最终只读总闸口.py
依赖：Python标准库；生成股票主动推送真实灰度发送前最终只读总闸口.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地总闸口并写验收日志；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易。
创建/修改记录：2026-05-09 创建股票主动推送真实灰度发送前最终只读总闸口验收脚本。
标识：stock-active-push-real-gray-final-readonly-gate-verify
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
        "# 股票主动推送真实灰度发送前最终只读总闸口验收",
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
    generator = root / "02脚本" / "生成股票主动推送真实灰度发送前最终只读总闸口.py"
    completed = subprocess.run(
        [sys.executable, str(generator)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = root / "03数据" / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous_keys = [
        "调用企业微信API",
        "真实发送企业微信",
        "启用n8n",
        "触发n8n",
        "重载19310",
        "重载19302",
        "调用券商接口",
        "自动交易",
        "写正式规则库",
        "修改总管面板",
        "修改一键接续包",
    ]
    dangerous = [key for key in dangerous_keys if actions.get(key) is not False]
    sub_status = report.get("子包状态", [])
    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr.strip()}),
        check("总闸口存在", latest.exists(), str(latest)),
        check("总闸口保持blocked", report.get("总体状态") == "blocked", report.get("总体状态")),
        check("真实发送未放行", report.get("是否允许真实发送") is False, report.get("是否允许真实发送")),
        check("n8n自动推送未放行", report.get("是否允许n8n自动推送") is False, report.get("是否允许n8n自动推送")),
        check("247-251子包均存在", len(sub_status) == 5 and all(item.get("存在") for item in sub_status), sub_status),
        check("247-251子包判定均通过", len(sub_status) == 5 and all(item.get("判定") == "pass" for item in sub_status), sub_status),
        check("阻断项存在", len(report.get("阻断项", [])) >= 1, report.get("阻断项", [])),
        check("人工前置确认完整", len(report.get("人工前置确认", [])) >= 7, report.get("人工前置确认", [])),
        check("危险动作全部关闭", not dangerous, dangerous),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "总闸口": str(latest),
    }
    log_dir = root / "04日志" / "主动推送真实灰度发送前最终只读总闸口"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = log_dir / f"stock-active-push-real-gray-final-readonly-gate-verify-{stamp}.json"
    latest_json = log_dir / "stock-active-push-real-gray-final-readonly-gate-verify-最新.json"
    output_md = log_dir / f"stock-active-push-real-gray-final-readonly-gate-verify-{stamp}.md"
    latest_md = log_dir / "stock-active-push-real-gray-final-readonly-gate-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
