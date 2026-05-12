# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验最小人工确认清单.py
作用：验证201最小人工确认清单可生成，并确认其只压缩确认问题、不写191、不替代人工判断。
触发方式：手动验收、股票系统日常一键运行或C+++总验收调用。
依赖：生成单股证据核验最小人工确认清单.py、200填写建议草案。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验最小人工确认清单/single-stock-evidence-minimal-human-confirmation-list-verify-最新.json。
安全边界：只运行201清单生成脚本并读取本地结果；不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-minimal-human-confirmation-list-verify
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
    script = root / "02脚本" / "生成单股证据核验最小人工确认清单.py"
    out_dir = root / "03数据" / "201单股证据核验最小人工确认清单"
    latest_json = out_dir / "单股证据核验最小人工确认清单_最新.json"
    latest_md = out_dir / "单股证据核验最小人工确认清单_最新.md"
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
    report = load_json(latest_json, {}) or {}
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    items = report.get("确认清单", []) if isinstance(report.get("确认清单"), list) else []
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    chains = {item.get("链路") for item in items if isinstance(item, dict)}
    checks = [
        check("生成脚本存在", script.exists(), str(script)),
        check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()),
        check("最新JSON存在", latest_json.exists(), str(latest_json)),
        check("最新Markdown存在", latest_md.exists(), str(latest_md)),
        check("三条链路均有确认问题", {"公司概况", "事件风险", "行业景气"}.issubset(chains), list(chains)),
        check("最小确认问题数为三", int(summary.get("最小确认问题数") or 0) == 3, summary),
        check("仍需确认字段数大于0", int(summary.get("仍需确认字段数") or 0) > 0, summary),
        check("不自动给已核验结论", all("核验状态" not in str(field) or "已核验" not in str(item.get("默认后续动作", "")) for item in items for field in item.get("必填确认字段", [])), "核验状态仍需人工确认，建议选项可包含已核验但不得作为默认结果"),
        check("安全边界不写正式链路", bool(boundary) and all(value is False for value in boundary.values()), boundary),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验最小人工确认清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-minimal-human-confirmation-list-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-minimal-human-confirmation-list-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
