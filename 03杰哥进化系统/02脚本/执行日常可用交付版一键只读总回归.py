# -*- coding: utf-8 -*-
"""执行日常可用交付版一键只读总回归。

安全边界：只运行已验收的只读/候选/阻断检查脚本；不重载服务，不请求19302业务接口，
不真实发送企业微信，不触发n8n，不接券商，不交易，不登录税局，不接财税软件，不真实渲染或发布视频。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "44日常可用交付版一键只读总回归"
LATEST_JSON = OUTPUT_DIR / "日常可用交付版一键只读总回归_最新.json"
LATEST_MD = OUTPUT_DIR / "日常可用交付版一键只读总回归_最新.md"


TASKS = [
    {
        "id": "DUR-001",
        "name": "企业微信公共入口日常巡检",
        "script": ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "02脚本" / "执行企业微信公共接入层日常只读巡检.py",
        "cwd": ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置",
        "category": "wecom",
    },
    {
        "id": "DUR-002",
        "name": "股票展示口径一致性",
        "script": ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证股票展示口径一致性.py",
        "cwd": ROOT / "02杰哥扩展系统" / "01股票研究系统",
        "category": "stock",
    },
    {
        "id": "DUR-003",
        "name": "股票第九批影子验收",
        "script": ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证股票线第九批统一影子验收总表.py",
        "cwd": ROOT / "02杰哥扩展系统" / "01股票研究系统",
        "category": "stock",
    },
    {
        "id": "DUR-004",
        "name": "视频制作系统状态摘要验收",
        "script": ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "验证视频制作系统状态摘要.py",
        "cwd": ROOT / "02杰哥扩展系统" / "02视频制作系统",
        "category": "video",
    },
    {
        "id": "DUR-005",
        "name": "视频真实渲染禁用态检查",
        "script": ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "执行视频真实渲染禁用态检查.py",
        "cwd": ROOT / "02杰哥扩展系统" / "02视频制作系统",
        "category": "video",
    },
    {
        "id": "DUR-006",
        "name": "视频P0人工回执影子样例验收",
        "script": ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "验证视频P0人工回执影子样例.py",
        "cwd": ROOT / "02杰哥扩展系统" / "02视频制作系统",
        "category": "video",
    },
    {
        "id": "DUR-007",
        "name": "视频任务ID与放行链一致性复核卡",
        "script": ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "生成视频任务ID与放行链一致性复核卡.py",
        "cwd": ROOT / "02杰哥扩展系统" / "02视频制作系统",
        "category": "video",
    },
    {
        "id": "DUR-008",
        "name": "阶段性多业务联调封版候选验收",
        "script": EVOLUTION_ROOT / "02脚本" / "验证阶段性多业务联调通过封版候选.py",
        "cwd": EVOLUTION_ROOT,
        "category": "evolution",
    },
    {
        "id": "DUR-009",
        "name": "阶段性封版候选回归建议拆单验收",
        "script": EVOLUTION_ROOT / "02脚本" / "验证阶段性封版候选回归建议拆单.py",
        "cwd": EVOLUTION_ROOT,
        "category": "evolution",
    },
    {
        "id": "DUR-010",
        "name": "日常可用交付版状态包生成",
        "script": EVOLUTION_ROOT / "02脚本" / "生成日常可用交付版状态包.py",
        "cwd": EVOLUTION_ROOT,
        "category": "evolution",
    },
    {
        "id": "DUR-011",
        "name": "日常可用交付版状态包验收",
        "script": EVOLUTION_ROOT / "02脚本" / "验证日常可用交付版状态包.py",
        "cwd": EVOLUTION_ROOT,
        "category": "evolution",
    },
]


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    script = Path(task["script"])
    if not script.exists():
        return {**task, "script": str(script), "passed": False, "returncode": None, "stdout": "", "stderr": "script missing"}
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(task["cwd"]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    return {
        "id": task["id"],
        "name": task["name"],
        "category": task["category"],
        "script": str(script),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout.strip()[-3000:],
        "stderr": result.stderr.strip()[-3000:],
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['name']} | {item['category']} | {'pass' if item['passed'] else 'fail'} | {item['returncode']} |"
        for item in report["任务结果"]
    ]
    return "\n".join(
        [
            "# 日常可用交付版一键只读总回归",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| ID | 名称 | 分类 | 结果 | 返回码 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 不重载19310/19302，不请求19302业务接口。",
            "- 不真实发送企业微信，不触发n8n。",
            "- 不接券商、不交易，不登录电子税务局、不接财税软件。",
            "- 不真实渲染视频，不自动发布视频。",
            "- 不写正式规则，不修改总管面板，不修改一键接续包。",
        ]
    )


def main() -> int:
    results = [run_task(task) for task in TASKS]
    passed = sum(1 for item in results if item["passed"])
    report = {
        "名称": "日常可用交付版一键只读总回归",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed == len(results) else "blocked",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "任务结果": results,
        "安全边界": {
            "重载19310": False,
            "重载19302": False,
            "请求19302业务接口": False,
            "真实发送企业微信": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式规则": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_markdown(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
