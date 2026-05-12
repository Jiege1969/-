# -*- coding: utf-8 -*-
"""
名称：记录单条复盘结果.py
作用：按任务ID把一条人工复盘结果写入107复盘结果填写模板，并可自动应用为107派生复盘结果文件。
触发方式：python 记录单条复盘结果.py --task-id sh603986-T+1 --status 已复盘 --conclusion 验证有效 --person 杰哥
依赖：Python标准库；300只候选复盘结果填写规则.json；300只候选复盘结果填写模板_最新.json；应用300只候选复盘结果填写模板.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只更新107复盘结果填写模板并生成107派生文件；不覆盖106原始任务包；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建单条复盘结果录入脚本。
标识：stock-trial-pool-300-review-result-single-record
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
    parser.add_argument("--task-id", required=True, help="任务ID，例如 sh603986-T+1")
    parser.add_argument("--status", required=True, choices=["待执行", "已复盘", "继续观察", "无法复盘"], help="执行状态")
    parser.add_argument("--close", default="", help="复盘日收盘价")
    parser.add_argument("--day-change", default="", help="复盘日涨跌幅")
    parser.add_argument("--range-change", default="", help="区间涨跌幅")
    parser.add_argument("--turnover-change", default="", help="成交额变化")
    parser.add_argument("--technical-change", default="", help="技术形态变化")
    parser.add_argument("--new-risk", default="", help="新增公告财务行业风险")
    parser.add_argument("--basis-verified", default="", help="是否验证原候选依据")
    parser.add_argument("--risk-realized", default="", help="是否兑现原风险点")
    parser.add_argument("--conclusion", default="", choices=["", "验证有效", "部分验证", "验证失败", "样本不足", "继续观察"], help="复盘结论")
    parser.add_argument("--tag", default="", help="经验提炼标签")
    parser.add_argument("--person", default="", help="复盘人")
    parser.add_argument("--time", default="", help="复盘时间，默认当前时间")
    parser.add_argument("--note", default="", help="备注")
    parser.add_argument("--no-apply", action="store_true", help="只更新模板，不自动应用派生文件")
    args = parser.parse_args()

    root = module_root()
    rule = load_json(root / "01配置" / "300只候选复盘结果填写规则.json")
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
    target["执行状态"] = args.status
    target["复盘日收盘价"] = args.close
    target["复盘日涨跌幅"] = args.day_change
    target["区间涨跌幅"] = args.range_change
    target["成交额变化"] = args.turnover_change
    target["技术形态变化"] = args.technical_change
    target["新增公告财务行业风险"] = args.new_risk
    target["是否验证原候选依据"] = args.basis_verified
    target["是否兑现原风险点"] = args.risk_realized
    target["复盘结论"] = args.conclusion
    target["经验提炼标签"] = args.tag
    target["复盘人"] = args.person
    target["复盘时间"] = args.time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target["备注"] = args.note
    template["最后修改时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template["最后修改任务ID"] = args.task_id
    write_json(template_path, template)
    applied = False
    if not args.no_apply:
        applier = root / "02脚本" / "应用300只候选复盘结果填写模板.py"
        subprocess.run([sys.executable, str(applier)], cwd=str(root), check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        applied = True
    print(json.dumps({"任务ID": args.task_id, "执行状态": args.status, "模板": str(template_path), "是否已应用派生文件": applied}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
