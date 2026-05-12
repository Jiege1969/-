# -*- coding: utf-8 -*-
"""生成稳定版试运行反馈入账执行器样例验收包。

样例验收只测试入账分类逻辑，不向正式待入账目录写入假反馈。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "93稳定版试运行反馈入账执行器样例验收包"

LATEST_JSON = OUTPUT_DIR / "稳定版试运行反馈入账执行器样例验收包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版试运行反馈入账执行器样例验收包_最新.md"
SAMPLES_JSON = OUTPUT_DIR / "稳定版试运行反馈入账样例_最新.json"

EXECUTOR_SCRIPT = EVOLUTION_ROOT / "02脚本" / "执行稳定版试运行反馈本地入账.py"


SAFETY_BOUNDARY = {
    "写入正式待入账目录": False,
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "重载19310": False,
    "重载19302": False,
}


VALID_SAMPLE = {
    "回传日期": "2026-05-08",
    "使用入口": "稳定版运行指挥台",
    "业务域": "公共接入",
    "用户原始输入": "试运行普通反馈样例",
    "系统返回摘要": "本地只读预演返回正常",
    "期望结果": "继续观察",
    "实际结果": "继续观察",
    "是否影响日常使用": False,
    "是否疑似红线": False,
    "复现步骤": "只读样例，不真实执行",
    "相关截图或文件路径": "",
    "建议处理级别": "P2",
}


RED_LINE_SAMPLE = {
    **VALID_SAMPLE,
    "用户原始输入": "试运行红线反馈样例",
    "是否疑似红线": True,
    "建议处理级别": "P2",
}


INVALID_SAMPLE = {
    "回传日期": "2026-05-08",
    "业务域": "股票",
    "是否疑似红线": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版试运行反馈入账执行器样例验收包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 样例数：{report['指标']['样例数']}",
            "",
            "## 样例目标",
            "",
            "- 普通反馈应被接收为 P2，且不需要总管确认。",
            "- 红线反馈应被接收并强制为 P0，且需要总管确认。",
            "- 缺字段反馈应被拒收。",
            "- 样例验收不写入正式待入账目录。",
            "",
        ]
    )


def main() -> int:
    samples = {
        "普通反馈样例": VALID_SAMPLE,
        "红线反馈样例": RED_LINE_SAMPLE,
        "缺字段反馈样例": INVALID_SAMPLE,
    }
    report = {
        "名称": "稳定版试运行反馈入账执行器样例验收包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_trial_feedback_intake_executor_sample_acceptance_ready",
        "执行器脚本": str(EXECUTOR_SCRIPT),
        "样例文件": str(SAMPLES_JSON),
        "指标": {"样例数": len(samples), "安全边界关闭项": len(SAFETY_BOUNDARY)},
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "样例JSON": str(SAMPLES_JSON),
        },
    }
    write_json(SAMPLES_JSON, samples)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "样例数": len(samples), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
