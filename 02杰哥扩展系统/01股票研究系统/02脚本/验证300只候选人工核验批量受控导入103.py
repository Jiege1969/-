# -*- coding: utf-8 -*-
"""
名称：验证300只候选人工核验批量受控导入103.py
作用：验证122受控导入工具默认只预演，当前不写103。
触发方式：python 验证300只候选人工核验批量受控导入103.py
依赖：Python标准库；受控导入300只候选人工核验批量填报到103.py；300只候选人工核验批量受控导入103规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写验收日志；不写入核验结果；不修改103；不导入填报表；不应用103派生任务；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-05-01 创建人工核验批量受控导入103验收脚本。
标识：stock-trial-pool-300-manual-verification-controlled-import-to-103-verify
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


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量受控导入103规则.json"
    script = root / "02脚本" / "受控导入300只候选人工核验批量填报到103.py"
    template_path = root / "03数据" / "103人工核验结果填写" / "300只候选人工核验结果填写模板_最新.json"
    before = template_path.read_text(encoding="utf-8-sig") if template_path.exists() else ""
    checks: list[dict[str, Any]] = [
        check("规则存在", rule_path.exists(), str(rule_path)),
        check("脚本存在", script.exists(), str(script)),
        check("103模板存在", template_path.exists(), str(template_path))
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run([sys.executable, str(script)], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    checks.append(check("默认预演执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    after = template_path.read_text(encoding="utf-8-sig") if template_path.exists() else ""
    checks.append(check("默认预演未修改103", before == after, str(template_path)))
    rule = load_json(rule_path)
    latest_json = root / rule["输出"]["数据目录"] / rule["输出"]["最新JSON"]
    latest_md = root / rule["输出"]["数据目录"] / rule["输出"]["最新Markdown"]
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json) if latest_json.exists() else {}
    checks.append(check("报告为默认预演", report.get("执行模式") == "默认预演", report.get("执行模式")))
    checks.append(check("报告未实际写103", report.get("是否实际写入103") is False, report))
    checks.append(check("当前被121阻断", "121闸口未放行" in report.get("阻断原因", []), report.get("阻断原因", [])))
    safety = report.get("安全边界", {})
    checks.append(check("默认高风险动作关闭", all(value is False for value in safety.values()), safety))
    text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含受控导入结论", "是否实际写入103" in text and "未写入103" in text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest_json)}
    log_dir = root / "04日志" / "人工核验批量受控导入103"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-manual-verification-controlled-import-to-103-verify-{stamp}.json"
    latest_log = log_dir / "trial-pool-300-manual-verification-controlled-import-to-103-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
