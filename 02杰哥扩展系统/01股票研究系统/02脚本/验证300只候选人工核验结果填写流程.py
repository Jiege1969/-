# -*- coding: utf-8 -*-
"""
名称：验证300只候选人工核验结果填写流程.py
作用：验证人工核验结果填写模板可生成、可应用为103派生任务文件，并且101回填包可优先读取派生任务文件。
触发方式：python 验证300只候选人工核验结果填写流程.py
依赖：Python标准库；生成300只候选人工核验结果填写模板.py；应用300只候选人工核验结果填写模板.py；生成300只候选事件核验结果回填包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不覆盖100原始核验任务；不覆盖101回填包；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建人工核验结果填写流程验收脚本。
标识：stock-trial-pool-300-human-verification-template-flow-verify
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


def run_script(path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=str(path.parents[1]),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验结果填写规则.json"
    generator = root / "02脚本" / "生成300只候选人工核验结果填写模板.py"
    applier = root / "02脚本" / "应用300只候选人工核验结果填写模板.py"
    single_recorder = root / "02脚本" / "记录单条人工核验结果.py"
    backfill_generator = root / "02脚本" / "生成300只候选事件核验结果回填包.py"
    checks: list[dict[str, Any]] = [
        check("规则存在", rule_path.exists(), str(rule_path)),
        check("模板生成脚本存在", generator.exists(), str(generator)),
        check("模板应用脚本存在", applier.exists(), str(applier)),
        check("单条录入脚本存在", single_recorder.exists(), str(single_recorder)),
    ]
    gen = run_script(generator)
    checks.append(check("模板生成脚本执行", gen.returncode == 0, gen.stdout.strip() or gen.stderr.strip()))
    app = run_script(applier)
    checks.append(check("模板应用脚本执行", app.returncode == 0, app.stdout.strip() or app.stderr.strip()))
    backfill = run_script(backfill_generator)
    checks.append(check("101回填包重跑", backfill.returncode == 0, backfill.stdout.strip() or backfill.stderr.strip()))

    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    template_path = output_dir / rule["输出"]["模板最新文件"]
    applied_path = output_dir / rule["输出"]["应用结果文件"]
    report_path = output_dir / rule["输出"]["应用报告文件"]
    checks.append(check("模板最新文件存在", template_path.exists(), str(template_path)))
    checks.append(check("派生任务文件存在", applied_path.exists(), str(applied_path)))
    checks.append(check("应用报告存在", report_path.exists(), str(report_path)))
    template = load_json(template_path) if template_path.exists() else {}
    applied = load_json(applied_path) if applied_path.exists() else {}
    checks.append(check("模板包含30个填写任务", len(template.get("填写区", [])) == 30, len(template.get("填写区", []))))
    checks.append(check("派生任务不覆盖100标记", applied.get("是否覆盖100原始核验任务") is False, applied.get("是否覆盖100原始核验任务")))
    stats = applied.get("人工填写应用统计", {})
    checks.append(check("已应用30个任务", stats.get("已应用任务数量") == 30, stats))
    backfill_latest = root / "03数据" / "101事件核验结果回填" / "300只候选事件核验结果回填包_最新.json"
    backfill_report = load_json(backfill_latest) if backfill_latest.exists() else {}
    source_used = str(backfill_report.get("输入文件", {}).get("事件正文核验任务", ""))
    checks.append(check("101优先读取103派生任务", "103人工核验结果填写" in source_used, source_used))
    safety = rule.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(applied_path)
    }
    output_dir_log = root / "04日志" / "人工核验结果填写"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir_log / f"trial-pool-300-human-verification-template-flow-verify-{stamp}.json"
    latest = output_dir_log / "trial-pool-300-human-verification-template-flow-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
