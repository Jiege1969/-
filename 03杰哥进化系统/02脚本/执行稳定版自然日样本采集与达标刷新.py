# -*- coding: utf-8 -*-
"""执行稳定版自然日样本采集与三日达标刷新。

只执行本地只读/本地台账刷新链路；不生成未来自然日样本，不触发外部系统。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "97稳定版自然日样本采集与达标刷新入口包"
LATEST_JSON = OUTPUT_DIR / "稳定版自然日样本采集与达标刷新执行结果_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版自然日样本采集与达标刷新执行结果_最新.md"


TASKS = [
    ("NSR-001", "刷新稳定版运行指挥台每日入口", "执行稳定交付版运行指挥台每日刷新入口.py"),
    ("NSR-002", "记录当前自然日三日巡检样本", "执行稳定候选三日巡检首日样本记录.py"),
    ("NSR-003", "刷新三日达标判定器", "生成稳定交付版三日达标判定器与样本采集标准包.py"),
    ("NSR-004", "核对三日达标判定器", "执行稳定交付版三日达标判定器只读核对.py"),
    ("NSR-005", "刷新运行指挥台索引", "生成稳定交付版运行指挥台索引包.py"),
    ("NSR-006", "核对运行指挥台只读状态", "执行稳定交付版运行指挥台只读核对.py"),
    ("NSR-007", "验收运行指挥台索引", "验证稳定交付版运行指挥台索引包.py"),
]

DECISION_JSON = EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定版三日达标判定结果_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "预生成未来自然日样本": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_task(task_id: str, name: str, script_name: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    script_path = SCRIPT_DIR / script_name
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "id": task_id,
        "名称": name,
        "脚本": str(script_path),
        "通过": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['名称']} | {item['通过']} | {item['returncode']} |"
        for item in report["任务结果"]
    ]
    return "\n".join(
        [
            "# 稳定版自然日样本采集与达标刷新执行结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 执行通过：{report['汇总']['通过']}/{report['汇总']['总数']}",
            f"- 运行灯号：{report['运行摘要'].get('运行灯号')}",
            f"- 三日达标：{report['运行摘要'].get('三日达标')}",
            f"- 仍缺自然日样本数：{report['运行摘要'].get('仍缺自然日样本数')}",
            "",
            "| ID | 名称 | 通过 | 返回码 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            *[f"- {key}={value}" for key, value in report["安全边界"].items()],
            "",
        ]
    )


def main() -> int:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = [run_task(*task) for task in TASKS]
    failed = [item for item in results if not item["通过"]]
    decision = read_json(DECISION_JSON)
    report = {
        "名称": "稳定版自然日样本采集与达标刷新执行结果",
        "生成时间": now_text,
        "总体状态": "pass" if not failed else "blocked",
        "汇总": {"总数": len(results), "通过": len(results) - len(failed), "失败": len(failed)},
        "任务结果": results,
        "运行摘要": {
            "当前日期": decision.get("当前日期"),
            "运行灯号": "green" if not failed else "blocked",
            "三日达标": decision.get("三日达标"),
            "不同自然日通过样本数": decision.get("不同自然日通过样本数"),
            "仍缺自然日样本数": decision.get("仍缺自然日样本数"),
            "下一自然日最早采集日期": decision.get("下一自然日最早采集日期"),
            "是否生成未来样本": decision.get("是否生成未来样本"),
        },
        "安全边界": SAFETY_BOUNDARY,
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["汇总"]["通过"], "失败": report["汇总"]["失败"], "三日达标": report["运行摘要"].get("三日达标"), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
