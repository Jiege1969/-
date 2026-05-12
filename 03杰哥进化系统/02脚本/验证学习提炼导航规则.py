# -*- coding: utf-8 -*-
"""
名称：验证学习提炼导航规则.py
作用：验证进化系统已经具备“学什么、怎么学、从哪里学、不乱学”的机器可读规则和通用方法文档。
安全边界：只读配置和方法文档，只写04日志；不触发n8n，不调用模型，不写正式业务库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def evolution_root() -> Path:
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
    root = evolution_root()
    rule_path = root / "01配置" / "学习提炼导航规则.json"
    method_path = root / "03数据" / "04通用方法" / "学习提炼导航_知道学什么怎么学_20260503.md"
    rule = load_json(rule_path, {}) or {}
    method_text = method_path.read_text(encoding="utf-8-sig") if method_path.exists() else ""

    checks = [
        check("学习提炼导航规则存在", rule_path.exists(), str(rule_path)),
        check("学习提炼通用方法文档存在", method_path.exists(), str(method_path)),
        check("规则声明核心原则", len(rule.get("核心原则", [])) >= 5, rule.get("核心原则", [])),
        check("规则声明应该学习", len(rule.get("应该学习", [])) >= 5, rule.get("应该学习", [])),
        check("规则声明不应该学习", len(rule.get("不应该学习", [])) >= 5, rule.get("不应该学习", [])),
        check("规则声明学习渠道", len(rule.get("学习渠道", [])) >= 5, rule.get("学习渠道", [])),
        check("规则声明学习流程", len(rule.get("学习流程", [])) >= 7, rule.get("学习流程", [])),
        check("规则包含文稿质检学习口径", bool(rule.get("文稿质检学习口径")), rule.get("文稿质检学习口径", {})),
        check("安全边界关闭自动乱学", all(value is False for value in rule.get("安全边界", {}).values()), rule.get("安全边界", {})),
        check("方法文档说明不乱学", "不是“什么都学”" in method_text and "不应学习" in method_text, "已检查关键句"),
        check("方法文档包含文稿质检案例", "文稿质检" in method_text and "脚本硬比对" in method_text, "已检查文稿质检案例"),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "学习提炼导航规则验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
    }
    log_dir = root / "04日志" / "学习提炼导航"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest = log_dir / "learning-navigation-verify-最新.json"
    write_json(log_dir / f"learning-navigation-verify-{stamp}.json", result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
