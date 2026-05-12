# -*- coding: utf-8 -*-
"""
名称：验证300只候选人工核验批量填报导入预演.py
作用：验证120导入预演只生成差异预览，不修改103。
触发方式：python 验证300只候选人工核验批量填报导入预演.py
依赖：Python标准库；生成300只候选人工核验批量填报导入预演.py；300只候选人工核验批量填报导入预演规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写验收日志；不写入核验结果；不修改103；不导入填报表；不应用103派生任务；不联网；不下载正文；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建人工核验批量填报导入预演验收脚本。
标识：stock-trial-pool-300-manual-verification-batch-import-preview-verify
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
    rule_path = root / "01配置" / "300只候选人工核验批量填报导入预演规则.json"
    script = root / "02脚本" / "生成300只候选人工核验批量填报导入预演.py"
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
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    after = template_path.read_text(encoding="utf-8-sig") if template_path.exists() else ""
    checks.append(check("未修改103模板", before == after, str(template_path)))
    rule = load_json(rule_path)
    latest_json = root / rule["输出"]["数据目录"] / rule["输出"]["最新JSON"]
    latest_md = root / rule["输出"]["数据目录"] / rule["输出"]["最新Markdown"]
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("摘要", {})
    checks.append(check("CSV行数为30", summary.get("CSV行数") == 30, summary))
    checks.append(check("当前无填写行", summary.get("已填写行数") == 0, summary))
    checks.append(check("当前无待导入变更", summary.get("将产生变更的任务数") == 0, summary))
    checks.append(check("当前不可进入导入确认", summary.get("是否可进入导入前人工确认") is False, summary))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含导入预演结论", "导入预演" in text and "当前没有任何待导入变更" in text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest_json)}
    log_dir = root / "04日志" / "人工核验批量导入预演"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-manual-verification-batch-import-preview-verify-{stamp}.json"
    latest_log = log_dir / "trial-pool-300-manual-verification-batch-import-preview-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
