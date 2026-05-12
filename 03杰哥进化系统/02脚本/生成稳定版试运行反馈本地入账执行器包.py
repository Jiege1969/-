# -*- coding: utf-8 -*-
"""生成稳定版试运行反馈本地入账执行器包。

执行器只读取本地待入账回传 JSON，做字段校验、分级和候选台账预入账。
不写正式规则，不触发外部系统，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包"
INBOX_DIR = OUTPUT_DIR / "待入账回传"

LATEST_JSON = OUTPUT_DIR / "稳定版试运行反馈本地入账执行器包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版试运行反馈本地入账执行器包_最新.md"
INBOX_README = INBOX_DIR / "README_放入试运行问题回传JSON.md"


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
}


REQUIRED_FIELDS = [
    "回传日期",
    "使用入口",
    "业务域",
    "用户原始输入",
    "系统返回摘要",
    "期望结果",
    "实际结果",
    "是否影响日常使用",
    "是否疑似红线",
    "复现步骤",
    "相关截图或文件路径",
    "建议处理级别",
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_inbox_readme() -> str:
    return "\n".join(
        [
            "# 待入账回传目录",
            "",
            "把稳定版试运行问题回传 JSON 放到本目录。",
            "",
            "要求：",
            "",
            *[f"- {field}" for field in REQUIRED_FIELDS],
            "",
            "执行器只做本地入账预演：不发送、不触发、不交易、不登录、不渲染、不发布、不写正式规则。",
            "",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版试运行反馈本地入账执行器包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 待入账目录：{report['待入账目录']}",
            f"- 必填字段数：{report['指标']['必填字段数']}",
            "",
            "## 执行入口",
            "",
            f"```powershell\npython \"{report['执行入口']}\"\n```",
            "",
            "## 验收入口",
            "",
            f"```powershell\npython \"{report['验收入口']}\"\n```",
            "",
        ]
    )


def main() -> int:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "名称": "稳定版试运行反馈本地入账执行器包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_trial_feedback_local_intake_executor_ready",
        "待入账目录": str(INBOX_DIR),
        "必填字段": REQUIRED_FIELDS,
        "执行入口": str(EVOLUTION_ROOT / "02脚本" / "执行稳定版试运行反馈本地入账.py"),
        "验收入口": str(EVOLUTION_ROOT / "02脚本" / "验证稳定版试运行反馈本地入账执行器包.py"),
        "指标": {"必填字段数": len(REQUIRED_FIELDS), "安全边界关闭项": len(SAFETY_BOUNDARY)},
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "待入账目录说明": str(INBOX_README),
        },
    }
    write_text(INBOX_README, build_inbox_readme())
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "待入账目录": str(INBOX_DIR), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
