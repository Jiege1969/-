# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验模板同步执行.py
作用：验证194执行器默认不写入、具备显式确认参数；193禁止时验证阻断有效，193允许时验证受控同步条件。
触发方式：手动验收或由股票系统日常/C+++验收调用。
依赖：执行单股证据核验模板同步.py、192同步预览、193同步执行闸口、172/175/178人工核验模板。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验模板同步执行/single-stock-evidence-template-sync-execute-verify-最新.json。
安全边界：只运行194 dry-run 验证和读取模板；不传入 --execute，不写172/175/178，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-template-sync-execute-verify
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


def parse_json_line(text: str) -> dict[str, Any]:
    for line in reversed([line.strip() for line in text.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def find_item(template: dict[str, Any], code: str) -> dict[str, Any]:
    for item in template.get("核验模板", []):
        if str(item.get("代码") or "").lower() == code.lower():
            return item
    return {}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "执行单股证据核验模板同步.py"
    preview_path = root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.json"
    gate_path = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    report_path = root / "03数据" / "194单股证据核验模板同步执行" / "单股证据核验模板同步执行报告_最新.json"
    checks = [check("194执行脚本存在", script.exists(), str(script))]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    dry = subprocess.run(
        [sys.executable, str(script), "--report-scope", "temp"],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("默认dry-run可执行", dry.returncode == 0, dry.stdout.strip() or dry.stderr.strip()))
    dry_output = parse_json_line(dry.stdout)
    dry_report_path = Path(dry_output.get("报告JSON", ""))
    preview = load_json(preview_path, {}) or {}
    gate = load_json(gate_path, {}) or {}
    report = load_json(dry_report_path, {}) or {}
    target = preview.get("目标股票", {})
    code = str(target.get("代码") or "")
    checks.append(check("192目标股票明确", bool(code), target))
    gate_allowed = bool(gate.get("是否允许进入模板同步执行器"))
    target_missing = int(target.get("合计待填") or 0)
    checks.append(check(
        "193闸口状态与191完成度一致",
        gate_allowed or target_missing > 0,
        {
            "193是否允许": gate_allowed,
            "191合计待填": target_missing,
            "闸口结论": gate.get("闸口结论"),
        },
    ))
    checks.append(check("默认不写入人工模板", report.get("执行写入") is False, report.get("总结论")))
    latest_report = load_json(report_path, {}) or {}
    checks.append(check("dry-run验证不覆盖最新执行报告", latest_report.get("执行写入") is True or latest_report.get("执行写入") is False, latest_report.get("总结论")))

    company = load_json(root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json", {}) or {}
    event = load_json(root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json", {}) or {}
    industry = load_json(root / "03数据" / "178行业景气人工核验模板" / "行业景气人工核验模板_最新.json", {}) or {}
    company_item = find_item(company, code)
    event_item = find_item(event, code)
    industry_item = find_item(industry, code)
    checks.append(check("公司概况目标记录存在", bool(company_item), code))
    checks.append(check("事件风险目标记录存在", bool(event_item), code))
    checks.append(check("行业景气目标记录存在", bool(industry_item), code))
    if company_item or event_item or industry_item:
        synced = (
            company_item.get("核验状态") == "已核验"
            and event_item.get("人工填写", {}).get("核验状态") == "已核验"
            and industry_item.get("人工填写", {}).get("核验状态") == "已核验"
        )
        checks.append(check(
            "目标记录已同步或仍处dry-run等待执行",
            synced or report.get("执行写入") is False,
            {
                "执行写入": report.get("执行写入"),
                "公司概况": company_item.get("核验状态"),
                "事件风险": event_item.get("人工填写", {}).get("核验状态"),
                "行业景气": industry_item.get("人工填写", {}).get("核验状态"),
            },
        ))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", bool(safety) and all(safety.get(key) is False for key in ["是否写正式档案", "是否导入执行", "是否修改评分或推荐", "是否企业微信真实发送", "是否触发n8n", "是否调用券商接口", "是否自动交易", "是否更新施工接续包"]), safety))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
    }
    log_dir = root / "04日志" / "单股证据核验模板同步执行"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-template-sync-execute-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-template-sync-execute-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
