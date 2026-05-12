# -*- coding: utf-8 -*-
"""
名称：验证税收人工入口资料下载闸口.py
作用：不联网验证下载闸口默认拒绝下载、只生成申请单；未勾选条目时即使有确认参数也不下载。
触发方式：python 验证税收人工入口资料下载闸口.py
依赖：Python标准库；税收人工入口资料下载闸口.py；税收人工入口资料下载器.py。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只运行self-test清单、选择模板和未确认闸口；不联网、不下载、不入库、不触发n8n、不推送企微。
创建/修改记录：2026-04-30 创建人工入口资料下载闸口验收脚本。
标识：tax-manual-url-download-gate-verify
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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def run_script(root: Path, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(script), *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收人工入口资料下载器配置.json"
    one_click = root / "02脚本" / "税收人工入口资料清单一键生成.py"
    selection_script = root / "02脚本" / "生成税收人工入口资料下载选择模板.py"
    gate = root / "02脚本" / "税收人工入口资料下载闸口.py"
    checks: list[dict[str, Any]] = [
        check("配置存在", config_path.exists(), str(config_path)),
        check("选择模板脚本存在", selection_script.exists(), str(selection_script)),
        check("下载闸口脚本存在", gate.exists(), str(gate)),
    ]
    config = load_json(config_path)
    seed = run_script(root, one_click, "--self-test")
    checks.append(check("自测清单已生成", seed.returncode == 0, seed.stdout.strip() or seed.stderr.strip()))
    selection_run = run_script(root, selection_script)
    checks.append(check("选择模板已生成", selection_run.returncode == 0, selection_run.stdout.strip() or selection_run.stderr.strip()))
    run = run_script(root, gate)
    checks.append(check("未确认时闸口执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    output_dir = root / config["输出"]["数据目录"]
    app_json = output_dir / "税收人工入口资料下载申请单_最新.json"
    app_md = output_dir / "税收人工入口资料下载申请单_最新.md"
    checks.append(check("申请单JSON存在", app_json.exists(), str(app_json)))
    checks.append(check("申请单Markdown存在", app_md.exists(), str(app_md)))
    app = load_json(app_json) if app_json.exists() else {}
    checks.append(check("默认不允许下载", app.get("是否允许执行下载") is False, app.get("是否允许执行下载")))
    checks.append(check("默认未勾选下载条目", app.get("已勾选下载数量") == 0, app.get("已勾选下载数量")))
    checks.append(check("选择模板匹配当前清单", app.get("选择模板状态") == "匹配当前清单", app.get("选择模板状态")))
    checks.append(check("未写正式政策目录", app.get("是否写入正式政策目录") is False, app.get("是否写入正式政策目录")))
    checks.append(check("未触发n8n和企微", app.get("是否触发n8n") is False and app.get("是否企业微信真实发送") is False, {"n8n": app.get("是否触发n8n"), "企微": app.get("是否企业微信真实发送")}))
    text = app_md.read_text(encoding="utf-8-sig") if app_md.exists() else ""
    checks.append(check("Markdown包含当前结论、选择模板状态和安全边界", "当前结论" in text and "选择模板状态" in text and "安全边界" in text, str(app_md)))
    confirmed_without_selection = run_script(root, gate, "--confirm-download", "YES", "--max-files", "1")
    checks.append(check("确认但未勾选时仍不下载", confirmed_without_selection.returncode == 0, confirmed_without_selection.stdout.strip() or confirmed_without_selection.stderr.strip()))
    app_after_confirm = load_json(app_json) if app_json.exists() else {}
    latest_app = load_json(output_dir / "税收人工入口资料下载申请单_最新.json")
    checks.append(check("确认但未勾选时申请单仍禁止下载", latest_app.get("是否允许执行下载") is False and latest_app.get("已勾选下载数量") == 0, latest_app.get("当前结论")))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(app_json)}
    output_log_dir = root / "04日志" / "人工入口下载器"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_log_dir / f"tax-manual-url-download-gate-verify-{stamp}.json"
    latest = output_log_dir / "tax-manual-url-download-gate-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
