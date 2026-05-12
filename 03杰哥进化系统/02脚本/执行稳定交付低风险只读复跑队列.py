# -*- coding: utf-8 -*-
"""执行稳定交付低风险只读复跑队列。

只执行队列中“允许自动复跑=True”的只读/候选验收任务；不执行低风险续建修复，不重载服务。
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
QUEUE_JSON = EVOLUTION_ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包" / "异常复跑队列_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包"
LATEST_JSON = OUTPUT_DIR / "稳定交付低风险只读复跑结果_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定交付低风险只读复跑结果_最新.md"


def run_item(item: dict[str, Any]) -> dict[str, Any]:
    script = Path(item["脚本"])
    if not script.exists():
        return {
            "编号": item["编号"],
            "名称": item["名称"],
            "执行": False,
            "通过": False,
            "返回码": None,
            "错误": "脚本不存在",
            "脚本": str(script),
        }
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=item["工作目录"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    return {
        "编号": item["编号"],
        "名称": item["名称"],
        "执行": True,
        "通过": result.returncode == 0,
        "返回码": result.returncode,
        "脚本": str(script),
        "输出验收": item.get("输出验收"),
        "stdout": result.stdout.strip()[-2500:],
        "stderr": result.stderr.strip()[-2500:],
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['名称']} | {'pass' if item['通过'] else 'fail'} | {item['返回码']} |"
        for item in report["复跑结果"]
    ]
    return "\n".join(
        [
            "# 稳定交付低风险只读复跑结果",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
            "",
            "| 编号 | 名称 | 结果 | 返回码 |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 只执行允许自动复跑的只读/候选验收脚本。",
            "- 不执行低风险续建修复，不重载 19310/19302，不触发真实外部系统。",
        ]
    )


def main() -> int:
    queue = json.loads(QUEUE_JSON.read_text(encoding="utf-8-sig"))
    runnable = [item for item in queue if item.get("允许自动复跑") is True]
    results = [run_item(item) for item in runnable]
    passed = sum(1 for item in results if item["通过"])
    report = {
        "名称": "稳定交付低风险只读复跑结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed == len(results) else "blocked",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "复跑结果": results,
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "自动转正式规则": False,
            "修改运行配置": False,
            "重载19310": False,
            "重载19302": False,
            "请求19302业务接口": False,
        },
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
