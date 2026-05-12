# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验191填写质量闸口.py
作用：验证198质量闸口可生成，并确认其只做191 CSV填写质量检查，不代填事实、不执行写入。
触发方式：手动验收、日常一键运行或C+++总验收调用。
依赖：生成单股证据核验191填写质量闸口.py、191人工填写CSV表单、191人工填写台账。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验191填写质量闸口/single-stock-evidence-191-quality-gate-verify-最新.json。
安全边界：只运行198质量闸口生成和本地结构检查；不联网抓取，不提供事实答案，不写191填写值，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 支持191 CSV填完后的动态验收。
标识：single-stock-evidence-191-quality-gate-verify
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
    script = root / "02脚本" / "生成单股证据核验191填写质量闸口.py"
    latest_json = root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.json"
    latest_md = root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.md"
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
    checks.append(check("最新JSON存在", latest_json.exists() and latest_json.stat().st_size > 500, str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists() and latest_md.stat().st_size > 500, str(latest_md)))
    report = load_json(latest_json, {}) or {}
    checks.append(check("目标股票明确", bool(report.get("目标股票", {}).get("代码")), report.get("目标股票", {})))
    checks.append(check("闸口结论存在", bool(report.get("闸口结论")), report.get("闸口结论")))
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    checks.append(check("汇总结构完整", all(key in summary for key in ["CSV行数", "链路数", "缺失字段总数", "问题总数"]), summary))
    chain_checks = report.get("链路检查", []) if isinstance(report.get("链路检查"), list) else []
    checks.append(check("三条链路检查齐全", {item.get("链路") for item in chain_checks} == {"公司概况", "事件风险", "行业景气"}, chain_checks))
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks.append(check("明确不提供事实答案且不填写191", boundary.get("提供事实答案") is False and boundary.get("填写191") is False, boundary))
    checks.append(check("高风险动作全部关闭", bool(boundary) and all(value is False for value in boundary.values()), boundary))
    checks.append(check("197预演放行状态与质量结果一致", (report.get("是否允许进入197预演") is True and int(summary.get("缺失字段总数") or 0) == 0 and int(summary.get("问题总数") or 0) == 0) or (report.get("是否允许进入197预演") is False and (int(summary.get("缺失字段总数") or 0) > 0 or int(summary.get("问题总数") or 0) > 0)), {"是否允许": report.get("是否允许进入197预演"), "汇总": summary}))
    open_bat = root / "05入口工具" / "单股证据核验191填写质量闸口_打开.bat"
    checks.append(check("入口工具存在", open_bat.exists(), str(open_bat)))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含197和安全边界", "197" in md_text and "不提供事实答案" in md_text, str(latest_md)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验191填写质量闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-191-quality-gate-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-191-quality-gate-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
