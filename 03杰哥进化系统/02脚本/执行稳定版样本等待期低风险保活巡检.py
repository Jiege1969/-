# -*- coding: utf-8 -*-
"""执行稳定版样本等待期低风险保活巡检。

用于真实自然日样本未到点时的低风险巡检；不新增三日样本，不触发外部系统。
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
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "100稳定版样本等待期低风险保活巡检包"
LATEST_JSON = OUTPUT_DIR / "稳定版样本等待期低风险保活巡检执行结果_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版样本等待期低风险保活巡检执行结果_最新.md"

GATE_JSON = EVOLUTION_ROOT / "03数据" / "99稳定版次日自然日样本待办与防重复闸口包" / "自然日样本防重复闸口_最新.json"
FEEDBACK_RESULT_JSON = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账结果_最新.json"
SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"

TASKS = [
    ("WKP-001", "刷新次日样本防重复闸口", "生成稳定版次日自然日样本待办与防重复闸口包.py"),
    ("WKP-002", "扫描试运行反馈本地收件箱", "执行稳定版试运行反馈本地入账.py"),
    ("WKP-003", "刷新稳定版运行指挥台索引", "生成稳定交付版运行指挥台索引包.py"),
    ("WKP-004", "核对稳定版运行指挥台", "执行稳定交付版运行指挥台只读核对.py"),
    ("WKP-005", "刷新自主巡检快照", "生成日常可用版自主巡检快照.py"),
]

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
    "新增三日自然日样本": False,
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
            "# 稳定版样本等待期低风险保活巡检执行结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过任务：{report['汇总']['通过']}/{report['汇总']['总数']}",
            f"- 今天允许新增自然日样本：{report['等待期摘要'].get('今天是否允许新增自然日样本')}",
            f"- 仍缺自然日样本数：{report['等待期摘要'].get('仍缺自然日样本数')}",
            f"- 反馈需总管确认数：{report['等待期摘要'].get('反馈需总管确认数')}",
            "",
            "| ID | 名称 | 通过 | 返回码 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    results = [run_task(*task) for task in TASKS]
    failed = [item for item in results if not item["通过"]]
    gate = read_json(GATE_JSON)
    feedback = read_json(FEEDBACK_RESULT_JSON)
    snapshot = read_json(SNAPSHOT_JSON)
    summary = {
        "当前日期": gate.get("当前日期"),
        "下一最早采集日期": gate.get("下一最早采集日期"),
        "今天是否允许新增自然日样本": gate.get("今天是否允许新增自然日样本"),
        "仍缺自然日样本数": max(0, 3 - len(gate.get("通过样本日期", []))),
        "反馈扫描文件数": feedback.get("扫描文件数") or feedback.get("鎵弿鏂囦欢鏁?") or 0,
        "反馈接收数": feedback.get("接收数") or feedback.get("鎺ユ敹鏁?") or 0,
        "反馈拒收数": feedback.get("拒收数") or feedback.get("鎷掓敹鏁?") or 0,
        "反馈需总管确认数": feedback.get("需总管确认数") or feedback.get("闇€鎬荤纭鏁?") or 0,
        "自主巡检状态": snapshot.get("总体状态") or snapshot.get("鎬讳綋鐘舵€?"),
    }
    report = {
        "名称": "稳定版样本等待期低风险保活巡检执行结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "汇总": {"总数": len(results), "通过": len(results) - len(failed), "失败": len(failed)},
        "任务结果": results,
        "等待期摘要": summary,
        "安全边界": SAFETY_BOUNDARY,
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["汇总"]["通过"], "失败": report["汇总"]["失败"], "今天是否允许新增自然日样本": summary["今天是否允许新增自然日样本"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
