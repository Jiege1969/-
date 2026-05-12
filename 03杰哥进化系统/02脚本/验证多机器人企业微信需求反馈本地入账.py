# -*- coding: utf-8 -*-
"""验证多机器人企业微信需求反馈本地入账。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"
RESULT_JSON = DATA_DIR / "多机器人企业微信需求反馈本地入账结果_最新.json"
LEDGER_JSON = DATA_DIR / "多机器人企业微信需求反馈候选台账_最新.json"
LOG_DIR = ROOT / "04日志" / "多机器人企业微信需求反馈本地入账验收"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    now = datetime.now()
    executor = ROOT / "02脚本" / "执行多机器人企业微信需求反馈本地入账.py"
    result = subprocess.run(
        [sys.executable, str(executor), "--use-built-in-samples"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks: list[dict[str, Any]] = []
    add_check(checks, "执行脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "入账结果JSON存在", RESULT_JSON.exists(), str(RESULT_JSON))
    add_check(checks, "候选台账JSON存在", LEDGER_JSON.exists(), str(LEDGER_JSON))
    report = read_json(RESULT_JSON) if RESULT_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}
    candidates = ledger.get("候选", []) if isinstance(ledger.get("候选"), list) else []
    business_set = set(ledger.get("覆盖业务", []))
    add_check(checks, "总体状态pass", report.get("总体状态") == "pass", report.get("总体状态"))
    add_check(checks, "覆盖股票", "股票" in business_set, sorted(business_set))
    add_check(checks, "覆盖税收", "税收" in business_set, sorted(business_set))
    add_check(checks, "覆盖视频", "视频" in business_set, sorted(business_set))
    add_check(checks, "覆盖办公内容", "办公内容" in business_set, sorted(business_set))
    add_check(checks, "覆盖系统管家", "系统管家" in business_set, sorted(business_set))
    add_check(checks, "候选均需人工确认", all(item.get("需人工确认") is True for item in candidates), len(candidates))
    add_check(checks, "候选均不自动吸收", all(item.get("是否可自动吸收") is False for item in candidates), len(candidates))
    add_check(checks, "候选均不转正式规则", all(item.get("转正式规则") is False for item in candidates), len(candidates))
    add_check(checks, "候选有去重键", all(bool(item.get("去重键")) for item in candidates), len(candidates))
    problem_types = json.dumps([item.get("问题类型") for item in candidates], ensure_ascii=False)
    add_check(checks, "包含展示链接需求", "展示/链接需求" in problem_types, problem_types)
    add_check(checks, "包含状态汇报需求", "状态汇报需求" in problem_types, problem_types)
    safety = ledger.get("安全边界", {}) if isinstance(ledger.get("安全边界"), dict) else {}
    for key in ("重载19310", "重载19302", "真实发送企业微信", "触发n8n", "接券商", "交易", "登录电子税务局", "接财税软件", "真实发布视频", "写正式规则库", "自动转正式规则"):
        add_check(checks, f"{key}=false", safety.get(key) is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "名称": "多机器人企业微信需求反馈本地入账验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(LEDGER_JSON),
    }
    output = LOG_DIR / f"multi-robot-wecom-feedback-local-ingest-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    latest = LOG_DIR / "multi-robot-wecom-feedback-local-ingest-verify-最新.json"
    latest_md = LOG_DIR / "multi-robot-wecom-feedback-local-ingest-verify-最新.md"
    write_json(output, verify)
    write_json(latest, verify)
    write_text(
        latest_md,
        "\n".join(
            [
                "# 多机器人企业微信需求反馈本地入账验收",
                "",
                f"- 生成时间：{verify['生成时间']}",
                f"- 通过：{passed}",
                f"- 失败：{failed}",
                f"- 验收对象：{LEDGER_JSON}",
            ]
        ),
    )
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
