# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = EVOLUTION / "03数据" / "114并行自主施工分片护栏与抢占处理包"
LOG_DIR = EVOLUTION / "04日志" / "并行自主施工分片护栏与抢占处理包验收"
SUMMARY = OUT_DIR / "并行自主施工分片护栏与抢占处理包_最新.json"


def add(checks: list[dict], name: str, passed: bool, detail: str) -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    checks: list[dict] = []

    lanes = data.get("分片", [])
    locks = data.get("互斥锁", [])
    queue = data.get("下一批自主施工队列", [])
    safety = data.get("安全边界", {})

    add(checks, "总包状态通过", data.get("状态") == "pass", data.get("状态", ""))
    add(checks, "分片数量足够", len(lanes) >= 6, str(len(lanes)))
    add(checks, "存在非并行总巡检分片", any(item.get("编号") == "P6" and item.get("可并行") is False for item in lanes), "P6")
    add(checks, "互斥锁数量足够", len(locks) >= 6, str(len(locks)))
    add(checks, "19310锁存在", any("19310" in item.get("路径或端口", "") for item in locks), "19310")
    add(checks, "19302锁存在", any("19302" in item.get("路径或端口", "") for item in locks), "19302")
    add(checks, "总巡检聚合脚本锁存在", any("生成日常可用版自主巡检快照.py" in item.get("路径或端口", "") for item in locks), "总巡检")
    add(checks, "下一批队列非空", len(queue) >= 4, str(len(queue)))
    add(checks, "安全边界均为False", all(value is False for value in safety.values()), json.dumps(safety, ensure_ascii=False))

    for name, path_text in data.get("输出文件", {}).items():
        add(checks, f"输出文件存在-{name}", Path(path_text).exists(), path_text)

    passed = all(item["通过"] for item in checks)
    log = {
        "名称": "并行自主施工分片护栏与抢占处理包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "通过项": sum(1 for item in checks if item["通过"]),
        "失败项": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
    }
    latest = LOG_DIR / "parallel-autonomous-work-guard-verify-最新.json"
    latest.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "log": str(latest)}, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
