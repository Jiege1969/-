# -*- coding: utf-8 -*-
"""
名称：记录单条人工核验结果.py
作用：按任务ID把一条人工核验结果写入103人工核验结果填写模板，并自动应用为103派生任务文件。
触发方式：python 记录单条人工核验结果.py --task-id sh603986-01 --status 通过 --person 杰哥 --title "公告标题" --date 2026-04-30 --major-risk 否 --support-draft 是 --note "人工核验通过"
依赖：Python标准库；300只候选人工核验结果填写规则.json；300只候选人工核验结果填写模板_最新.json；应用300只候选人工核验结果填写模板.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只更新103人工填写模板并生成103派生任务文件；不覆盖100原始核验任务；不覆盖101回填包；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建单条人工核验结果录入脚本。
标识：stock-trial-pool-300-human-verification-single-record
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True, help="任务ID，例如 sh603986-01")
    parser.add_argument("--status", required=True, choices=["待人工核验", "通过", "继续待核实", "阻断"], help="核验状态")
    parser.add_argument("--person", default="", help="核验人")
    parser.add_argument("--time", default="", help="核验时间，默认当前时间")
    parser.add_argument("--title", default="", help="材料标题")
    parser.add_argument("--date", default="", help="材料发布日期，建议YYYY-MM-DD")
    parser.add_argument("--major-risk", default="", choices=["", "是", "否", "待核实"], help="是否发现新增重大风险")
    parser.add_argument("--support-draft", default="", choices=["", "是", "否", "待核实"], help="是否支持进入精选推送草案")
    parser.add_argument("--note", default="", help="备注")
    parser.add_argument("--no-apply", action="store_true", help="只更新模板，不自动应用派生任务文件")
    args = parser.parse_args()

    root = module_root()
    rule = load_json(root / "01配置" / "300只候选人工核验结果填写规则.json")
    template_path = root / rule["输出"]["数据目录"] / rule["输出"]["模板最新文件"]
    template = load_json(template_path)
    target = None
    for row in template.get("填写区", []):
        if str(row.get("任务ID")) == args.task_id:
            target = row
            break
    if target is None:
        print(json.dumps({"错误": "任务ID不存在", "任务ID": args.task_id}, ensure_ascii=False))
        return 1

    target["状态"] = args.status
    target["核验人"] = args.person
    target["核验时间"] = args.time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target["材料标题"] = args.title
    target["材料发布日期"] = args.date
    target["是否发现新增重大风险"] = args.major_risk
    target["是否支持进入精选推送草案"] = args.support_draft
    target["备注"] = args.note
    template["最后修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template["最后修改任务ID"] = args.task_id
    write_json(template_path, template)

    applied = False
    if not args.no_apply:
        applier = root / "02脚本" / "应用300只候选人工核验结果填写模板.py"
        subprocess.run([sys.executable, str(applier)], cwd=str(root), check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        applied = True

    print(json.dumps({
        "任务ID": args.task_id,
        "状态": args.status,
        "模板": str(template_path),
        "是否已应用派生任务文件": applied
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
