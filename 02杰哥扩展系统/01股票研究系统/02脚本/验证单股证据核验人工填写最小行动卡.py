# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验人工填写最小行动卡.py
作用：验证191人工填写最小行动卡可生成，且只提供行动指引、不替代人工核验。
触发方式：手动验收或由股票系统日常/C+++验收调用。
依赖：生成单股证据核验人工填写最小行动卡.py、191单股证据核验人工填写台账。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验人工填写最小行动卡/single-stock-evidence-minimum-action-card-verify-最新.json。
安全边界：只读191行动卡和台账；运行生成脚本只写191行动卡；不联网抓取、不填写事实、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易、不更新施工接续包。
创建/修改记录：2026-05-03 创建。
标识：single-stock-evidence-manual-minimum-action-card-verify
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


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成单股证据核验人工填写最小行动卡.py"
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    latest_json = out_dir / "单股证据核验人工填写最小行动卡_最新.json"
    latest_md = out_dir / "单股证据核验人工填写最小行动卡_最新.md"
    checks: list[dict[str, Any]] = [check("生成脚本存在", script.exists(), str(script))]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json, {}) or {}
    checks.append(check("目标股票明确", bool(report.get("目标股票", {}).get("代码")), report.get("目标股票", {})))
    actions = report.get("三步行动", [])
    checks.append(check("包含三步行动", len(actions) == 3 and {item.get("链路") for item in actions} == {"公司概况", "事件风险", "行业景气"}, actions))
    checks.append(check("每步包含必填字段", all(item.get("必填字段") for item in actions), actions))
    steps = report.get("最小操作顺序", [])
    checks.append(check("操作顺序包含CSV、198、197与193/194", any("CSV" in item for item in steps) and any("198" in item for item in steps) and any("197" in item for item in steps) and any("193" in item for item in steps) and any("194" in item for item in steps), steps))
    forbidden = report.get("禁止事项", [])
    checks.append(check("禁止事项防止伪造核验", any("没有来源" in item for item in forbidden) and any("已核验" in item for item in forbidden), forbidden))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown明确不替代人工核验", "不替代人工核验" in md_text and "不提供事实内容" in md_text, str(latest_md)))
    open_bat = root / "05入口工具" / "单股证据核验人工填写最小行动卡_打开.bat"
    checks.append(check("入口工具存在", open_bat.exists(), str(open_bat)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验人工填写最小行动卡"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-minimum-action-card-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-minimum-action-card-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
