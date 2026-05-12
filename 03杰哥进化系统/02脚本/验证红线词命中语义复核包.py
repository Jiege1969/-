# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = EVOLUTION / "03数据" / "113红线词命中语义复核包"
LOG_DIR = EVOLUTION / "04日志" / "红线词命中语义复核包验收"
SUMMARY = OUT_DIR / "红线词命中语义复核包_最新.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail: str, checks: list[dict]) -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    data = read_json(SUMMARY)
    checks: list[dict] = []

    check("总包存在", SUMMARY.exists(), str(SUMMARY), checks)
    check("状态通过", data.get("状态") == "pass", data.get("状态", ""), checks)
    check(
        "实际红线触发为0",
        data.get("指标", {}).get("实际红线触发数") == 0,
        str(data.get("指标", {}).get("实际红线触发数")),
        checks,
    )
    check(
        "需人工复核为0",
        data.get("指标", {}).get("需人工复核数") == 0,
        str(data.get("指标", {}).get("需人工复核数")),
        checks,
    )
    check(
        "端口冲突为0",
        data.get("指标", {}).get("端口冲突数") == 0,
        str(data.get("指标", {}).get("端口冲突数")),
        checks,
    )
    check(
        "端口均单监听",
        all(item.get("通过") and len(item.get("监听PID", [])) == 1 for item in data.get("端口语义复核", [])),
        json.dumps(data.get("端口语义复核", []), ensure_ascii=False),
        checks,
    )
    for label, path_text in data.get("输出文件", {}).items():
        check(f"输出文件存在-{label}", Path(path_text).exists(), path_text, checks)

    safety = data.get("安全边界", {})
    safety_ok = all(value is False for value in safety.values())
    check("安全边界均未触发", safety_ok, json.dumps(safety, ensure_ascii=False), checks)

    passed = all(item["通过"] for item in checks)
    log = {
        "名称": "红线词命中语义复核包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "通过项": sum(1 for item in checks if item["通过"]),
        "失败项": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
    }
    latest = LOG_DIR / "redline-hit-semantic-review-verify-最新.json"
    latest.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "log": str(latest)}, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
