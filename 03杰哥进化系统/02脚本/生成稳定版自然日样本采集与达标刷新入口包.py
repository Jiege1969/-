# -*- coding: utf-8 -*-
"""生成稳定版自然日样本采集与达标刷新入口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SCRIPT_DIR = EVOLUTION_ROOT / "02脚本"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "97稳定版自然日样本采集与达标刷新入口包"
LATEST_JSON = OUTPUT_DIR / "稳定版自然日样本采集与达标刷新入口包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版自然日样本采集与达标刷新入口包_最新.md"
RUN_SCRIPT = SCRIPT_DIR / "执行稳定版自然日样本采集与达标刷新.py"
RUN_RESULT = OUTPUT_DIR / "稳定版自然日样本采集与达标刷新执行结果_最新.json"


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


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    rows = [f"| {item['顺序']} | {item['动作']} | {item['脚本或产物']} |" for item in report["执行链路"]]
    return "\n".join(
        [
            "# 稳定版自然日样本采集与达标刷新入口包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            "- 用途：把每日稳定版刷新、当前自然日样本记录、三日达标判定和运行指挥台刷新收成一个可执行入口。",
            "",
            "## 执行命令",
            "",
            f'```powershell\npython "{RUN_SCRIPT}"\n```',
            "",
            "## 执行链路",
            "",
            "| 顺序 | 动作 | 脚本或产物 |",
            "| --- | --- | --- |",
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
    report = {
        "名称": "稳定版自然日样本采集与达标刷新入口包",
        "生成时间": now_text,
        "状态": "stable_natural_day_sample_refresh_entry_ready",
        "执行命令": f'python "{RUN_SCRIPT}"',
        "执行链路": [
            {"顺序": 1, "动作": "刷新稳定版运行指挥台每日入口", "脚本或产物": str(SCRIPT_DIR / "执行稳定交付版运行指挥台每日刷新入口.py")},
            {"顺序": 2, "动作": "记录当前自然日三日巡检样本", "脚本或产物": str(SCRIPT_DIR / "执行稳定候选三日巡检首日样本记录.py")},
            {"顺序": 3, "动作": "刷新三日达标判定器", "脚本或产物": str(SCRIPT_DIR / "生成稳定交付版三日达标判定器与样本采集标准包.py")},
            {"顺序": 4, "动作": "核对三日达标判定器", "脚本或产物": str(SCRIPT_DIR / "执行稳定交付版三日达标判定器只读核对.py")},
            {"顺序": 5, "动作": "刷新并验收运行指挥台", "脚本或产物": str(SCRIPT_DIR / "验证稳定交付版运行指挥台索引包.py")},
            {"顺序": 6, "动作": "输出本次执行结果", "脚本或产物": str(RUN_RESULT)},
        ],
        "约束": [
            "同一自然日重复运行只覆盖当日样本，不增加虚假样本数",
            "不生成未来自然日样本",
            "三日达标必须来自三个不同自然日的 pass 样本",
            "任何红线动作均保持 false",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {"总包JSON": str(LATEST_JSON), "总包Markdown": str(LATEST_MD), "执行结果": str(RUN_RESULT)},
    }
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
