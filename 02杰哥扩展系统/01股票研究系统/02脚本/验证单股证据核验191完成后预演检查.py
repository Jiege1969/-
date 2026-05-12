# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验191完成后预演检查.py
作用：验证197预演检查器可安全运行；若最新报告已是正式apply-191结果，则只读验证并避免回写为默认预演态。
触发方式：python 验证单股证据核验191完成后预演检查.py
依赖：执行单股证据核验191完成后预演检查.py、191人工填写CSV表单、192同步预览、193同步执行闸口、194受控同步dry-run验证。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验191完成后预演检查/single-stock-evidence-after-191-preflight-verify-最新.json。
安全边界：默认只运行197默认预演模式；若最新报告已写入191台账，则只读验证不重跑；不重新生成CSV表单，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 支持正式apply-191后只读验证，避免验收脚本覆盖最新正式状态。
标识：single-stock-evidence-after-191-preflight-verify
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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def run_preflight(root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(root / "02脚本" / "执行单股证据核验191完成后预演检查.py")],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=240,
    )


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行单股证据核验191完成后预演检查.py"
    out_json = root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.json"
    out_md = root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md"
    ledger_json = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    csv_path = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"

    existing_report = load_json(out_json, {}) or {}
    already_applied = existing_report.get("是否写入191台账") is True
    before_ledger = file_state(ledger_json)
    before_csv = file_state(csv_path)
    if already_applied:
        run = subprocess.CompletedProcess(args=[], returncode=0, stdout="最新197报告已是apply-191结果，本验证只读检查，不重跑默认预演。", stderr="")
    else:
        run = run_preflight(root)
    after_ledger = file_state(ledger_json)
    after_csv = file_state(csv_path)
    report = load_json(out_json, {}) or {}

    checks: list[dict[str, Any]] = [
        check("197预演脚本存在", script.exists(), str(script)),
        check("197验证执行或只读检查成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()),
        check("最新JSON存在", out_json.exists() and out_json.stat().st_size > 500, str(out_json)),
        check("最新Markdown存在", out_md.exists() and out_md.stat().st_size > 500, str(out_md)),
        check("验证过程不额外改写191台账", before_ledger == after_ledger, {"执行前": before_ledger, "执行后": after_ledger}),
        check("验证过程不覆盖CSV表单", before_csv == after_csv, {"执行前": before_csv, "执行后": after_csv}),
        check("执行模式符合当前阶段", (already_applied and report.get("执行模式") == "同步CSV到191台账后预演" and report.get("是否写入191台账") is True) or ((not already_applied) and report.get("执行模式") == "只预演不写入" and report.get("是否写入191台账") is False), report.get("执行模式")),
    ]
    sync = report.get("CSV同步摘要", {}) if isinstance(report.get("CSV同步摘要"), dict) else {}
    gate = report.get("193闸口摘要", {}) if isinstance(report.get("193闸口摘要"), dict) else {}
    verify_194 = report.get("194验证摘要", {}) if isinstance(report.get("194验证摘要"), dict) else {}
    checks.extend([
        check("CSV同步摘要存在", "缺失字段总数" in sync and "可进入预览链路数" in sync, sync),
        check("193闸口摘要存在", "是否允许进入模板同步执行器" in gate and "闸口结论" in gate, gate),
        check("194 dry-run验证摘要存在", "失败" in verify_194 and "通过" in verify_194, verify_194),
        check("安全边界声明完整", all(keyword in "\n".join(report.get("安全边界", [])) for keyword in ["不写172/175/178", "不触发n8n", "不发送企业微信", "不更新施工接续包"]), report.get("安全边界", [])),
    ])
    actions = report.get("动作", []) if isinstance(report.get("动作"), list) else []
    action_names = {item.get("脚本") for item in actions}
    required_actions = {
        "同步单股证据核验CSV表单到台账.py",
        "生成单股证据核验台账同步预览.py",
        "验证单股证据核验台账同步预览.py",
        "生成单股证据核验模板同步执行闸口.py",
        "验证单股证据核验模板同步执行闸口.py",
        "验证单股证据核验模板同步执行.py",
    }
    checks.append(check("预演动作链完整", required_actions.issubset(action_names), sorted(action_names)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(out_json),
    }
    log_dir = root / "04日志" / "单股证据核验191完成后预演检查"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-after-191-preflight-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-after-191-preflight-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
