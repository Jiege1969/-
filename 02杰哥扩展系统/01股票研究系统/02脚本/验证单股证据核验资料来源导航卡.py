# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验资料来源导航卡.py
作用：验证191资料来源导航卡可生成，且只提供候选资料入口、资料导航和合格标准，不代填事实、不触发外部动作。
触发方式：手动验收、日常一键运行或C+++总验收调用。
依赖：生成单股证据核验资料来源导航卡.py、191人工填写台账、191最小行动卡。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验资料来源导航卡/single-stock-evidence-source-navigation-card-verify-最新.json。
安全边界：只运行资料来源导航卡生成和本地结构检查；不联网抓取，不提供事实答案，不写191填写值，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-source-navigation-card-verify
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
    script = root / "02脚本" / "生成单股证据核验资料来源导航卡.py"
    latest_json = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.json"
    latest_md = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.md"
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
    navigation = report.get("资料导航", []) if isinstance(report.get("资料导航"), list) else []
    chain_names = {item.get("链路") for item in navigation if isinstance(item, dict)}
    checks.append(check("三条资料导航齐全", chain_names == {"公司概况", "事件风险", "行业景气"}, sorted(chain_names)))
    checks.append(check("每条链路包含来源关键词和合格标准", all(
        isinstance(item, dict)
        and item.get("推荐资料来源")
        and item.get("建议检索关键词")
        and item.get("合格标准")
        for item in navigation
    ), navigation))
    candidates = report.get("候选资料入口", []) if isinstance(report.get("候选资料入口"), list) else []
    checks.append(check(
        "天齐锂业候选资料入口包含最高优先级和第二优先级",
        any(item.get("优先级") == "最高优先级" for item in candidates)
        and any(item.get("优先级") == "第二优先级" for item in candidates)
        and any("巨潮" in str(item.get("来源名称")) for item in candidates)
        and any("东方财富" in str(item.get("来源名称")) for item in candidates),
        candidates,
    ))
    checks.append(check("资料状态明确不是资料不存在", "资料尚未结构化核验入账" in str(report.get("资料状态判断", "")), report.get("资料状态判断", "")))
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks.append(check("明确不提供事实答案且不填写191", boundary.get("提供事实答案") is False and boundary.get("填写191") is False, boundary))
    checks.append(check("高风险动作全部关闭", bool(boundary) and all(value is False for value in boundary.values()), boundary))
    open_bat = root / "05入口工具" / "单股证据核验资料来源导航卡_打开.bat"
    checks.append(check("入口工具存在", open_bat.exists(), str(open_bat)))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown说明不代填事实和197预演", "不提供事实答案" in md_text and "197" in md_text, str(latest_md)))
    checks.append(check("Markdown包含候选资料入口", "候选资料入口" in md_text and "巨潮资讯" in md_text and "东方财富" in md_text, str(latest_md)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验资料来源导航卡"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-source-navigation-card-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-source-navigation-card-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
