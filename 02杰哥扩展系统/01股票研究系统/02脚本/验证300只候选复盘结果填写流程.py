# -*- coding: utf-8 -*-
"""
名称：验证300只候选复盘结果填写流程.py
作用：验证107复盘结果填写模板和应用流程可运行，且不覆盖106原始任务包。
触发方式：python 验证300只候选复盘结果填写流程.py
依赖：Python标准库；生成300只候选复盘结果填写模板.py；应用300只候选复盘结果填写模板.py；300只候选复盘结果填写规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不覆盖106原始任务包；不联网抓取行情；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选复盘结果填写流程验收脚本。
标识：stock-trial-pool-300-review-result-fill-flow-verify
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
    rule_path = root / "01配置" / "300只候选复盘结果填写规则.json"
    generate_script = root / "02脚本" / "生成300只候选复盘结果填写模板.py"
    apply_script = root / "02脚本" / "应用300只候选复盘结果填写模板.py"
    single_script = root / "02脚本" / "记录单条复盘结果.py"
    checks: list[dict[str, Any]] = [
        check("规则存在", rule_path.exists(), str(rule_path)),
        check("模板生成脚本存在", generate_script.exists(), str(generate_script)),
        check("模板应用脚本存在", apply_script.exists(), str(apply_script)),
        check("单条录入脚本存在", single_script.exists(), str(single_script)),
    ]
    gen = run_script(root, generate_script)
    checks.append(check("模板生成脚本执行", gen.returncode == 0, gen.stdout.strip() or gen.stderr.strip()))
    app = run_script(root, apply_script)
    checks.append(check("模板应用脚本执行", app.returncode == 0, app.stdout.strip() or app.stderr.strip()))
    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    template_path = output_dir / rule["输出"]["模板最新文件"]
    template_md = output_dir / rule["输出"]["模板说明文件"]
    result_path = output_dir / rule["输出"]["应用结果文件"]
    report_md = output_dir / rule["输出"]["应用报告文件"]
    template = load_json(template_path) if template_path.exists() else {}
    result = load_json(result_path) if result_path.exists() else {}
    tasks = result.get("复盘执行任务", [])
    checks.append(check("模板JSON存在", template_path.exists(), str(template_path)))
    checks.append(check("模板Markdown存在", template_md.exists(), str(template_md)))
    checks.append(check("派生结果JSON存在", result_path.exists(), str(result_path)))
    checks.append(check("应用报告Markdown存在", report_md.exists(), str(report_md)))
    checks.append(check("模板任务数量正确", template.get("任务数量") == 15, template.get("任务数量")))
    checks.append(check("派生任务数量正确", len(tasks) == 15, len(tasks)))
    checks.append(check("不覆盖106原始任务包", result.get("是否覆盖106原始任务包") is False, result.get("是否覆盖106原始任务包")))
    safety = result.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))
    text = template_md.read_text(encoding="utf-8-sig") if template_md.exists() else ""
    checks.append(check("模板说明包含使用方式和安全边界", "使用方式" in text and "安全边界" in text, str(template_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(result_path)}
    log_dir = root / "04日志" / "复盘结果填写"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-review-result-fill-flow-verify-{stamp}.json"
    latest = log_dir / "trial-pool-300-review-result-fill-flow-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
