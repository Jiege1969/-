# -*- coding: utf-8 -*-
"""
名称：运行300候选核验流水线.py
作用：统一串联300只候选人工核验任务、人工填写等待、推送前检查包。
安全边界：只运行本地已有脚本并写流水线状态；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(root: Path, name: str, timeout: int = 300) -> dict[str, Any]:
    script = root / "02脚本" / name
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, "-B", str(script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout,
    )
    return {
        "脚本": name,
        "返回码": completed.returncode,
        "是否通过": completed.returncode == 0,
        "标准输出": (completed.stdout or "").strip()[-1000:],
        "标准错误": (completed.stderr or "").strip()[-1000:],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 300候选核验流水线状态 - {report['生成时间']}",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 是否等待人工填写：{report['是否等待人工填写']}",
        f"- 是否已生成推送前检查包：{report['是否已生成推送前检查包']}",
        "",
        "## 运行步骤",
        "",
    ]
    for item in report["运行步骤"]:
        lines.append(f"- {'通过' if item['是否通过'] else '失败'}：{item['脚本']}")
        if item.get("标准输出"):
            lines.append(f"  - 输出：{item['标准输出']}")
        if item.get("标准错误"):
            lines.append(f"  - 错误：{item['标准错误']}")
    lines.extend([
        "",
        "## 人工提示",
        "",
        f"- {report['人工提示']}",
        "",
        "## 安全边界",
        "",
        "- 未触发n8n，未真实发送企业微信，未接券商，未交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    steps: list[dict[str, Any]] = []
    prepare_scripts = [
        "生成300只候选公告财务行业事件正文核验任务.py",
        "生成300只候选人工核验任务优先级清单.py",
        "生成300只候选人工核验结果填写模板.py",
        "生成300只候选人工核验填写结果完整性闸口报告.py",
    ]
    for script in prepare_scripts:
        result = run_script(root, script)
        steps.append(result)
        if not result["是否通过"]:
            break

    completeness_path = root / "03数据" / "117人工核验完整性闸口" / "300只候选人工核验填写结果完整性闸口报告_最新.json"
    completeness = load_json(completeness_path, {})
    allow = bool(completeness.get("闸口结论", {}).get("是否允许刷新101/102放行"))
    current_status = "等待人工填写"
    human_tip = "请补齐103人工核验结果填写；下次运行本流水线会自动继续。"
    precheck_done = False

    if steps and all(item["是否通过"] for item in steps) and allow:
        current_status = "人工填写已满足，生成推送前检查包"
        human_tip = "人工填写已满足最低放行条件，流水线已继续生成推送前检查包。"
        post_scripts = [
            "生成300只候选精选推送草案.py",
            "生成300只候选推送前人工闸口复核单.py",
            "生成300只候选精选推送人工确认回执.py",
            "生成300只候选真实发送前检查包.py",
        ]
        for script in post_scripts:
            result = run_script(root, script)
            steps.append(result)
            if not result["是否通过"]:
                current_status = "推送前检查包生成存在失败"
                break
        precheck_done = all(item["是否通过"] for item in steps) and (root / "03数据" / "105真实发送前检查" / "300只候选真实发送前检查包_最新.json").exists()
    elif any(not item["是否通过"] for item in steps):
        current_status = "流水线脚本失败"
        human_tip = "请先查看失败脚本标准错误，修复后重新运行流水线。"

    report = {
        "名称": "300核验流水线状态",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前状态": current_status,
        "是否等待人工填写": current_status == "等待人工填写",
        "是否已生成推送前检查包": precheck_done,
        "完整性闸口": str(completeness_path),
        "闸口结论": completeness.get("闸口结论", {}),
        "人工提示": human_tip,
        "运行步骤": steps,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    out_dir = root / "03数据" / "300候选核验流水线"
    latest_json = out_dir / "300核验流水线状态_最新.json"
    latest_md = out_dir / "300核验流水线状态_最新.md"
    write_json(out_dir / f"300核验流水线状态_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(out_dir / f"300核验流水线状态_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"当前状态": current_status, "是否等待人工填写": report["是否等待人工填写"], "状态文件": str(latest_json)}, ensure_ascii=False))
    return 0 if current_status != "流水线脚本失败" else 1


if __name__ == "__main__":
    raise SystemExit(main())
