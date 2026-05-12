# -*- coding: utf-8 -*-
"""
名称：运行300只候选人工核验后联动刷新.py
作用：在103人工核验结果填写后，顺序刷新101/102/104/105并生成联动刷新报告；不发送、不交易。
触发方式：python 运行300只候选人工核验后联动刷新.py
依赖：Python标准库；300只候选人工核验后联动刷新规则.json；101/102/104/105生成脚本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地生成脚本并写108报告；不修改103人工填写结果；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建人工核验后联动刷新脚本。
标识：stock-trial-pool-300-human-verification-refresh-chain
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    script = root / item["脚本"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    started = datetime.now()
    if not script.exists():
        return {
            "层级": item.get("层级"),
            "名称": item.get("名称"),
            "脚本": str(script),
            "返回码": 1,
            "是否成功": False,
            "输出": "",
            "错误": "脚本不存在",
            "耗时秒": 0
        }
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=180,
    )
    return {
        "层级": item.get("层级"),
        "名称": item.get("名称"),
        "脚本": str(script),
        "返回码": run.returncode,
        "是否成功": run.returncode == 0,
        "输出": run.stdout.strip(),
        "错误": run.stderr.strip(),
        "耗时秒": round((datetime.now() - started).total_seconds(), 2)
    }


def summarize_state(root: Path) -> dict[str, Any]:
    paths = {
        "101事件核验结果回填": root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json",
        "102精选推送草案": root / "03数据" / "102精选推送草案" / "300只候选精选推送草案_最新.json",
        "104精选推送人工确认回执": root / "03数据" / "104精选推送人工确认回执" / "300只候选精选推送人工确认回执_最新.json",
        "105真实发送前检查": root / "03数据" / "105真实发送前检查" / "300只候选真实发送前检查包_最新.json",
    }
    loaded = {name: load_json(path) for name, path in paths.items() if path.exists()}
    event = loaded.get("101事件核验结果回填", {})
    draft = loaded.get("102精选推送草案", {})
    confirm = loaded.get("104精选推送人工确认回执", {})
    precheck = loaded.get("105真实发送前检查", {})
    return {
        "101可进入精选推送草案数量": event.get("可进入精选推送草案数量", event.get("可进入数量", "未知")),
        "102入选草案数量": draft.get("入选草案数量", "未知"),
        "102暂缓数量": draft.get("暂缓数量", "未知"),
        "104是否允许进入真实发送前检查": confirm.get("真实发送前检查准入", {}).get("是否允许进入真实发送前检查", False),
        "105是否具备提交真实发送讨论资格": precheck.get("是否具备提交真实发送讨论资格", False),
        "105是否执行真实发送": precheck.get("是否执行真实发送", False),
        "105阻断原因": precheck.get("阻断原因", []),
        "最新文件": {name: str(path) for name, path in paths.items()}
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 300只候选人工核验后联动刷新报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 刷新是否全部成功：{report['刷新是否全部成功']}",
        f"- 是否执行真实发送：{report['是否执行真实发送']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 刷新顺序",
        "",
    ]
    for item in report.get("刷新结果", []):
        lines.append(f"- {item['层级']} {item['名称']}：成功={item['是否成功']}，返回码={item['返回码']}。")
    lines.extend(["", "## 最新状态摘要", ""])
    for key, value in report.get("最新状态摘要", {}).items():
        if key == "最新文件":
            continue
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验后联动刷新规则.json"
    rule = load_json(rule_path)
    refresh_results = [run_script(root, item) for item in rule.get("刷新顺序", [])]
    state = summarize_state(root)
    all_success = all(item["是否成功"] for item in refresh_results)
    real_send = state.get("105是否执行真实发送") is True
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "刷新结果": refresh_results,
        "刷新是否全部成功": all_success,
        "最新状态摘要": state,
        "是否执行真实发送": False,
        "当前结论": "联动刷新完成；当前仍未执行真实发送。" if all_success and not real_send else "联动刷新存在失败或异常，请查看刷新结果。",
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验后联动刷新报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新文件"]
    output_md = output_dir / f"300只候选人工核验后联动刷新报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["报告文件"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"刷新是否全部成功": all_success, "是否执行真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if all_success and not real_send else 1


if __name__ == "__main__":
    raise SystemExit(main())
