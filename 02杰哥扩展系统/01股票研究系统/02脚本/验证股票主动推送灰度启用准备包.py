# -*- coding: utf-8 -*-
"""
名称：验证股票主动推送灰度启用准备包.py
作用：验证股票主动推送灰度启用准备包是否可用，并确认真实发送、n8n、券商和交易仍关闭。
触发方式：python 验证股票主动推送灰度启用准备包.py
依赖：Python标准库；生成股票主动推送灰度启用准备包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取和写入本地验收日志；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易。
创建/修改记录：2026-05-09 创建股票主动推送灰度启用准备包验收脚本。
标识：stock-active-push-gray-enable-prep-verify
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
        "# 股票主动推送灰度启用准备包验收",
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
    generator = root / "02脚本" / "生成股票主动推送灰度启用准备包.py"
    completed = subprocess.run(
        [sys.executable, str(generator)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    latest = root / "03数据" / "247主动推送灰度启用准备包" / "股票主动推送灰度启用准备包_最新.json"
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
        "写正式规则",
        "修改总管面板",
        "修改一键接续包",
    ]
    dangerous = [key for key in dangerous_keys if actions.get(key) is not False]
    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr.strip()}),
        check("准备包存在", latest.exists(), str(latest)),
        check("可以推进准备工作", report.get("可以推进准备工作") is True, report.get("可以推进准备工作")),
        check("真实推送未立即放行", report.get("可以立即真实推送") is False, report.get("可以立即真实推送")),
        check("n8n自动推送未立即放行", report.get("可以立即启用n8n自动推送") is False, report.get("可以立即启用n8n自动推送")),
        check("企业微信受控发送闸口未放行真实发送", report.get("受控发送闸口是否允许真实发送") is False, report.get("受控发送闸口是否允许真实发送")),
        check("灰度路径完整", len(report.get("灰度路径", [])) >= 6, len(report.get("灰度路径", []))),
        check("仍需补齐项完整", len(report.get("仍需补齐", [])) >= 5, len(report.get("仍需补齐", []))),
        check("危险动作全部关闭", not dangerous, dangerous),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "准备包": str(latest),
    }
    log_dir = root / "04日志" / "主动推送灰度启用准备包"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = log_dir / f"stock-active-push-gray-enable-prep-verify-{stamp}.json"
    latest_json = log_dir / "stock-active-push-gray-enable-prep-verify-最新.json"
    output_md = log_dir / f"stock-active-push-gray-enable-prep-verify-{stamp}.md"
    latest_md = log_dir / "stock-active-push-gray-enable-prep-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
