# -*- coding: utf-8 -*-
"""
名称：验证300只试运行池.py
作用：验证300只试运行池生成结果满足数量、重点关注保留、字段完整和安全边界要求。
触发方式：python 验证300只试运行池.py
依赖：Python标准库；生成300只试运行池.py；300只试运行池生成规则.json；重点关注股票池.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地生成与验收；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只试运行池验收脚本。
标识：stock-trial-pool-300-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(code: str) -> str:
    return str(code).strip()


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成300只试运行池.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    rule = load_json(root / "01配置" / "300只试运行池生成规则.json")
    focus = load_json(root / "01配置" / "重点关注股票池.json")
    latest = root / "03数据" / "91试运行池" / "300只试运行池_最新.json"
    report = load_json(latest)
    pool = report.get("股票池", [])
    target = int(rule.get("目标规模", 300))
    pool_codes = {normalize_code(item.get("代码", "")) for item in pool}
    focus_codes = {normalize_code(item.get("代码", "")) for item in focus.get("股票池", [])}
    required_fields = {"代码", "名称", "市场", "行业", "成交额", "总市值", "流通市值", "入池原因", "评分"}
    actions = report.get("实际动作", {})

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本运行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新试运行池存在", latest.exists(), str(latest))
    add_check(checks, "数量不超过300且大于0", 0 < len(pool) <= target, len(pool))
    add_check(checks, "重点关注池全部保留", focus_codes.issubset(pool_codes), sorted(focus_codes - pool_codes))
    add_check(checks, "字段完整", all(required_fields.issubset(set(item)) for item in pool), sorted(required_fields))
    add_check(checks, "公开候选数量有效", report.get("数据源", {}).get("过滤后候选数量", 0) >= len(pool), report.get("数据源", {}))
    add_check(
        checks,
        "高风险动作未执行",
        actions.get("触发n8n") is False
        and actions.get("企业微信真实发送") is False
        and actions.get("写正式库") is False
        and actions.get("写旧系统") is False
        and actions.get("调用券商接口") is False
        and actions.get("自动交易") is False
        and actions.get("重启服务") is False,
        actions,
    )

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "试运行池": str(latest),
        "结论": "300只试运行池已具备下一步盘后轻扫描试运行条件。" if failed == 0 else "300只试运行池仍有失败项。",
    }
    output_dir = root / "04日志" / "试运行池"
    output = output_dir / f"stock-trial-pool-300-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_verify = output_dir / "stock-trial-pool-300-verify-最新.json"
    write_json(output, verify)
    write_json(latest_verify, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
