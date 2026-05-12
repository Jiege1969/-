# -*- coding: utf-8 -*-
"""
名称：验证税收问题驱动取证任务包.py
作用：验证问题驱动取证任务包离线生成、产物完整、安全边界关闭。
触发方式：python 验证税收问题驱动取证任务包.py
依赖：Python标准库；生成税收业务问题输入模板.py；生成税收问题驱动取证任务包.py；税收问题驱动取证工作流规则.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只做离线验收；不联网检索、不下载、不写正式政策库、不写向量库、不触发n8n、不推送企微、不向外部问答窗口提问、不生成正式税务结论。
创建/修改记录：2026-04-30 创建税收问题驱动取证任务包验收脚本。
标识：tax-question-driven-evidence-task-package-verify
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


def run_script(root: Path, script: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(script)], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "税收问题驱动取证工作流规则.json"
    input_script = root / "02脚本" / "生成税收业务问题输入模板.py"
    task_script = root / "02脚本" / "生成税收问题驱动取证任务包.py"
    checks: list[dict[str, Any]] = [
        check("规则存在", rule_path.exists(), str(rule_path)),
        check("问题输入模板脚本存在", input_script.exists(), str(input_script)),
        check("任务包脚本存在", task_script.exists(), str(task_script))
    ]
    gen_input = run_script(root, input_script)
    checks.append(check("问题输入模板生成", gen_input.returncode == 0, gen_input.stdout.strip() or gen_input.stderr.strip()))
    gen_task = run_script(root, task_script)
    checks.append(check("任务包生成", gen_task.returncode == 0, gen_task.stdout.strip() or gen_task.stderr.strip()))
    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    task_json = output_dir / rule["输出"]["任务包最新文件"]
    task_md = output_dir / rule["输出"]["任务包Markdown最新文件"]
    evidence = output_dir / rule["输出"]["证据台账模板"]
    answer = output_dir / rule["输出"]["答案草案模板"]
    review = output_dir / rule["输出"]["人工复核单模板"]
    for name, path in [
        ("任务包JSON存在", task_json),
        ("任务包Markdown存在", task_md),
        ("证据台账模板存在", evidence),
        ("答案草案模板存在", answer),
        ("人工复核单模板存在", review)
    ]:
        checks.append(check(name, path.exists(), str(path)))
    package = load_json(task_json) if task_json.exists() else {}
    checks.append(check("识别出增值税", any(item.get("税种") == "增值税" for item in package.get("税种识别", [])), package.get("税种识别", [])))
    checks.append(check("生成官方检索任务", len(package.get("官方检索任务", [])) >= 4, len(package.get("官方检索任务", []))))
    checks.append(check("包含答案草案声明", "不得作为正式税务结论" in (answer.read_text(encoding="utf-8-sig") if answer.exists() else ""), str(answer)))
    safety = package.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    checks.append(check("未生成正式税务结论", package.get("安全边界", {}).get("是否生成正式税务结论") is False and "草案" in answer.name, answer.name))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(task_json)}
    log_dir = root / "04日志" / "问题驱动取证"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"tax-question-driven-evidence-task-package-verify-{stamp}.json"
    latest = log_dir / "tax-question-driven-evidence-task-package-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
