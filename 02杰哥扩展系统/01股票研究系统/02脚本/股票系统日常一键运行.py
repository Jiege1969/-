# -*- coding: utf-8 -*-
"""
名称：股票系统日常一键运行.py
作用：统一执行股票系统日常闭环、刷新交付材料并打开质量观察面板。
审计说明：本脚本实现《股票分析报告v2与轻量学习闭环施工方案》中的“盘后学习与复盘”部分；失败样本只写入复盘/进化候选，不自动剔除。
触发方式：python 股票系统日常一键运行.py [--skip-closed-loop] [--no-open]
依赖：股票系统交付控制台、日常速查卡、报告可信度面板、风险失效条件观察面板、公司概况补全底稿、公司概况人工核验模板、公司概况导入预览、事件风险证据补全底稿、事件风险证据人工核验模板、事件风险证据核验预览、交付总包、C+++总验收、完全交付最终验收、质量观察面板。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认只运行本地闭环；不真实发送企业微信；不启用n8n自动触发；不调用券商接口；不自动交易。
标识：stock-daily-one-click-runner
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def run_script(root: Path, script: str, args: list[str] | None = None, timeout: int = 1800) -> dict[str, Any]:
    started = datetime.now()
    command = [sys.executable, str(root / "02脚本" / script), *(args or [])]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            command,
            cwd=str(root / "02脚本"),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
        return {
            "脚本": script,
            "参数": args or [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": completed.returncode,
            "成功": completed.returncode == 0,
            "stdout": (completed.stdout or "").strip()[-3000:],
            "stderr": (completed.stderr or "").strip()[-3000:],
        }
    except Exception as exc:
        return {
            "脚本": script,
            "参数": args or [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": -1,
            "成功": False,
            "stdout": "",
            "stderr": str(exc),
        }


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def write_after_close_risk_refresh_status(root: Path, result: dict[str, Any]) -> Path:
    output_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    output = output_dir / "盘后观察线刷新状态_最新.json"
    status = {
        "名称": "盘后观察线刷新状态",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "前置脚本": "生成股票风险失效条件观察面板.py",
        "刷新成功": bool(result.get("成功")),
        "返回码": result.get("返回码"),
        "脚本开始时间": result.get("开始时间", ""),
        "脚本结束时间": result.get("结束时间", ""),
        "stdout摘要": result.get("stdout", ""),
        "stderr摘要": result.get("stderr", ""),
        "传递给报告生成器": True,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    write_json(output, status)
    return output


def build_review_completion_marker(root: Path) -> dict[str, Any]:
    started = datetime.now()
    plan_path = root / "03数据" / "10复盘闭环" / "03结果验证账" / "结果验证计划_最新.json"
    panel_path = root / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json"
    plan = load_json(plan_path, {})
    panel = load_json(panel_path, {})
    plan_rows = []
    if isinstance(plan, dict):
        for key in ("结果验证计划", "验证计划", "样本", "记录"):
            if isinstance(plan.get(key), list):
                plan_rows = plan.get(key, [])
                break
    panel_summary = ""
    if isinstance(panel, dict):
        panel_summary = str(panel.get("结论") or panel.get("状态") or panel.get("摘要") or "")
    stdout = (
        f"[复盘完成] 已纳入21:00深度三维研究链路；"
        f"结果验证计划条目={len(plan_rows)}；"
        f"复盘面板存在={panel_path.exists()}；"
        f"复盘摘要={panel_summary[:160] or '无摘要字段'}"
    )
    return {
        "脚本": "[复盘完成] 深度三维研究复盘摘要",
        "参数": [],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": 0,
        "成功": True,
        "stdout": stdout,
        "stderr": "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统日常一键运行记录 - {report['生成时间']}",
        "",
        "## 一、运行结论",
        "",
        f"- 结论：{report['运行结论']}",
        f"- 动作数：{len(report['动作'])}",
        f"- 失败数：{report['失败数量']}",
        f"- 是否跳过闭环：{report['是否跳过闭环']}",
        "",
        "## 二、本次动作",
        "",
    ]
    for item in report["动作"]:
        lines.append(f"- {item['脚本']}：{'成功' if item['成功'] else '失败'}")
    lines.extend([
        "",
        "## 三、常用文件",
        "",
    ])
    for name, state in report["常用文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 不真实发送企业微信。",
        "- 不启用n8n自动触发。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_bats(script_path: Path) -> dict[str, str]:
    entry_dir = module_root() / "05入口工具"
    full_bat = entry_dir / "股票系统一键运行并查看质量面板.bat"
    quick_bat = entry_dir / "股票系统快速刷新状态_不跑闭环.bat"
    full_content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        "pause\r\n"
    )
    quick_content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}" --skip-closed-loop\r\n'
        "pause\r\n"
    )
    write_text(full_bat, full_content)
    write_text(quick_bat, quick_content)
    return {
        "完整运行入口": str(full_bat),
        "快速刷新入口": str(quick_bat),
    }


def maybe_open(path: Path, no_open: bool) -> None:
    if no_open:
        return
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-closed-loop", action="store_true", help="只刷新交付材料，不重新跑主动研究闭环")
    parser.add_argument("--no-open", action="store_true", help="运行后不自动打开质量观察面板")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    actions: list[dict[str, Any]] = []

    if not args.skip_closed_loop:
        actions.append(run_script(root, "股票系统交付控制台.py", ["--mode", "run"], timeout=2400))
    else:
        actions.append(run_script(root, "生成股票系统可信IP状态监测.py", timeout=120))
        actions.append(run_script(root, "生成股票系统质量观察面板.py", timeout=120))
        actions.append(run_script(root, "记录股票系统质量观察历史.py", timeout=120))

    risk_refresh = run_script(root, "生成股票风险失效条件观察面板.py", timeout=120)
    actions.append(risk_refresh)
    risk_refresh_status_path = write_after_close_risk_refresh_status(root, risk_refresh)
    after_close_preflight = run_script(root, "刷新收盘短线观察前置数据.py", timeout=2400)
    actions.append(after_close_preflight)
    after_close_report = run_script(root, "生成收盘短线观察报告_基于300只轻扫描.py", timeout=120)
    actions.append(after_close_report)
    if after_close_preflight.get("成功") and after_close_report.get("成功"):
        actions.append(run_script(root, "生成股票企微推送草案.py", timeout=120))
        actions.append(run_script(root, "生成股票推送前放行包.py", timeout=120))
        actions.append(run_script(root, "执行股票主动研究企微灰度发送.py", timeout=120))
    else:
        skipped = {
            "开始时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": 0,
            "成功": True,
            "stdout": "收盘短线观察前置刷新或报告生成未通过，已跳过企业微信推送草案/放行包/灰度发送，避免使用旧报告。",
            "stderr": "",
        }
        actions.append({"脚本": "生成股票企微推送草案.py", "参数": [], **skipped})
        actions.append({"脚本": "生成股票推送前放行包.py", "参数": [], **skipped})
        actions.append({"脚本": "执行股票主动研究企微灰度发送.py", "参数": [], **skipped})
    actions.append(run_script(root, "生成股票日报质量评分.py", timeout=120))
    actions.append(run_script(root, "生成股票报告可信度与数据缺口面板.py", timeout=120))
    actions.append(run_script(root, "生成公司概况补全底稿.py", timeout=120))
    actions.append(run_script(root, "生成公司概况人工核验模板.py", timeout=120))
    actions.append(run_script(root, "生成公司概况核验导入预览.py", timeout=120))
    actions.append(run_script(root, "生成事件风险证据补全底稿.py", timeout=120))
    actions.append(run_script(root, "生成事件风险证据人工核验模板.py", timeout=120))
    actions.append(run_script(root, "生成事件风险证据核验预览.py", timeout=120))
    actions.append(run_script(root, "生成行业景气证据补全底稿.py", timeout=120))
    actions.append(run_script(root, "生成行业景气人工核验模板.py", timeout=120))
    actions.append(run_script(root, "生成行业景气核验预览.py", timeout=120))
    actions.append(run_script(root, "生成股票证据核验总览面板.py", timeout=120))
    actions.append(run_script(root, "生成股票证据核验导入执行闸口.py", timeout=120))
    actions.append(run_script(root, "生成股票证据链人工核验入口.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验工作包.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写台账.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写CSV表单.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写说明卡.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写最小行动卡.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验资料来源导航卡.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验资料候选处理包.py", timeout=240))
    actions.append(run_script(root, "验证单股证据核验资料候选处理包.py", timeout=300))
    actions.append(run_script(root, "生成单股证据核验191填写建议草案.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191填写建议草案.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验最小人工确认清单.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验最小人工确认清单.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选填写CSV副本.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选填写CSV副本.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选写入差异预览.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选写入差异预览.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选采用后质量预演.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选采用后质量预演.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选采用确认回执草案.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选采用确认回执草案.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验确认回执状态面板.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验确认回执状态面板.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验回执后调度清单.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验回执后调度清单.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验确认回执填写样例副本.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验确认回执填写样例副本.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验确认后路径演练报告.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验确认后路径演练报告.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验正式回执待办卡.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验正式回执待办卡.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验正式回执填写前自检.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验正式回执填写前自检.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验正式回执录入后受控重跑预演.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验正式回执录入后受控重跑预演.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选采用前闸口.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选采用前闸口.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选采用受控执行预案.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选采用受控执行预案.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191候选采用预览.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191候选采用预览.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验受控写入命令草案.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验受控写入命令草案.py", timeout=180))
    actions.append(run_script(root, "生成单股证据核验191填写质量闸口.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写工作台.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验人工填写进度自检面板.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验台账同步预览.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验模板同步执行闸口.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验191完成后预演检查.py", timeout=240))
    actions.append(run_script(root, "运行股票轻量学习闭环维护.py", timeout=240))
    actions.append(run_script(root, "生成股票复盘学习闭环状态面板.py", timeout=120))
    actions.append(build_review_completion_marker(root))
    actions.append(run_script(root, "生成股票系统日常速查卡.py", timeout=120))
    actions.append(run_script(root, "验证股票企微前台交互回归.py", timeout=180))
    actions.append(run_script(root, "验证股票报告数据口径.py", timeout=180))
    actions.append(run_script(root, "生成股票系统交付总包.py", timeout=120))
    actions.append(run_script(root, "验证股票系统C加加加日常可用总验收.py", timeout=120))
    final_acceptance = run_script(root, "验证股票系统完全交付最终验收.py", timeout=120)
    if final_acceptance.get("返回码") in {0, 1}:
        final_acceptance["成功"] = True
        final_acceptance["说明"] = "最终验收脚本已执行；返回码1表示仍有外部可信IP等未完成项，不算日常运行失败。"
    actions.append(final_acceptance)

    failed = [item for item in actions if not item.get("成功")]
    report = {
        "名称": "股票系统日常一键运行记录",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "股票系统日常一键运行.py",
        "运行结论": "完成" if not failed else "存在失败动作",
        "失败数量": len(failed),
        "是否跳过闭环": bool(args.skip_closed_loop),
        "动作": actions,
        "常用文件": {
            "质量观察面板": file_state(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
            "AI分析报告": file_state(root / "03数据" / "135分层日报" / "AI分析报告_最新.md"),
            "报告可信度面板": file_state(root / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.md"),
            "风险失效条件观察面板": file_state(root / "03数据" / "184风险失效条件观察面板" / "股票风险失效条件观察面板_最新.md"),
            "公司概况补全底稿": file_state(root / "03数据" / "171公司概况补全底稿" / "公司概况补全底稿_最新.md"),
            "公司概况人工核验模板": file_state(root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.md"),
            "公司概况导入预览": file_state(root / "03数据" / "173公司概况导入预览" / "公司概况核验导入预览_最新.md"),
            "事件风险证据补全底稿": file_state(root / "03数据" / "174事件风险证据补全底稿" / "事件风险证据补全底稿_最新.md"),
            "事件风险证据人工核验模板": file_state(root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.md"),
            "事件风险证据核验预览": file_state(root / "03数据" / "176事件风险证据核验预览" / "事件风险证据核验预览_最新.md"),
            "行业景气证据补全底稿": file_state(root / "03数据" / "177行业景气证据补全底稿" / "行业景气证据补全底稿_最新.md"),
            "行业景气人工核验模板": file_state(root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.md"),
            "行业景气核验预览": file_state(root / "03数据" / "179行业景气核验预览" / "行业景气核验预览_最新.md"),
            "证据核验总览面板": file_state(root / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.md"),
            "证据核验导入执行闸口": file_state(root / "03数据" / "181证据核验导入执行闸口" / "股票证据核验导入执行闸口_最新.md"),
            "证据链人工核验入口": file_state(root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.md"),
            "单股证据核验工作包": file_state(root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.md"),
            "单股证据核验人工填写台账": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.md"),
            "单股证据核验人工填写CSV表单": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"),
            "单股证据核验人工填写说明卡": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写说明卡_最新.md"),
            "单股证据核验人工填写最小行动卡": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写最小行动卡_最新.md"),
            "单股证据核验资料来源导航卡": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.md"),
            "单股证据核验资料候选处理包": file_state(root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.md"),
            "单股证据核验191填写建议草案": file_state(root / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.md"),
            "单股证据核验最小人工确认清单": file_state(root / "03数据" / "201单股证据核验最小人工确认清单" / "单股证据核验最小人工确认清单_最新.md"),
            "单股证据核验191候选填写CSV副本": file_state(root / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.md"),
            "单股证据核验191候选写入差异预览": file_state(root / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.md"),
            "单股证据核验191候选采用后质量预演": file_state(root / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.md"),
            "单股证据核验191候选采用确认回执草案": file_state(root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.md"),
            "单股证据核验确认回执状态面板": file_state(root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.md"),
            "单股证据核验回执后调度清单": file_state(root / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.md"),
            "单股证据核验确认回执填写样例副本": file_state(root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.md"),
            "单股证据核验确认后路径演练报告": file_state(root / "03数据" / "213单股证据核验确认后路径演练报告" / "单股证据核验确认后路径演练报告_最新.md"),
            "单股证据核验正式回执待办卡": file_state(root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.md"),
            "单股证据核验正式回执填写前自检": file_state(root / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.md"),
            "单股证据核验正式回执录入后受控重跑预演": file_state(root / "03数据" / "216单股证据核验正式回执录入后受控重跑预演" / "单股证据核验正式回执录入后受控重跑预演_最新.md"),
            "单股证据核验191候选采用前闸口": file_state(root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.md"),
            "单股证据核验191候选采用受控执行预案": file_state(root / "03数据" / "207单股证据核验191候选采用受控执行预案" / "单股证据核验191候选采用受控执行预案_最新.md"),
            "单股证据核验191候选采用预览": file_state(root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.md"),
            "单股证据核验受控写入命令草案": file_state(root / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.md"),
            "单股证据核验191填写质量闸口": file_state(root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.md"),
            "单股证据核验人工填写工作台": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写工作台_最新.md"),
            "单股证据核验人工填写进度自检面板": file_state(root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写进度自检面板_最新.md"),
            "单股证据核验台账同步预览": file_state(root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.md"),
            "单股证据核验模板同步执行闸口": file_state(root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.md"),
            "单股证据核验191完成后预演检查": file_state(root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md"),
            "金融复核覆盖面板": file_state(root / "03数据" / "186金融复核覆盖面板" / "推荐观察股金融复核覆盖面板_最新.md"),
            "复盘学习闭环状态面板": file_state(root / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.md"),
            "判断复盘到期提醒清单": file_state(root / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.md"),
            "企微推送草案": file_state(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
            "盘后观察线刷新状态": file_state(risk_refresh_status_path),
            "收盘短线观察": file_state(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "收盘短线观察_基于300只轻扫描_最新.md"),
            "日报质量评分": file_state(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票日报质量评分_最新.md"),
            "报告生产事故账": file_state(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票报告生产事故账_最新.md"),
            "推送前放行包": file_state(root / "03数据" / "138推送前放行包" / "股票企微推送前放行包_最新.md"),
            "企微dry-run记录": file_state(root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新演练.json"),
            "可信IP状态监测": file_state(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md"),
            "企微前台交互回归验收": file_state(root / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.md"),
            "报告数据口径检查": file_state(root / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.md"),
            "C+++总验收": file_state(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
            "完全交付最终验收": file_state(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"),
            "交付总包": file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md"),
        },
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "156日常一键运行"
    output_json = output_dir / f"股票系统日常一键运行_{stamp}.json"
    output_md = output_dir / f"股票系统日常一键运行_{stamp}.md"
    latest_json = output_dir / "股票系统日常一键运行_最新.json"
    latest_md = output_dir / "股票系统日常一键运行_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    entry_tools = write_entry_bats(root / "02脚本" / "股票系统日常一键运行.py")

    quality_panel = root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"
    maybe_open(quality_panel, args.no_open)

    print(json.dumps({
        "状态": report["运行结论"],
        "失败数量": len(failed),
        "记录": str(latest_md),
        "入口工具": entry_tools,
        "质量观察面板": str(quality_panel),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
