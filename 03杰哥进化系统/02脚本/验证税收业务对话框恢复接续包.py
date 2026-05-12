# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = EVOLUTION / "03数据" / "115税收业务对话框恢复接续包"
LOG_DIR = EVOLUTION / "04日志" / "税收业务对话框恢复接续包验收"
SUMMARY = OUT_DIR / "税收业务对话框恢复接续包_最新.json"


def add(checks: list[dict], name: str, passed: bool, detail: str) -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    checks: list[dict] = []

    add(checks, "总包状态通过", data.get("状态") == "pass", data.get("状态", ""))
    add(checks, "恢复任务指令存在", "恢复任务指令" in data and len(data["恢复任务指令"]) > 200, "恢复任务指令")
    add(checks, "只读验收样本三条", len(data.get("只读验收样本", [])) == 3, str(len(data.get("只读验收样本", []))))
    add(checks, "包含待复核草案摘要标题", "【税收分析助手-待复核草案摘要】" in json.dumps(data, ensure_ascii=False), "标题")
    add(checks, "包含软件产品事项", "软件产品增值税即征即退" in json.dumps(data, ensure_ascii=False), "软件产品")
    add(checks, "包含增值税法事项", "增值税法依据" in json.dumps(data, ensure_ascii=False), "增值税法依据")
    add(checks, "包含研发费用事项", "研发费用加计扣除" in json.dumps(data, ensure_ascii=False), "研发费用")
    add(checks, "需总管确认事项存在", len(data.get("需总管确认事项", [])) >= 4, str(data.get("需总管确认事项", [])))
    add(checks, "安全边界均未触发", all(value is False for value in data.get("安全边界", {}).values()), json.dumps(data.get("安全边界", {}), ensure_ascii=False))

    for name, path_text in data.get("输出文件", {}).items():
        add(checks, f"输出文件存在-{name}", Path(path_text).exists(), path_text)

    passed = all(item["通过"] for item in checks)
    log = {
        "名称": "税收业务对话框恢复接续包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "通过项": sum(1 for item in checks if item["通过"]),
        "失败项": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
    }
    latest = LOG_DIR / "tax-dialog-recovery-continuation-verify-最新.json"
    latest.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "log": str(latest)}, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
