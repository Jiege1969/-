# -*- coding: utf-8 -*-
"""
名称：执行单股证据核验191完成后预演检查.py
作用：在191人工CSV填写后，按安全顺序预演191→192→193→194 dry-run链路，判断是否具备进入受控同步的条件。
触发方式：python 执行单股证据核验191完成后预演检查.py；如需写入191台账，必须追加 --apply-191 --confirm 允许同步CSV到191台账。
依赖：191人工填写CSV表单、同步单股证据核验CSV表单到台账.py、192同步预览、193同步执行闸口、194受控同步dry-run验证。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/197单股证据核验191完成后预演检查/单股证据核验191完成后预演检查_最新.json 与 .md。
安全边界：默认只运行CSV dry-run和后续闸口预演；不重新生成CSV表单，不覆盖人工填写；不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-after-191-preflight
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


CONFIRM_TEXT = "允许同步CSV到191台账"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(root: Path, script_name: str, args: list[str] | None = None, timeout: int = 180) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    command = [sys.executable, str(root / "02脚本" / script_name), *(args or [])]
    started = datetime.now()
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
            "脚本": script_name,
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
            "脚本": script_name,
            "参数": args or [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": -1,
            "成功": False,
            "stdout": "",
            "stderr": str(exc),
        }


def summarize_sync_report(root: Path) -> dict[str, Any]:
    path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验CSV表单同步到台账_最新.json"
    report = load_json(path, {}) or {}
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    return {
        "报告路径": str(path),
        "只预检": report.get("只预检"),
        "读取行数": report.get("读取行数"),
        "变更字段数": len(report.get("变更", []) if isinstance(report.get("变更"), list) else []),
        "忽略行数": len(report.get("忽略", []) if isinstance(report.get("忽略"), list) else []),
        "可进入预览链路数": int(summary.get("可进入预览链路数") or 0),
        "缺失字段总数": int(summary.get("缺失字段总数") or 0),
    }


def summarize_gate(root: Path) -> dict[str, Any]:
    path = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    report = load_json(path, {}) or {}
    target = report.get("目标股票", {}) if isinstance(report.get("目标股票"), dict) else {}
    return {
        "报告路径": str(path),
        "目标股票": f"{target.get('名称')}({target.get('代码')})" if target else "",
        "闸口结论": report.get("闸口结论"),
        "是否允许进入模板同步执行器": bool(report.get("是否允许进入模板同步执行器")),
        "本脚本是否执行写入": report.get("本脚本是否执行写入"),
    }


def summarize_194_verify(root: Path) -> dict[str, Any]:
    path = root / "04日志" / "单股证据核验模板同步执行" / "single-stock-evidence-template-sync-execute-verify-最新.json"
    report = load_json(path, {}) or {}
    return {
        "报告路径": str(path),
        "通过": int(report.get("通过") or 0),
        "失败": int(report.get("失败") or 0),
    }


def build_conclusion(apply_191: bool, sync: dict[str, Any], gate: dict[str, Any], verify_194: dict[str, Any]) -> tuple[str, list[str]]:
    next_steps: list[str] = []
    if not apply_191:
        if int(sync.get("缺失字段总数") or 0) == 0 and int(sync.get("可进入预览链路数") or 0) == 3:
            conclusion = "CSV预检显示191可同步；当前仍未写入191台账，需要显式执行apply-191后再看193闸口。"
            next_steps.append(f"确认CSV内容无误后，手动运行：python 执行单股证据核验191完成后预演检查.py --apply-191 --confirm {CONFIRM_TEXT}")
        else:
            conclusion = "CSV预检仍未达到191完成条件，禁止进入正式同步。"
            next_steps.append("继续补齐191 CSV“填写值”列，尤其是缺失字段和核验状态。")
        next_steps.append("默认模式不会写191台账，也不会覆盖人工CSV。")
        return conclusion, next_steps

    if gate.get("是否允许进入模板同步执行器") and int(verify_194.get("失败") or 0) == 0:
        conclusion = "191已同步并通过193闸口；194 dry-run验证通过，具备后续显式受控同步条件。"
        next_steps.append("如需写入172/175/178人工模板，另行人工确认运行194执行器的显式写入命令。")
    else:
        conclusion = "191已按确认同步，但193或194 dry-run仍未完全放行，禁止进入模板写入。"
        next_steps.append("查看193闸口结论和194 dry-run验证日志，定位仍被阻断的链路。")
    next_steps.append("无论本步是否通过，都不写正式档案、不导入正式库。")
    return conclusion, next_steps


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 单股证据核验191完成后预演检查 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总结论：{report['总结论']}",
        f"- 执行模式：{report['执行模式']}",
        f"- 是否写入191台账：{'是' if report['是否写入191台账'] else '否'}",
        "",
        "## 二、链路预演结果",
        "",
        f"- CSV同步预检：缺失字段 {report['CSV同步摘要']['缺失字段总数']}，可进入预览链路 {report['CSV同步摘要']['可进入预览链路数']} / 3，变更字段 {report['CSV同步摘要']['变更字段数']}。",
        f"- 193闸口：{'允许' if report['193闸口摘要']['是否允许进入模板同步执行器'] else '禁止'}；{report['193闸口摘要']['闸口结论']}",
        f"- 194 dry-run验证：通过 {report['194验证摘要']['通过']}，失败 {report['194验证摘要']['失败']}。",
        "",
        "## 三、本次脚本动作",
        "",
        "| 动作 | 结果 | 说明 |",
        "|---|---|---|",
    ]
    for item in report["动作"]:
        detail = item["stdout"] or item["stderr"]
        detail = detail.replace("\n", " ")[:160]
        lines.append(f"| {item['脚本']} | {'成功' if item['成功'] else '失败'} | {detail} |")
    lines.extend([
        "",
        "## 四、下一步",
        "",
    ])
    for step in report["下一步"]:
        lines.append(f"- {step}")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
    ])
    for item in report["安全边界"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-191", action="store_true", help="显式允许把CSV填写值同步到191台账")
    parser.add_argument("--confirm", default="", help=f"写入191台账时必须填写：{CONFIRM_TEXT}")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    actions: list[dict[str, Any]] = []

    apply_191 = bool(args.apply_191)
    if apply_191 and args.confirm != CONFIRM_TEXT:
        raise SystemExit(f"拒绝执行：--apply-191 必须同时传入 --confirm {CONFIRM_TEXT}")

    sync_args: list[str] = [] if apply_191 else ["--dry-run"]
    actions.append(run_script(root, "同步单股证据核验CSV表单到台账.py", sync_args, timeout=120))

    actions.append(run_script(root, "生成单股证据核验台账同步预览.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验台账同步预览.py", timeout=120))
    actions.append(run_script(root, "生成单股证据核验模板同步执行闸口.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验模板同步执行闸口.py", timeout=120))
    actions.append(run_script(root, "验证单股证据核验模板同步执行.py", timeout=120))

    sync = summarize_sync_report(root)
    gate = summarize_gate(root)
    verify_194 = summarize_194_verify(root)
    conclusion, next_steps = build_conclusion(apply_191, sync, gate, verify_194)

    report = {
        "名称": "单股证据核验191完成后预演检查",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行单股证据核验191完成后预演检查.py",
        "执行模式": "同步CSV到191台账后预演" if apply_191 else "只预演不写入",
        "是否写入191台账": apply_191,
        "总结论": conclusion,
        "动作": actions,
        "CSV同步摘要": sync,
        "193闸口摘要": gate,
        "194验证摘要": verify_194,
        "下一步": next_steps,
        "安全边界": [
            "默认不写191台账；只有显式 --apply-191 和确认短语才写191。",
            "不重新生成CSV表单，避免覆盖用户人工填写。",
            "不写172/175/178人工模板，194只做dry-run验证。",
            "不写正式档案，不导入正式库，不修改评分或推荐。",
            "不触发n8n，不发送企业微信，不调用券商接口，不自动交易。",
            "不更新施工接续包。",
        ],
    }
    out_dir = root / "03数据" / "197单股证据核验191完成后预演检查"
    latest_json = out_dir / "单股证据核验191完成后预演检查_最新.json"
    latest_md = out_dir / "单股证据核验191完成后预演检查_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    write_json(out_dir / f"单股证据核验191完成后预演检查_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验191完成后预演检查_{stamp}.md", build_markdown(report))
    print(json.dumps({"总结论": conclusion, "是否写入191台账": apply_191, "报告": str(latest_json)}, ensure_ascii=False))
    return 0 if all(item.get("成功") for item in actions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
