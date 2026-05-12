# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验人工填写工作台.py
作用：验证 191 人工填写工作台可生成，且保持只读材料汇总性质。
触发方式：手动验收或由股票系统日常/C+++验收调用。
依赖：生成单股证据核验人工填写工作台.py、190/191/198/197/192/193材料、191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、210确认回执状态面板、211回执后调度清单、212确认回执填写样例副本、213确认后路径演练报告、214正式回执待办卡、215正式回执填写前自检、216正式回执录入后受控重跑预演、206候选采用前闸口。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验人工填写工作台/single-stock-evidence-manual-workbench-verify-最新.json。
安全边界：只运行工作台生成脚本并读取本地材料；不联网抓取、不写正式档案、不导入、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易、不更新施工接续包。
创建/修改记录：2026-05-03 创建；2026-05-03 增加191最小行动卡检查；2026-05-03 增加197完成后预演检查；2026-05-03 增加191资料来源导航卡检查；2026-05-03 增加198填写质量闸口检查；2026-05-03 增加199资料候选处理包检查；2026-05-03 增加200填写建议草案检查；2026-05-03 增加201最小人工确认清单检查；2026-05-03 增加202候选填写CSV副本检查；2026-05-03 增加203候选写入差异预览检查；2026-05-03 增加204候选采用后质量预演检查；2026-05-03 增加205候选采用确认回执草案检查；2026-05-03 增加210至216回执确认链路检查；2026-05-03 增加206候选采用前闸口检查。
标识：single-stock-evidence-manual-workbench-verify
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
    script = root / "02脚本" / "生成单股证据核验人工填写工作台.py"
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    latest_json = out_dir / "单股证据核验人工填写工作台_最新.json"
    latest_md = out_dir / "单股证据核验人工填写工作台_最新.md"
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
    materials = report.get("材料", [])
    checks.append(check("二十八类材料齐全", len(materials) == 28 and all(item.get("存在") for item in materials), materials))
    steps = report.get("建议操作顺序", [])
    checks.append(check("建议操作顺序包含行动卡、资料来源导航、199候选包、200建议草案、201确认清单、202候选CSV、203差异预览、204质量预演、205确认回执、210状态面板、211调度清单、212样例副本、213演练报告、214待办卡、215自检、216重跑预演、206采用前闸口、207受控执行预案、208采用预览、209命令草案、CSV、198闸口和197预演", len(steps) >= 28 and any("最小行动卡" in item for item in steps) and any("资料来源导航卡" in item for item in steps) and any("199" in item and "候选" in item for item in steps) and any("200" in item and "建议" in item for item in steps) and any("201" in item and "确认" in item for item in steps) and any("202" in item and "CSV" in item for item in steps) and any("203" in item and "差异预览" in item for item in steps) and any("204" in item and "质量预演" in item for item in steps) and any("205" in item and "确认回执" in item for item in steps) and any("210" in item and "状态" in item for item in steps) and any("211" in item and "调度" in item for item in steps) and any("212" in item and "样例" in item for item in steps) and any("213" in item and "演练" in item for item in steps) and any("214" in item and "待办" in item for item in steps) and any("215" in item and "自检" in item for item in steps) and any("216" in item and "预演" in item for item in steps) and any("206" in item and "闸口" in item for item in steps) and any("207" in item and "受控执行预案" in item for item in steps) and any("208" in item and "预览" in item for item in steps) and any("209" in item and "命令" in item for item in steps) and any("CSV" in item for item in steps) and any("198" in item for item in steps) and any("197" in item for item in steps), steps))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    open_one = root / "05入口工具" / "单股证据核验人工填写工作台_打开.bat"
    open_all = root / "05入口工具" / "单股证据核验人工填写材料_全部打开.bat"
    csv_open = root / "05入口工具" / "单股证据核验人工填写CSV表单_打开.bat"
    csv_sync = root / "05入口工具" / "单股证据核验CSV表单同步到台账_执行.bat"
    preflight_bat = root / "05入口工具" / "单股证据核验191完成后预演检查_执行.bat"
    quality_bat = root / "05入口工具" / "单股证据核验191填写质量闸口_执行.bat"
    checks.append(check("入口工具存在", open_one.exists() and open_all.exists() and csv_open.exists() and csv_sync.exists() and preflight_bat.exists() and quality_bat.exists(), [str(open_one), str(open_all), str(csv_open), str(csv_sync), str(quality_bat), str(preflight_bat)]))
    open_all_text = open_all.read_text(encoding="utf-8-sig", errors="replace") if open_all.exists() else ""
    checks.append(check(
        "全部打开入口不再直开192/193旧材料",
        "192单股证据核验台账同步预览" not in open_all_text and "193单股证据核验模板同步执行闸口" not in open_all_text,
        str(open_all),
    ))
    sync_bat_text = csv_sync.read_text(encoding="utf-8-sig", errors="replace") if csv_sync.exists() else ""
    checks.append(check("CSV同步入口已转为197预演", "执行单股证据核验191完成后预演检查.py" in sync_bat_text and "--apply-191" in sync_bat_text, str(csv_sync)))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含191、资料来源导航、199候选包、200建议草案、201确认清单、202候选CSV、203差异预览、204质量预演、205确认回执、210状态面板、211调度清单、212样例副本、213演练报告、214待办卡、215自检、216重跑预演、206采用前闸口、207受控执行预案、208采用预览、209命令草案、198、197与192/193提醒", "191 未填完" in md_text and "192/193" in md_text and "197" in md_text and "198" in md_text and "资料来源导航卡" in md_text and "199 资料候选处理包" in md_text and "200 191填写建议草案" in md_text and "201 最小人工确认清单" in md_text and "202 191候选填写CSV副本" in md_text and "203 191候选写入差异预览" in md_text and "204 191候选采用后质量预演" in md_text and "205 191候选采用确认回执草案" in md_text and "210 确认回执状态面板" in md_text and "211 回执后调度清单" in md_text and "212 确认回执填写样例副本" in md_text and "213 确认后路径演练报告" in md_text and "214 正式回执待办卡" in md_text and "215 正式回执填写前自检" in md_text and "216 正式回执录入后受控重跑预演" in md_text and "206 191候选采用前闸口" in md_text and "207 191候选采用受控执行预案" in md_text and "208 191候选采用预览" in md_text and "209 受控写入命令草案" in md_text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验人工填写工作台"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-manual-workbench-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-manual-workbench-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
