# -*- coding: utf-8 -*-
"""
名称：执行四系统股票小闭环.py
作用：一键执行四系统股票小闭环：股票快检、日常快速刷新、企微回归、公网回调、四系统面板、四系统验收、开工快检、融合面板、历史观察和历史观察验证，并生成执行记录。
触发方式：python 执行四系统股票小闭环.py [--no-open]
依赖：本机Python、股票系统验收脚本、企微回归脚本、公网回调检查脚本、四系统状态面板、开工快检、融合面板、历史观察面板和验收脚本。
所属系统：00杰哥系统总管
输出：03数据/四系统小闭环/四系统股票小闭环一键执行_最新.json 与 .md。
安全边界：只运行本地验收和状态生成脚本；不重启服务；不触发n8n；不真实发送企业微信；不调用券商接口；不自动交易；不写正式业务库；不更新施工接续包。
标识：four-system-stock-loop-runner
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


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(script: Path, args: list[str] | None = None, timeout: int = 600) -> dict[str, Any]:
    started = datetime.now()
    try:
        completed = subprocess.run(
            [sys.executable, str(script), *(args or [])],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "名称": script.name,
            "路径": str(script),
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
            "名称": script.name,
            "路径": str(script),
            "参数": args or [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": -1,
            "成功": False,
            "stdout": "",
            "stderr": str(exc),
        }


def run_powershell_status(script: Path, timeout: int = 120) -> dict[str, Any]:
    started = datetime.now()
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        stdout = (completed.stdout or "").strip()
        parsed: dict[str, Any] = {}
        try:
            parsed = json.loads(stdout) if stdout else {}
        except Exception:
            parsed = {}
        ready = parsed.get("status") == "ready"
        return {
            "名称": script.name,
            "路径": str(script),
            "参数": [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": completed.returncode,
            "成功": completed.returncode == 0 and ready,
            "stdout": stdout[-3000:],
            "stderr": (completed.stderr or "").strip()[-3000:],
            "状态数据": parsed,
        }
    except Exception as exc:
        return {
            "名称": script.name,
            "路径": str(script),
            "参数": [],
            "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "返回码": -1,
            "成功": False,
            "stdout": "",
            "stderr": str(exc),
            "状态数据": {},
        }


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 四系统股票小闭环一键执行记录 - {report['生成时间']}",
        "",
        "## 一、执行结论",
        "",
        f"- 结论：{report['执行结论']}",
        f"- 动作数：{len(report['动作'])}",
        f"- 失败数：{report['失败数量']}",
        "",
        "## 二、执行动作",
        "",
    ]
    for item in report["动作"]:
        lines.append(f"- {item['名称']}：{'成功' if item['成功'] else '失败'}")
    lines.extend(["", "## 三、关键产物", ""])
    for name, state in report["关键产物"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 不重启服务。",
        "- 不真实发送企业微信。",
        "- 不触发n8n自动工作流。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不写正式业务库。",
    ])
    return "\n".join(lines) + "\n"


def write_entry_bat(script_path: Path) -> Path:
    bat = system_root() / "00杰哥系统总管" / "06工具" / "四系统股票小闭环一键执行.bat"
    content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        "pause\r\n"
    )
    write_text(bat, content)
    return bat


def maybe_open(path: Path, no_open: bool) -> None:
    if no_open:
        return
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-open", action="store_true", help="执行后不自动打开四系统闭环面板")
    args = parser.parse_args()

    root = system_root()
    manager = root / "00杰哥系统总管"
    stock = root / "02杰哥扩展系统" / "01股票研究系统"
    now = datetime.now()
    actions: list[dict[str, Any]] = []
    actions.append(run_script(stock / "02脚本" / "验证股票系统完全交付最终验收.py", timeout=180))
    actions.append(run_script(stock / "02脚本" / "验证股票系统C加加加日常可用总验收.py", timeout=180))
    actions.append(run_script(stock / "02脚本" / "股票系统日常一键运行.py", ["--skip-closed-loop", "--no-open"], timeout=600))
    actions.append(run_script(stock / "02脚本" / "验证股票企微前台交互回归.py", timeout=180))
    actions.append(run_powershell_status(stock / "02脚本" / "查看股票公网回调状态.ps1", timeout=120))
    actions.append(run_script(manager / "02脚本" / "生成四系统股票小闭环状态面板.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "验证四系统股票小闭环.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "执行四系统小闭环开工快检.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "验证四系统小闭环开工快检.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "生成股票四系统融合闭环状态面板.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "验证股票四系统融合闭环状态面板.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "生成子系统全闭环继承状态.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "验证子系统全闭环继承状态.py", timeout=120))

    panel = manager / "03数据" / "四系统小闭环" / "四系统股票小闭环状态面板_最新.md"
    output_dir = manager / "03数据" / "四系统小闭环"
    latest_json = output_dir / "四系统股票小闭环一键执行_最新.json"
    latest_md = output_dir / "四系统股票小闭环一键执行_最新.md"

    def build_report(current_actions: list[dict[str, Any]]) -> dict[str, Any]:
        current_failed = [item for item in current_actions if not item.get("成功")]
        return {
        "名称": "四系统股票小闭环一键执行记录",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行四系统股票小闭环.py",
        "执行结论": "完成：四系统股票小闭环执行成功" if not current_failed else "存在失败动作",
        "失败数量": len(current_failed),
        "动作": current_actions,
        "关键产物": {
            "四系统小闭环状态面板": file_state(panel),
            "四系统小闭环验收": file_state(manager / "03数据" / "四系统小闭环" / "四系统股票小闭环验收_最新.md"),
            "四系统小闭环开工快检": file_state(manager / "03数据" / "四系统小闭环" / "四系统小闭环开工快检_最新.md"),
            "股票四系统融合闭环状态面板": file_state(manager / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.md"),
            "四系统小闭环历史观察": file_state(manager / "03数据" / "四系统小闭环" / "四系统股票小闭环历史观察面板_最新.md"),
            "四系统小闭环历史观察验证": file_state(manager / "04日志" / "四系统小闭环" / "four-system-stock-loop-history-panel-verify-最新.json"),
            "子系统全闭环继承状态": file_state(manager / "03数据" / "全闭环保障" / "子系统全闭环继承状态_最新.json"),
            "四系统小闭环通用施工模板": file_state(root / "03杰哥进化系统" / "03数据" / "04通用方法" / "四系统小闭环_通用施工模板_20260503.md"),
            "文稿质检样本复盘报告": file_state(root / "01杰哥智能系统" / "03数据" / "文稿质检" / "样本复盘" / "文稿质检样本复盘报告_最新.md"),
            "股票完全交付验收": file_state(stock / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"),
            "股票C+++验收": file_state(stock / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
            "股票日常一键运行": file_state(stock / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.md"),
            "企微前台回归": file_state(stock / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.md"),
        },
        "安全边界": {
            "是否重启服务": False,
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写正式业务库": False,
            "是否更新施工接续包": False,
        },
    }

    preliminary = build_report(actions)
    write_json(latest_json, preliminary)
    write_text(latest_md, build_markdown(preliminary))

    actions.append(run_script(manager / "02脚本" / "生成四系统股票小闭环历史观察面板.py", timeout=120))
    actions.append(run_script(manager / "02脚本" / "验证四系统股票小闭环历史观察面板.py", timeout=120))
    report = build_report(actions)
    failed = [item for item in actions if not item.get("成功")]
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    bat = write_entry_bat(manager / "02脚本" / "执行四系统股票小闭环.py")
    maybe_open(panel, args.no_open)

    print(json.dumps({
        "状态": report["执行结论"],
        "失败数量": len(failed),
        "记录": str(latest_md),
        "入口工具": str(bat),
        "状态面板": str(panel),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
